from accounts.models import User
from common.models import District, Region, TimeStampedModel
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from tinymce.models import HTMLField


# Create your models here.
class LicenseType(TimeStampedModel):
    '''License types'''
    code = models.CharField(max_length = 10, null=False, blank=False, unique=True)
    name = models.CharField(max_length=100, null=False, blank=False, unique=True)

    def __str__(self):
        return self.name

class Institution(TimeStampedModel):
    '''Institution model to represent an institution. '''
    INSTITUTION_TYPE_CHOICES = (
        ('public', 'Public'),
        ('private', 'Private'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='institution')
    name = models.CharField(max_length=255, unique=True, null=False, blank=False)
    acroynm = models.CharField(max_length=50, unique=True, null=True, blank=False)
    alternative_email = models.EmailField(max_length=255, blank=True, null=True)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='institutions', blank=False, null=True)
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='institutions', blank=False)
    institution_type = models.CharField(max_length=20, choices=INSTITUTION_TYPE_CHOICES, default='public', blank=False)
    landline = PhoneNumberField(region='UG', blank=True, null=True)
    contact_person = models.CharField(max_length=100, blank=False, null=True)
    contact_person_phone = PhoneNumberField(region='UG', blank=True, null=True)
    alternative_contact_person = models.CharField(max_length=100, blank=False, null=True)
    alternative_contact_person_phone = PhoneNumberField(region='UG', blank=True, null=True)
    logo = models.ImageField(upload_to='institutions/logos/', blank=False, null=True)
    postal_address = models.CharField(null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    location = models.TextField(null=True, blank=True)
    license = models.ForeignKey(LicenseType, on_delete=models.CASCADE, related_name='institutions', blank=False, null=True)
    is_closed = models.BooleanField(null=False, blank=True, default=False)

    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Institutions"
        ordering = ['name']

class PublicationYear(TimeStampedModel):
    '''Publication Year model. '''
    year = models.IntegerField(null=False, blank=False)

    def __str__(self):
        return str(self.year)


    

class InstitutionVehicle(TimeStampedModel):
    """Institution Vehicle"""
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='vehicles', blank=False)
    vehicle_name = models.CharField(max_length=255, unique=True, null=False, blank=False)
    registration_number = models.CharField(max_length=255, unique=True, null=False, blank=False)

    def __str__(self):
        return self.vehicle_name
    


class OtherDocuments(TimeStampedModel):
    """Other Documents"""
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='other_documents', blank=False)
    document_name = models.CharField(max_length=255, unique=True, null=False, blank=False)
    document = models.FileField(null=False, blank=False)

    def __str__(self):
        return self.document_name

