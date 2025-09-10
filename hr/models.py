from accounts.models import User
from common.choices import GENDER, MARITAL_STATUS, PARENT_STATUS
from common.models import TimeStampedModel, Title
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

# Create your models here.

class Directorate(TimeStampedModel):
    short_code = models.CharField(max_length=10, null=False, blank=False)
    name = models.CharField(max_length=100, null=False, blank=False)

    def __str__(self):
        return self.name

class Department(TimeStampedModel):
    short_code = models.CharField(max_length=10, null=False, blank=False)
    name = models.CharField(max_length=100, null=False, blank=False)
    directorate = models.ForeignKey(Directorate, on_delete=models.DO_NOTHING, null=False, blank=False)

    def __str__(self):
        return self.name

class Employee(TimeStampedModel):
    '''Employee model'''
    system_account = models.OneToOneField(User, on_delete=models.DO_NOTHING, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.DO_NOTHING, null=True, blank=True)
    employee_number = models.CharField(null=True, blank=True, max_length=50)
    title = models.ForeignKey(Title, on_delete=models.DO_NOTHING, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=False)
    gender = models.CharField(max_length=10, choices=GENDER, null=True, blank=False)
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS, null=True, blank=False)
    father_name = models.CharField(max_length=200, null=True, blank=True)
    father_status = models.CharField(max_length=20, choices=PARENT_STATUS, null=True, blank=False)
    father_phone = PhoneNumberField(region='UG', blank=True, null=True)
    mother_name = models.CharField(max_length=200, null=True, blank=True)
    mother_status = models.CharField(max_length=20, choices=PARENT_STATUS, null=True, blank=False)
    mother_phone = PhoneNumberField(region='UG', blank=True, null=True)

    def __str__(self):
        return self.system_account

   

