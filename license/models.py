from common.models import TimeStampedModel
from django.db import models

# Create your models here.

class LicenseType(TimeStampedModel):
    '''License types'''
    code = models.CharField(max_length = 10, null=False, blank=False)
    name = models.CharField(max_length=100, null=False, blank=False)

    def __str__(self):
        return self.name


class OTIProvisional(TimeStampedModel):
    code = models.CharField(max_length=30, null=True, blank=True)
    
