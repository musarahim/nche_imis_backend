from accounts.models import User
from common.choices import (BANK_ACCOUNT_TYPE_CHOICES, BLOOD_GROUP, GENDER,
                            MARITAL_STATUS, PARENT_STATUS,
                            PASSPORT_TYPE_CHOICES)
from common.models import (County, District, Nationality, Parish, Religion,
                           SubCounty, TimeStampedModel, Title, Tribe, Village)
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

# Create your models here.

class Directorate(TimeStampedModel):
    '''Directorate model'''
    short_code = models.CharField(max_length=10, null=False, blank=False)
    name = models.CharField(max_length=100, null=False, blank=False, unique=True)

    def __str__(self):
        return self.name
    

class Department(TimeStampedModel):
    '''Department model'''
    short_code = models.CharField(max_length=10, null=False, blank=False, unique=True)
    name = models.CharField(max_length=100, null=False, blank=False, unique=True)
    directorate = models.ForeignKey(Directorate, on_delete=models.DO_NOTHING, null=False, blank=False)

    def __str__(self):
        return self.name
    
class Designation(TimeStampedModel):
    '''Designation model'''
    name = models.CharField(max_length=100, null=False, blank=False, unique=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

class Employee(TimeStampedModel):
    '''Employee model'''
    system_account = models.OneToOneField(User, on_delete=models.DO_NOTHING, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.DO_NOTHING, null=True, blank=True)
    employee_number = models.CharField(null=True, blank=True, max_length=50)
    designation = models.ForeignKey(Designation, on_delete=models.DO_NOTHING, null=True, blank=True)
    title = models.ForeignKey(Title, on_delete=models.DO_NOTHING, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=False)
    gender = models.CharField(max_length=10, choices=GENDER, null=True, blank=False)
    nationality = models.ForeignKey(Nationality, on_delete=models.DO_NOTHING, null=True, blank=False)
    religion = models.ForeignKey(Religion, on_delete=models.DO_NOTHING, null=True, blank=False)
    tribe = models.ForeignKey(Tribe, on_delete=models.DO_NOTHING, null=True, blank=False)
    joining_date = models.DateField(null=True, blank=True)
    # Residential Address
    district = models.ForeignKey(District, on_delete=models.DO_NOTHING, null=True, blank=True)
    county = models.ForeignKey(County, on_delete=models.DO_NOTHING, null=True, blank=True)
    sub_county = models.ForeignKey(SubCounty, on_delete=models.DO_NOTHING, null=True, blank=True)
    parish = models.ForeignKey(Parish, on_delete=models.DO_NOTHING, null=True, blank=True)
    village = models.ForeignKey(Village, on_delete=models.DO_NOTHING, null=True, blank=True)
    distance_from_work = models.FloatField(null=True, blank=True, help_text="Distance from work in kilometers")
    address = models.TextField(null=True, blank=True)
    # place of origin
    district_of_origin = models.ForeignKey(District, on_delete=models.DO_NOTHING, null=True, blank=True, related_name='district_of_origin')
    county_of_origin = models.ForeignKey(County, on_delete=models.DO_NOTHING, null=True, blank=True, related_name='county_of_origin')
    sub_county_of_origin = models.ForeignKey(SubCounty, on_delete=models.DO_NOTHING, null=True, blank=True, related_name='sub_county_of_origin')
    parish_of_origin = models.ForeignKey(Parish, on_delete=models.DO_NOTHING, null=True, blank=True, related_name='parish_of_origin')
    village_of_origin = models.ForeignKey(Village, on_delete=models.DO_NOTHING, null=True, blank=True, related_name='village_of_origin')
    address_of_origin = models.TextField(null=True, blank=True)
    # other details
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS, null=True, blank=False)
    spouse_name = models.CharField(max_length=200, null=True, blank=True)
    # next of kin
    next_of_kin_name = models.CharField(max_length=200, null=True, blank=True)
    next_of_kin_relationship = models.CharField(max_length=100, null=True, blank=True)
    next_of_kin_date_of_birth = models.DateField(null=True, blank=True)
    occupation = models.CharField(max_length=200, null=True, blank=True)
    work_place = models.CharField(max_length=100, null=True, blank=False)
    next_of_kin_phone_number = PhoneNumberField(null=True, blank=True)
    next_of_kin_address = models.TextField(null=True, blank=True)
    next_of_kin_email = models.EmailField(null=True, blank=True)
    # contact person
    contact_person_name = models.CharField(max_length=200, null=True, blank=True)
    contact_person_relationship = models.CharField(max_length=100, null=True, blank=True)
    contact_person_telephone = PhoneNumberField(null=True, blank=True)
    contact_person_email = models.EmailField(null=True, blank=True)
    contact_person_address = models.TextField(null=True, blank=True)
    # medical records
    blood_group = models.CharField(max_length=10, null=True, blank=True, choices=BLOOD_GROUP)
    allergies = models.TextField(null=True, blank=True)
    # biological parents
    father_name = models.CharField(max_length=200, null=True, blank=True)
    father_status = models.CharField(max_length=50, choices=PARENT_STATUS, null=True, blank=True)
    father_contact = PhoneNumberField(null=True, blank=True)
    mother_name = models.CharField(max_length=200, null=True, blank=True)
    mother_status = models.CharField(max_length=50, choices=PARENT_STATUS, null=True, blank=True)
    mother_contact = PhoneNumberField(null=True, blank=True)
    # identification
    nin = models.CharField(max_length=14, null=True, blank=True)
    national_id_document = models.FileField(upload_to='employees_documents/', null=True, blank=True)
    passport_photo = models.ImageField(upload_to='employees_photos/', null=True, blank=True)
    # driving license
    license_number = models.CharField(max_length=50, null=True, blank=True)
    class_of_license = models.CharField(max_length=50, null=True, blank=True)
    date_of_issue = models.DateField(null=True, blank=True)
    date_of_expiry = models.DateField(null=True, blank=True)
    license_document = models.FileField(upload_to='employees_documents/', null=True, blank=True)
    # passport 
    passport_number = models.CharField(max_length=50, null=True, blank=True)
    passport_type = models.CharField(max_length=50, null=True, blank=True, choices=PASSPORT_TYPE_CHOICES)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    place_of_issue = models.CharField(max_length=100, null=True, blank=True)
    #nssf & tin
    nssf_number = models.CharField(max_length=50, null=True, blank=True)
    tin_number = models.CharField(max_length=50, null=True, blank=True)
    # bank details
    bank_name = models.CharField(max_length=100, null=True, blank=True)
    branch = models.CharField(max_length=100, null=True, blank=True)
    account_name = models.CharField(max_length=200, null=True, blank=True)
    account_number = models.CharField(max_length=50, null=True, blank=True)
    account_type = models.CharField(max_length=50, null=True, blank=True, choices=BANK_ACCOUNT_TYPE_CHOICES)
    # signature
    signature = models.ImageField(upload_to='employees_signatures/', null=True, blank=True)


    def __str__(self):
        return self.system_account
    

class Dependent(TimeStampedModel):
    '''Employee Dependents/children'''
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, null=False, blank=False)
    name = models.CharField(max_length=200, null=False, blank=False)
    relationship = models.CharField(max_length=100, null=False, blank=False)
    date_of_birth = models.DateField(null=True, blank =False)

    def __str__(self):
        return self.name

   

class EducationHistory(TimeStampedModel):
    '''
    Schools, colleges & institutions attended
    (from the highest level attained to primary seven)
    '''
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, null=False, blank=False)
    institution = models.CharField(max_length=200, null=False, blank=False)
    from_year = models.IntegerField(null=False, blank=False)
    to_year = models.IntegerField(null=False, blank=False)
    qualification = models.CharField(max_length=200, null=False, blank=False)
    award_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.institution} - {self.qualification}"
    
class WorkHistory(TimeStampedModel):
    '''working experience (from the current )'''
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, null=False, blank=False)
    employer = models.CharField(max_length=200, null=False, blank=False)
    from_date = models.DateField(null=False, blank=False)
    to_date = models.DateField(null=True, blank=True)
    position = models.CharField(max_length=200, null=False, blank=False)
    responsibilities = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.employer} - {self.position}"
    
class Referee(TimeStampedModel):
    '''Referees'''
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, null=False, blank=False)
    name = models.CharField(max_length=200, null=False, blank=False)
    place_of_work = models.CharField(max_length=200, null=False, blank=False)
    position = models.CharField(max_length=200, null=False, blank=False)
    telephone = PhoneNumberField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)

    def __str__(self):
        return self.name
    