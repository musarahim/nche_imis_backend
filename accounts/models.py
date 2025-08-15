import pyotp
from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager,
                                        PermissionsMixin)
from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
from simple_history.models import HistoricalRecords
from trench.models import MFAMethod

# Create your models here.
# accounts/models.py


class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """
    def create_user(self, username, email, password=None, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email,username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        
        if user:
            # Create a default MFA method for the user
            MFAMethod.objects.get_or_create(
                user=user,
                name='email',
                is_active=True,
                is_primary=True,
                secret = pyotp.random_base32(length=32)  # Generate a random secret for the user
                )
        return user

    def create_superuser(self, email,username, password=None, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True) # Superusers should always be active

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(username,email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    '''Custom user model'''
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True, verbose_name='email address')
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    account_expiry_date = models.DateTimeField(null=True, blank=True)
    phone = PhoneNumberField(region='UG', blank=True, null=True)
    alternative_phone_number = PhoneNumberField(region='UG', blank=True, null=True)

    objects = CustomUserManager()
    history = HistoricalRecords()
    USERNAME_FIELD = 'username' # This tells Django to use email for authentication
    REQUIRED_FIELDS = ["email"] # No other fields required at creation besides email and password

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self):
        return self.email

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """
        Returns the short name for the user.
        """
        return self.username

