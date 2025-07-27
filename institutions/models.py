from accounts.models import User
from common.models import District, TimeStampedModel
from django.db import models

# Create your models here.

class Institution(TimeStampedModel):
    '''Institution model to represent an institution. '''
    INSTITUTION_TYPE_CHOICES = (
        ('public', 'Public'),
        ('private', 'Private'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='institution')
    name = models.CharField(max_length=255, unique=True, null=False, blank=False)
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='institutions', blank=False)
    institution_type = models.CharField(max_length=20, choices=INSTITUTION_TYPE_CHOICES, default='public', blank=False)
    landline = models.CharField(max_length=15, blank=True, null=True)
    contact_person = models.CharField(max_length=100, blank=False, null=True)
    contact_person_phone = models.CharField(max_length=14, blank=False, null=True)
    alternative_contact_person = models.CharField(max_length=100, blank=False, null=True)
    alternative_contact_person_phone = models.CharField(max_length=14, blank=False, null=True)
    logo = models.ImageField(upload_to='institutions/logos/', blank=False, null=True)
    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Institutions"
        ordering = ['name']
