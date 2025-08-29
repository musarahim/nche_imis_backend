from accounts.models import User
from common.models import District, TimeStampedModel
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

# Create your models here.

class Institution(TimeStampedModel):
    '''Institution model to represent an institution. '''
    INSTITUTION_TYPE_CHOICES = (
        ('public', 'Public'),
        ('private', 'Private'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='institution')
    name = models.CharField(max_length=255, unique=True, null=False, blank=False)
    alternative_email = models.EmailField(max_length=255, blank=True, null=True)
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='institutions', blank=False)
    institution_type = models.CharField(max_length=20, choices=INSTITUTION_TYPE_CHOICES, default='public', blank=False)
    landline = PhoneNumberField(region='UG', blank=True, null=True)
    contact_person = models.CharField(max_length=100, blank=False, null=True)
    contact_person_phone = PhoneNumberField(region='UG', blank=True, null=True)
    alternative_contact_person = models.CharField(max_length=100, blank=False, null=True)
    alternative_contact_person_phone = PhoneNumberField(region='UG', blank=True, null=True)
    logo = models.ImageField(upload_to='institutions/logos/', blank=False, null=True)
    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Institutions"
        ordering = ['name']

class PublicationYear(TimeStampedModel):
    year = models.IntegerField(null=False, blank=False)

    def __str__(self):
        return str(self.year)

class CertificationAndClassification(TimeStampedModel):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='certifications', blank=False)
    institution_name = models.CharField(max_length=255, unique=True, null=False, blank=False)
    acronym = models.CharField(max_length=255, unique=True, null=False, blank=False)
    postal_address = models.CharField(max_length=255, unique=True, null=False, blank=False)
    email_address = models.EmailField(max_length=255, unique=True, null=False, blank=False)
    website = models.URLField(max_length=255, unique=True, null=False, blank=False)
    landline = PhoneNumberField(region='UG', blank=True, null=True)
    mobile = PhoneNumberField(region='UG', blank=True, null=True)
    provisional_license_issue_date = models.DateField(null=False, blank=False)
    # consider using a reference to the provisional license
    provisional_license = models.FileField(upload_to='certifications/', null=False, blank=False)
    location = models.TextField(null=False, blank=False)
    amount_of_land = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    land_title = models.FileField(upload_to='land_titles/', null=False, blank=False)
    land_in_use = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    land_for_future_use = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    year_obtained = models.IntegerField(null=False, blank=False)
    leased_or_rented = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    lease_or_rent_agreement = models.FileField(upload_to='land_titles/', null=False, blank=False)
    # infrastructure
    classrooms = models.IntegerField(null=False, blank=False)
    libraries = models.IntegerField(null=False, blank=False)
    science_labs = models.IntegerField(null=False, blank=False)
    computer_labs = models.IntegerField(null=False, blank=False)
    staff_houses = models.IntegerField(null=False, blank=False)
    staff_houses_number = models.IntegerField(null=False, blank=False)
    administrative_staff_area = models.IntegerField(null=False, blank=False)
    area_for_staff_use = models.IntegerField(null=False, blank=False)
    administrative_block_area = models.IntegerField(null=False, blank=False)
    student_Welfare_offices = models.IntegerField(null=False, blank=False)
    sick_bay_area = models.IntegerField(null=False, blank=False)
    hostels_area = models.IntegerField(null=False, blank=False)
    meeting_hall_area = models.IntegerField(null=False, blank=False)
    master_plan = models.FileField(upload_to='land_titles/', null=False, blank=False)
    # ground,physical infrastructure
    area_of_playground = models.IntegerField(null=False, blank=False)
    # type of playground
    available_playgrounds = models.CharField(max_length=255, null=False, blank=False)
    # Area of empty space (and within the campus dedicated to aesthetic and recreation use)
    area_of_empty_space = models.IntegerField(null=False, blank=False)
    total_roads_mileage = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    water_source = models.CharField(max_length=255, null=False, blank=False)
    power_source = models.CharField(max_length=255, null=False, blank=False)
    has_cultivable_land = models.BooleanField(null=False, blank=False)
    cultivable_land = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    # Facilities
    library_books = models.IntegerField(null=False, blank=False)
    text_books = models.IntegerField(null=False, blank=False)
    publication_years = models.ManyToManyField(PublicationYear, blank=False)
    computers_in_use = models.IntegerField(null=False, blank=False)
    computers_in_library = models.IntegerField(null=False, blank=False)
    academic_staff_computers = models.IntegerField(null=False, blank=False)
    administrative_staff_computers = models.IntegerField(null=False, blank=False)
    library_computer_software = models.IntegerField(null=False, blank=False)
    #State whether students will access computers to locate reading materials in the library
    students_have_access = models.BooleanField(null=False, blank=False)
    has_internet_access = models.BooleanField(null=False, blank=False)
    library_seats = models.IntegerField(null=False, blank=False)
    classroom_seats = models.IntegerField(null=False, blank=False)
    laboratories_seats = models.IntegerField(null=False, blank=False)
    administration_block_seats = models.IntegerField(null=False, blank=False)
    student_facilities = models.TextField(null=False, blank=False)
    # academic staff
    full_time_staff = models.IntegerField(null=False, blank=False)
    part_time_staff = models.IntegerField(null=False, blank=False)
    academic_staff_qualification = models.FileField(null=False, blank=False)
    optional_staff = models.IntegerField(null=False, blank=False)
    part_time_staff_qualification = models.FileField(null=False, blank=False)
    
    

    def __str__(self):
        """
        Returns the institution name as a string representation of the model.
        """
        return self.institution_name
    

class InstitutionVehicle(TimeStampedModel):
    """Institution Vehicle"""
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='vehicles', blank=False)
    vehicle_name = models.CharField(max_length=255, unique=True, null=False, blank=False)
    registration_number = models.CharField(max_length=255, unique=True, null=False, blank=False)

    def __str__(self):
        return self.vehicle_name
    

class AcademicStaff(TimeStampedModel):
    """Academic Staff"""
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='academic_staff', blank=False)
    name = models.CharField(max_length=255, null=False, blank=False)
    position = models.CharField(max_length=255, null=False, blank=False)
    email = models.EmailField(max_length=255, null=False, blank=False)



