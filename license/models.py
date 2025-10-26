from common.models import FinanceYear, TimeStampedModel
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone
from institutions.models import Institution, PublicationYear
from phonenumber_field.modelfields import PhoneNumberField
from tinymce.models import HTMLField

# Create your models here.

class LicenseType(TimeStampedModel):
    '''License types'''
    code = models.CharField(max_length = 10, null=False, blank=False)
    name = models.CharField(max_length=100, null=False, blank=False)

    def __str__(self):
        return self.name


class OTIProvisional(TimeStampedModel):
    code = models.CharField(max_length=30, null=True, blank=True)
    application_date = models.DateField(null=True, blank=True, auto_now=True)
    institute = models.ForeignKey(Institution, on_delete=models.DO_NOTHING, null=True, blank=True)
    land_owned = models.BooleanField(null=True, blank=True)
    amount_of_land = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=False)
    land_title = models.FileField(upload_to='land_titles/', null=True, blank=False)
    land_in_use = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=False)
    land_for_future_use = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=False)
    years_for_future_use = models.IntegerField(null=True, blank=False)
    leased_or_rented = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=False)
    lease_or_rent_agreement = models.FileField(upload_to='land_titles/', null=True, blank=False)
    # infrastructure
    classrooms = models.IntegerField(null=True, blank=False)
    libraries = models.IntegerField(null=True, blank=False)
    science_labs = models.IntegerField(null=True, blank=False)
    computer_labs = models.IntegerField(null=True, blank=False)
    staff_houses = models.IntegerField(null=True, blank=False)
    administrative_staff_area = models.IntegerField(null=True, blank=False)
    area_for_staff_use = models.IntegerField(null=True, blank=False)
    administrative_block_area = models.IntegerField(null=True, blank=False)
    student_Welfare_offices = models.IntegerField(null=True, blank=False)
    sick_bay_area = models.IntegerField(null=True, blank=False)
    hostels_area = models.IntegerField(null=True, blank=False)
    meeting_hall_area = models.IntegerField(null=True, blank=False)
    # ground,physical infrastructure
    area_of_playground = models.IntegerField(null=True, blank=False)
    # type of playground
    available_playgrounds = models.CharField(max_length=255, null=True, blank=False)
    # Area of empty space (and within the campus dedicated to aesthetic and recreation use)
    area_of_empty_space = models.IntegerField(null=True, blank=False)
    total_roads_mileage = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=False)
    water_source = models.CharField(max_length=255, null=True, blank=False)
    power_source = models.CharField(max_length=255, null=True, blank=False)
    has_cultivable_land = models.BooleanField(null=True, blank=False)
    cultivable_land = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=False)
    master_plan = models.FileField(upload_to='institution/', null=True, blank=False)
    # [VEHICLES]
    vehicles = models.IntegerField(null=True, blank=False)
    vehicle_details = HTMLField(null=True, blank=False)
    # EDUCATIONAL FACILITIES IN PLACE	
    library_books = models.IntegerField(null=True, blank=False)
    text_books = models.IntegerField(null=True, blank=False)
    publication_years = models.ManyToManyField(PublicationYear, blank=False)
    computers_in_use = models.IntegerField(null=True, blank=False)
    computers_in_library = models.IntegerField(null=True, blank=False)
    academic_staff_computers = models.IntegerField(null=True, blank=False)
    administrative_staff_computers = models.IntegerField(null=True, blank=False)
    library_computer_software = models.IntegerField(null=True, blank=False)
    #State whether students will access computers to locate reading materials in the library
    students_have_access = models.BooleanField(null=True, blank=False)
    has_internet_access = models.BooleanField(null=True, blank=False)
    library_seats = models.IntegerField(null=True, blank=False)
    classroom_seats = models.IntegerField(null=True, blank=False)
    laboratories_seats = models.IntegerField(null=True, blank=False)
    administration_block_seats = models.IntegerField(null=True, blank=False)
    student_facilities = models.TextField(null=True, blank=False)
    # academic staff
    full_time_staff = models.IntegerField(null=True, blank=False)
    intended_full_time_staff = models.IntegerField(null=True, blank=False)
    full_time_staff_qualification = models.FileField(null=True, blank=False)
    part_time_staff = models.IntegerField(null=True, blank=False)
    part_time_staff_qualification = models.FileField(null=True, blank=False)
    phd_holders = models.IntegerField(null=True, blank=False)
    phd_holder_discipline = models.FileField(null=True, blank=False)
    masters_holders = models.IntegerField(null=True, blank=False)
    masters_holders_discipline = models.FileField(null=True, blank=False)
    bachelor_holders = models.IntegerField(null=True, blank=False)
    bachelor_holders_discipline = models.FileField(null=True, blank=False)
    diploma_holders = models.IntegerField(null=True, blank=False)
    diploma_holders_discipline = models.FileField(null=True, blank=False)
    average_staff_student_ratio = models.IntegerField(null=True, blank=False)
    programme_staff_student_ratio = models.FileField(null=True, blank=False)
    staff_overload = models.IntegerField(null=True, blank=False)
    # administrative and support staff
    administrative_staff = models.IntegerField(null=True, blank=False)
    support_staff = models.IntegerField(null=True, blank=False)
    # names, qualifications and gender
    council_members = models.FileField(null=True, blank=False)
    senate_members = models.FileField(null=True, blank=False)
    # other infor
    governing_council_chairperson = models.CharField(max_length=255, null=True, blank=False)
    governing_council_vice = models.CharField(max_length=255, null=True, blank=False)
    principal = models.CharField(max_length=255, null=True, blank=False)
    academic_registrar = models.CharField(max_length=255, null=True, blank=False)
    heads_of_academic_divisions = HTMLField(null=True, blank=False)
    academic_board_members = HTMLField(null=True, blank=False)
    #OWNERSHIP OF THE TERTIARY INSTITUTE/ COLLEGE
    institution_ownership = HTMLField(null=True, blank=False)
    institution_promoters = HTMLField(null=True, blank=False)
    # Financial Management
    other_assets = HTMLField(null=True, blank=False)
    anual_budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=False)
    previous_financial_year_accounts = models.FileField(null=True, blank=False)
    fee_structure = models.FileField(null=True, blank=False)
    fees_percent_budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=False)
    other_institution_income = models.TextField(null=True, blank=False)
    # How much of the budget will be given to:
    infrastructure_development = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=False)
    research_development = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=False)
    computer_hardware_software = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=False)
    science_lab_equipment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=False)
    staff_development = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=False)
    staff_salaries_percentage_budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=False)
    current_bankers = models.TextField(null=True, blank=False)
    # vision and mission
    vision = models.TextField(null=True, blank=False)
    mission = models.TextField(null=True, blank=False)
    specific_objectives = models.TextField(null=True, blank=False)
    logo = models.ImageField(blank=False, null=True)
    stractegic_plan = models.FileField(null=True, blank=False)
    current_programmes = HTMLField(null=True, blank=False)
    area_of_competence = HTMLField(null=True, blank=False)
    feature_programmes = HTMLField(null=True, blank=False)
    # student population
    total_number_of_students = models.IntegerField(null=True, blank=False)
    # programme_distribution
    arts_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=False)
    social_sciences_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=False)
    basic_sciences_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=False)
    arts_education_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=False)
    science_education_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=False)
    agriculture_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=False)
    medicine_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=False)
    veterinary_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=False)
    engineering_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=False)
        #     12.	SIGNATURES OF THE OFFICERS OF THE INSTITUTION
        # (i) 	Chairperson of Governing Council (print, sign and date)
        # Name ……………………………………………………………………….

        # Signature	…………………………….        Date…………………………..

        # (ii) 	Principal of the institution	   
        # Name …………………………………………………………………..…  

        # Signature	……….……………………….                 Date…………………
        
        # (iii) 	Deputy Principal	
        # Name  ………………………………………………………………….…              
        
        # Signature	…………………………………… Date …….……………………..\ attach template
    signatures = models.FileField(null=True, blank=False)
    members_cvs = models.FileField(null=True, blank=False)
    detailed_programmes = models.FileField(null=True, blank=False)
    physical_education_facilities = models.FileField(null=True, blank=False)
    status = models.CharField(max_length=20, choices=(('draft', 'Draft'), ('submitted', 'Submitted')), default='draft', blank=False)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        super().save(*args, **kwargs)   

    def generate_code(self):
        # Academic year format (e.g., 2024-2025)
        year = timezone.now().year
        if timezone.now().month >= 7:  # financial year starts in July
            academic_year = f"{year}-{year+1}"
        else:
            academic_year = f"{year-1}-{year}"

        # Get last sequence number for this year
        last_app = OTIProvisional.objects.filter(
            code__contains=academic_year
        ).order_by("id").last()

        if last_app:
            last_number = int(last_app.code.split("/")[-1])
        else:
            last_number = 0

        new_number = str(last_number + 1).zfill(5)  # zero-padded

        return f"OTIP/{academic_year}/{new_number}"

class OTIProvisionalDocument(TimeStampedModel):
    '''Documents for OTI Provisional'''
    oti_provisional = models.ForeignKey(OTIProvisional, on_delete=models.CASCADE, related_name='documents', blank=False)
    title = models.CharField(max_length=255, null=False, blank=False)
    document = models.FileField(upload_to='oti_provisional_documents/', null=False, blank=False)

    def __str__(self):
        return f"{self.name} - {self.oti_provisional.institution.name}"


    







    
class CertificationAndClassification(TimeStampedModel):
    '''Certification and Classification model to represent an institution. '''
    STATUS_CHOICES=(
        ('draft', 'Draft'),
        ('Submitted', 'Submitted'),
    )
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='certifications', blank=False)
    provisional_license_issue_date = models.DateField(null=False, blank=False)
    # consider using a reference to the provisional license
    provisional_license = models.FileField(upload_to='certifications/', null=False, blank=False)
    location = models.TextField(null=False, blank=False)
    amount_of_land = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    land_title = models.FileField(upload_to='land_titles/', null=False, blank=False)
    land_in_use = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    land_for_future_use = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=False)
    year_obtained = models.IntegerField(null=False, blank=False)
    leased_or_rented = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=False)
    lease_or_rent_agreement = models.FileField(upload_to='land_titles/', null=True, blank=False)
    # infrastructure
    classrooms = models.IntegerField(null=True, blank=False)
    libraries = models.IntegerField(null=False, blank=False)
    science_labs = models.IntegerField(null=False, blank=False)
    computer_labs = models.IntegerField(null=False, blank=False)
    staff_houses = models.IntegerField(null=False, blank=False)
    administrative_staff_area = models.IntegerField(null=True, blank=False)
    area_for_staff_use = models.IntegerField(null=False, blank=False)
    administrative_block_area = models.IntegerField(null=False, blank=False)
    student_Welfare_offices = models.IntegerField(null=False, blank=False)
    sick_bay_area = models.IntegerField(null=False, blank=False)
    hostels_area = models.IntegerField(null=False, blank=False)
    meeting_hall_area = models.IntegerField(null=False, blank=False)
    master_plan = models.FileField(upload_to='land_titles/', null=True, blank=False)
    # ground,physical infrastructure
    area_of_playground = models.IntegerField(null=False, blank=False)
    # type of playground
    available_playgrounds = models.CharField(max_length=255, null=False, blank=False)
    # Area of empty space (and within the campus dedicated to aesthetic and recreation use)
    area_of_empty_space = models.IntegerField(null=False, blank=False)
    total_roads_mileage = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=False)
    water_source = models.CharField(max_length=255, null=True, blank=False)
    power_source = models.CharField(max_length=255, null=True, blank=False)
    has_cultivable_land = models.BooleanField(null=True, blank=False)
    cultivable_land = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=False)
    # Facilities
    library_books = models.IntegerField(null=False, blank=False)
    text_books = models.IntegerField(null=False, blank=False)
    publication_years = models.ManyToManyField(PublicationYear, blank=False)
    computers_in_use = models.IntegerField(null=False, blank=False)
    computers_in_library = models.IntegerField(null=False, blank=False)
    academic_staff_computers = models.IntegerField(null=False, blank=False)
    administrative_staff_computers = models.IntegerField(null=True, blank=False)
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
    intended_full_time_staff = models.IntegerField(null=False, blank=False)
    full_time_staff_qualification = models.FileField(null=False, blank=False)
    part_time_staff = models.IntegerField(null=False, blank=False)
    part_time_staff_qualification = models.FileField(null=True, blank=False)
    phd_holders = models.IntegerField(null=False, blank=False)
    phd_holder_discipline = models.FileField(null=False, blank=False)
    masters_holders = models.IntegerField(null=False, blank=False)
    masters_holders_discipline = models.FileField(null=False, blank=False)
    bachelor_holders = models.IntegerField(null=False, blank=False)
    bachelor_holders_discipline = models.FileField(null=False, blank=False)
    diploma_holders = models.IntegerField(null=True, blank=False)
    diploma_holders_discipline = models.FileField(null=True, blank=False)
    average_staff_student_ratio = models.IntegerField(null=False, blank=False)
    programme_staff_student_ratio = models.FileField(null=False, blank=False)
    staff_overload = models.IntegerField(null=False, blank=False)
    # administrative and support staff
    administrative_staff = models.IntegerField(null=True, blank=False)
    support_staff = models.IntegerField(null=True, blank=False)
    # names, qualifications and gender
    council_members = models.FileField(null=True, blank=False)
    senate_members = models.FileField(null=True, blank=False)
    # other infor
    governing_council_chairperson = models.CharField(max_length=255, null=True, blank=False)
    governing_council_vice = models.CharField(max_length=255, null=True, blank=False)
    principal = models.CharField(max_length=255, null=True, blank=False)
    academic_registrar = models.CharField(max_length=255, null=True, blank=False)
    heads_of_academic_divisions = HTMLField(null=True, blank=False)
    academic_board_members = HTMLField(null=True, blank=False)
    institution_ownership = HTMLField(null=True, blank=False)
    # Financial Management
    other_assets = models.FileField(null=False, blank=False)
    anual_budget = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    previous_financial_year_accounts = models.FileField(null=True, blank=False)
    fee_structure = models.FileField(null=False, blank=False)
    fees_percent_budget = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    other_institution_income = models.TextField(null=False, blank=False)
    # How much of the budget will be given to:
    infrastructure_development = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    research_development = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    computer_hardware_software = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    science_lab_equipment = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    library_equipment = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    staff_development = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    staff_salaries = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    current_bankers = models.TextField(null=False, blank=False)
    # vision and mission
    vision = models.TextField(null=False, blank=False)
    mission = models.TextField(null=False, blank=False)
    specific_objectives = models.TextField(null=False, blank=False)
    logo = models.ImageField(blank=False, null=True)
    stractegic_plan = models.FileField(null=False, blank=False)
    current_programmes = HTMLField(null=True, blank=False)
    area_of_competence = HTMLField(null=True, blank=False)
    feature_programmes = HTMLField(null=True, blank=False)
    # student population
    total_number_of_students = models.IntegerField(null=False, blank=False)
    programme_distribution = HTMLField(null=True, blank=False)
    # Regions distribution
    eastern_students = models.IntegerField(null=False, blank=False)
    central_students = models.IntegerField(null=False, blank=False)
    northern_students = models.IntegerField(null=False, blank=False)
    western_students = models.IntegerField(null=False, blank=False)
    # Non Ugandan Students
    east_africans_students = models.IntegerField(null=False, blank=False)
    other_students = models.IntegerField(null=False, blank=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', blank=False)
    application_date = models.DateField(null=True, blank=True, auto_now=True)
    # payment, integrate URA
    def __str__(self):
        """
        Returns the institution name as a string representation of the model.
        """
        return self.institution_name
    
# university license
class IntrimAuthority(TimeStampedModel):
    """Intrim Authority University License"""
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('pending', 'Pending'),
    )
    application_code = models.CharField(max_length=30, null=True, blank=True, unique=True)
    institution = models.ForeignKey(Institution, on_delete=models.DO_NOTHING, null=False, blank=True)
    has_title_deed = models.BooleanField(null=False, blank=False)
    title_deed = models.FileField(null=False, blank=True)
    names_of_promoters = HTMLField(null=True, blank=False)
    # VISION, MISSION, OBJECTIVES AND PHILOSOPHY
    vision = models.TextField(null=False, blank=True)
    mission = models.TextField(null=False, blank=True)
    objectives = models.TextField(null=False, blank=True)
    philosophy = models.TextField(null=False, blank=True)
    governance_structure = HTMLField(null=True, blank=False)
    human_resources = HTMLField(null=True, blank=False)
    source_of_finance = models.TextField(null=False, blank=True)
    action_plan = HTMLField(null=True, blank=False)
    infrastructure = HTMLField(null=True, blank=False)
    programmes = HTMLField(null=True, blank=False)
    promoters = models.FileField(null=True, blank=False)
    project_proposal = models.FileField(null=True, blank=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', blank=False)
    application_date = models.DateField(null=True, blank=True, auto_now=True)

    def save(self, *args, **kwargs):
        if not self.application_code:
            self.application_code = self.generate_code()
        super().save(*args, **kwargs)
    
    def generate_code(self):
        # Academic year format (e.g., 2024-2025)
        year = timezone.now().year
        if timezone.now().month >= 7:  # financial year starts in July
            academic_year = f"{year}-{year+1}"
        else:
            academic_year = f"{year-1}-{year}"

        # Get last sequence number for this year
        last_app = IntrimAuthority.objects.filter(
            application_code__contains=academic_year
        ).order_by("id").last()

        if last_app:
            last_number = int(last_app.application_code.split("/")[-1])
        else:
            last_number = 0

        new_number = str(last_number + 1).zfill(5)  # zero-padded

        return f"UNII/{academic_year}/{new_number}"
    def __str__(self):
        """
        Returns the institution name as a string representation of the model.
        """
        return self.institution.name
    
class IntrimAuthorityDocument(TimeStampedModel):
    '''Documents for Intrim Authority'''
    intrim_authority = models.ForeignKey(IntrimAuthority, on_delete=models.CASCADE, related_name='documents', blank=False)
    title = models.CharField(max_length=255, null=False, blank=False)
    document = models.FileField(upload_to='intrim_authority_documents/', null=False, blank=False)

    def __str__(self):
        return f"{self.name} - {self.intrim_authority.institution.name}"
    
# next provisional license university
class UniversityProvisionalLicense(TimeStampedModel):
    """University Provisional License"""
    LEASE_RENTED=(
        ('lease', 'Lease'),
        ('rent', 'Rent'),
    )
    application_code = models.CharField(max_length=20, null=True, blank=True)
    institution = models.ForeignKey(Institution, on_delete=models.DO_NOTHING, null=False, blank=True)
    # LOCATION AND LAND
    amount_of_land = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    land_title = models.FileField(upload_to='land_titles/', null=False, blank=True)
    land_in_use = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    land_for_future_use = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=False)
    year_obtained = models.CharField(null=False, blank=False, max_length=30)
    leased_or_rented = models.CharField(choices=LEASE_RENTED, max_length=10, null=True, blank=False)
    lease_or_rent_agreement = models.FileField(upload_to='land_titles/', null=True, blank=False)
    # infrastructure
    classrooms = models.FloatField(null=True, blank=True)
    libraries = models.FloatField(null=True, blank=True)
    science_labs = models.FloatField(null=True, blank=True)
    computer_labs = models.FloatField(null=True, blank=True)
    staff_houses = models.FloatField(null=True, blank=True)
    administrative_staff_area = models.FloatField(null=True, blank=True)
    area_for_staff_use = models.FloatField(null=True, blank=True)
    administrative_block_area = models.FloatField(null=True, blank=True)
    student_Welfare_offices = models.FloatField(null=True, blank=True)
    sick_bay_area = models.FloatField(null=True, blank=True)
    hostels_area = models.FloatField(null=True, blank=True)
    meeting_hall_area = models.FloatField(null=True, blank=True)
    master_plan = models.FileField(upload_to='land_titles/', null=True, blank=True)
    # ground,physical infrastructure
    area_of_playground = models.IntegerField(null=True, blank=True)
    # type of playground
    available_playgrounds = models.CharField(max_length=255, null=True, blank=True)
    # Area of empty space (and within the campus dedicated to aesthetic and recreation use)
    area_of_empty_space = models.IntegerField(null=True, blank=True)
    total_roads_mileage = models.FloatField(null=True, blank=True)
    water_source = models.CharField(max_length=255, null=True, blank=True)
    power_source = models.CharField(max_length=255, null=True, blank=True)
    has_cultivable_land = models.BooleanField(null=True, blank=True)
    cultivable_land = models.FloatField(null=True, blank=True)
    # vehicles go here
    number_of_vehicles = models.IntegerField(null=True, blank=True)
    vehicle_registration = models.TextField(null=True, blank=True)
    # EDUCATIONAL FACILITIES IN PLACE	
    library_books = models.IntegerField(null=True, blank=True)
    text_books = models.IntegerField(null=True, blank=True)
    publication_years = ArrayField(
        models.CharField(max_length=5),  # store as list of strings
        blank=True,
        default=list
    )
    computers_in_use = models.IntegerField(null=True, blank=True)
    computers_in_library = models.IntegerField(null=True, blank=True)
    academic_staff_computers = models.IntegerField(null=True, blank=True)
    administrative_staff_computers = models.IntegerField(null=True, blank=True)
    library_computer_software = models.TextField(null=True, blank=True)
    #State whether students will access computers to locate reading materials in the library
    students_have_access = models.BooleanField(null=True, blank=True)
    has_internet_access = models.BooleanField(null=True, blank=True)
    library_seats = models.IntegerField(null=True, blank=True)
    classroom_seats = models.IntegerField(null=True, blank=True)
    laboratories_seats = models.IntegerField(null=True, blank=True)
    administration_block_seats = models.IntegerField(null=True, blank=True)
    student_facilities = models.TextField(null=True, blank=True)
    # academic staff
    intended_full_time_academic_staff = models.IntegerField(null=True, blank=True)
    intended_part_time_academic_staff = models.IntegerField(null=True, blank=True)

    # ADMINISTRATIVE AND SUPPORT STAFF
    intended_full_time_admin_staff = models.IntegerField(null=True, blank=True)
    intended_support_staff = models.IntegerField(null=True, blank=True)
    # university council members
    council_members = HTMLField(null=True, blank=True)
    proposed_chancellor = models.CharField(max_length=255, null=True, blank=True)
    proposed_vice_chancellor = models.CharField(max_length=255, null=True, blank=True)
    proposed_university_secretary = models.CharField(max_length=255, null=True, blank=True)
    proposed_academic_registrar = models.CharField(max_length=255, null=True, blank=True)
    heads_of_faculties = HTMLField(null=True, blank=True)
    # Ownership OF THE UNIVERSITY
    institution_ownership = HTMLField(null=True, blank=True)
    university_promoters = HTMLField(null=True, blank=True)
    # Financial Management
    other_assets = models.TextField(null=True, blank=True)
    annual_budget = models.DecimalField(max_digits=250, decimal_places=2, null=True, blank=True)
    fee_structure = models.FileField(null=True, blank=True)
    fees_percent_budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    other_income_sources = models.TextField(null=True, blank=True)
    # How much of the budget is to be given to
    infrastructure_development = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    research_development = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    computer_hardware_software = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    science_lab_equipment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    library_equipment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    staff_development = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    staff_salaries = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    current_bankers = models.TextField(null=True, blank=True)
    # vision and mission
    vision = models.TextField(null=True, blank=True)
    mission = models.TextField(null=True, blank=True)
    specific_objectives = models.TextField(null=True, blank=True)
    stractegic_plan = models.FileField(null=True, blank=True)
    programmes = models.FileField(null=True, blank=True)
    area_of_competence = HTMLField(null=True, blank=True)
    feature_programmes = HTMLField(null=True, blank=True)
    # student population
    total_number_of_students = models.IntegerField(null=True, blank=True)
    # programme_distribution
    arts_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    social_sciences_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    basic_sciences_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    arts_education_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    science_education_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    agriculture_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    medicine_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    veterinary_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    engineering_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    technology_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    #signatures
    signatures = models.FileField(null=True, blank=True)
    member_cvs = models.FileField(null=True, blank=True)
    finance_control = models.FileField(null=True, blank=True)
    detailed_programmes = models.FileField(null=True, blank=True)
    physical_education_facilities = models.FileField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=(('draft', 'Draft'), ('submitted', 'Submitted')), default='draft', blank=False)
    application_date = models.DateField(null=True, blank=True, auto_now=True)

    def __str__(self):
        """
        Returns the institution name as a string representation of the model.
        """
        return self.institution.name
    
    def save(self, *args, **kwargs):
        if not self.application_code:
            self.application_code = self.generate_code()
        super().save(*args, **kwargs)

    def generate_code(self):
        # Academic year format (e.g., 2024-2025)
        year = timezone.now().year
        if timezone.now().month >= 7:  # financial year starts in July
            academic_year = f"{year}-{year+1}"
        else:
            academic_year = f"{year-1}-{year}"

        # Get last sequence number for this year
        last_app = UniversityProvisionalLicense.objects.filter(
            application_code__contains=academic_year
        ).order_by("id").last()

        if last_app:
            last_number = int(last_app.application_code.split("/")[-1])
        else:
            last_number = 0

        new_number = str(last_number + 1).zfill(5)  # zero-padded 

        return f"UNIP/{academic_year}/{new_number}"
    
class UniversityProvisionalLicenseDocument(TimeStampedModel):
    '''Documents for University Provisional License'''
    university_provisional_license = models.ForeignKey(UniversityProvisionalLicense, on_delete=models.CASCADE, related_name='documents', blank=False)
    title = models.CharField(max_length=255, null=False, blank=False)
    document = models.FileField(upload_to='university_provisional_license_documents/', null=False, blank=False)

    def __str__(self):
        return f"{self.name} - {self.university_provisional_license.institution.name}"
    

class CharterApplication(TimeStampedModel):
    """Charter Application"""
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('pending', 'Pending'),
    )
    application_code = models.CharField(max_length=30, null=True, blank=True, unique=True)
    institution = models.ForeignKey(Institution, on_delete=models.DO_NOTHING, null=False, blank=True)
    has_provisional_license = models.BooleanField(null=False, blank=False)
    provisional_license = models.FileField(null=False, blank=True)
    # LOCATION AND LAND
    location = models.TextField(null=False, blank=True)
    amount_of_land_owned = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=True)
    land_title = models.FileField(upload_to='land_titles/', null=False, blank=True)
    land_in_use = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    land_for_future_use = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=False)
    year_obtained = models.IntegerField(null=False, blank=False)
    leased_or_rented = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=False)
    lease_or_rent_agreement = models.FileField(upload_to='land_titles/', null=True, blank=False)
    # infrastructure
    classrooms = models.IntegerField(null=True, blank=False)
    libraries = models.IntegerField(null=False, blank=False)
    science_labs = models.IntegerField(null=False, blank=False)
    computer_labs = models.IntegerField(null=False, blank=False)
    staff_houses = models.IntegerField(null=False, blank=False)
    areadministrative_staff_area = models.IntegerField(null=True, blank=False)
    area_for_staff_use = models.IntegerField(null=False, blank=False)
    administrative_block_area = models.IntegerField(null=False, blank=False)
    student_Welfare_offices = models.IntegerField(null=False, blank=False)
    sick_bay_area = models.IntegerField(null=False, blank=False)
    hostels_area = models.IntegerField(null=False, blank=False)
    meeting_hall_area = models.IntegerField(null=True, blank=False)
    master_plan = models.FileField(upload_to='land_titles/', null=True, blank=False)
    # ground,physical infrastructure
    area_of_playground = models.FloatField(null=False, blank=False)
    # type of playground
    available_playgrounds = models.CharField(max_length=255, null=False, blank=False)
    area_of_empty_space = models.IntegerField(null=False, blank=False)
    total_roads_mileage = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=False)
    water_source = models.CharField(max_length=255, null=False, blank=False)
    power_source = models.CharField(max_length=255, null=False, blank=False)
    has_cultivable_land = models.BooleanField(null=True, blank=False)
    cultivable_land = models.FloatField(null=True, blank=False)
   
    #Transport - State the number and registration of vehicles the university has
    # EDUCATIONAL FACILITIES IN PLACE
    library_books = models.IntegerField(null=False, blank=False)
    text_books = models.IntegerField(null=False, blank=False)
    publication_years = models.ManyToManyField(PublicationYear, blank=False)
    computers_in_use = models.IntegerField(null=False, blank=False)
    computers_in_library = models.IntegerField(null=False, blank=False)
    academic_staff_computers = models.IntegerField(null=False, blank=False)
    administrative_staff_computers = models.IntegerField(null=True, blank=False)
    library_computer_software = models.IntegerField(null=False, blank=False)
    #State whether students will access computers to locate reading materials in the library
    students_have_access = models.BooleanField(null=False, blank=False)
    has_internet_access = models.BooleanField(null=False, blank=False)
    library_seats = models.IntegerField(null=False, blank=False)
    classroom_seats = models.IntegerField(null=False, blank=False)
    laboratories_seats = models.IntegerField(null=False, blank=False)
    administration_block_seats = models.IntegerField(null=False, blank=False)
    student_facilities = models.TextField(null=False, blank=False)
    # ACADEMIC STAFF
    full_time_academic_staff = models.IntegerField(null=False, blank=False)
    intended_full_time_academic_staff = models.IntegerField(null=False, blank=False)
    full_time_academic_staff_qualifications = models.FileField(null=True, blank=True)
    intended_part_time_academic_staff = models.IntegerField(null=False, blank=False)
    part_time_academic_staff_qualifications = models.FileField(null=True, blank=True)
    phd_holders = models.IntegerField(null=False, blank=False)
    phd_holder_discipline = models.FileField(null=False, blank=False)
    masters_holders = models.IntegerField(null=False, blank=False)
    masters_holders_discipline = models.FileField(null=False, blank=False)
    bachelor_holders = models.IntegerField(null=False, blank=False)
    bachelor_holders_discipline = models.FileField(null=False, blank=False)
    diploma_holders = models.IntegerField(null=True, blank=False)
    diploma_holders_discipline = models.FileField(null=True, blank=False)
    average_staff_student_ratio = models.IntegerField(null=False, blank=False)
    programme_staff_student_ratio = models.FileField(null=False, blank=False)
    staff_overload = models.IntegerField(null=False, blank=False)
    # ADMINISTRATIVE AND SUPPORT STAFF
    administrative_staff = models.IntegerField(null=False, blank=False)
    support_staff = models.IntegerField(null=False, blank=False)
    council_members = models.FileField(null=False, blank=False)
    senate_members = models.FileField(null=False, blank=False)
    chancellor = models.CharField(max_length=255, null=False, blank=False)
    vice_chancellor = models.CharField(max_length=255, null=False, blank=False)
    university_secretary = models.CharField(max_length=255, null=False, blank=False)
    academic_registrar = models.CharField(max_length=255, null=False, blank=False)
    vice_registrar = models.CharField(max_length=255, null=False, blank=False)
    deans = models.FileField(null=False, blank=False)
    # OWNERSHIP OF THE UNIVERSITY
    ownership = HTMLField(null=False, blank=False)
    # FINANCES AND THEIR MANAGEMENT
    other_assets = HTMLField(null=False, blank=False)
    annual_budget = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    previous_year_accounts = models.FileField(null=False, blank=False)
    fees_structure = models.FileField(null=False, blank=False)
    fees_percentage = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    other_income_source = HTMLField(null=False, blank=False)
    # How much of the budget is given to
    infrastructure_budget = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    research_budget = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    computer_budget = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    science_labs_budget = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    staff_development_budget = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    library_budget = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    staff_salary_budget = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    current_bankers = models.TextField(null=False, blank=False)
    # VISION AND MISSION OF THE UNIVERSITY
    vision = models.TextField(null=False, blank=False)
    mission = models.TextField(null=True, blank=False)
    specific_objectives = models.TextField(null=False, blank=False)
    university_strategic_plan = models.FileField(null=False, blank=False)
    programmes_offered = models.FileField(null=False, blank=False)
    areas_of_competence = models.FileField(null=False, blank=False)
    future_planned_programmes = models.FileField(null=True, blank=True)
    # STUDENT POPULATION
    total_students = models.IntegerField(null=False, blank=False)
    # programmes distribution
    arts_students = models.IntegerField(null=False, blank=False)
    social_science_students = models.IntegerField(null=False, blank=False)
    basic_science_students = models.IntegerField(null=False, blank=False)
    arts_education_students = models.IntegerField(null=False, blank=False)
    agriculture_students = models.IntegerField(null=False, blank=False)
    medicine_students = models.IntegerField(null=False, blank=False)
    veterinary_students = models.IntegerField(null=False, blank=False)
    engineering_students = models.IntegerField(null=False, blank=False)
    other_students_numbers = HTMLField(null=False, blank=False)
    # Regions of origin
    eastern_region = models.IntegerField(null=False, blank=False)
    central_region = models.IntegerField(null=False, blank=False)
    northern_region = models.IntegerField(null=False, blank=False)
    western_region = models.IntegerField(null=False, blank=False)
    # Non-Ugandan students
    east_africans = models.IntegerField(null=False, blank=False)
    other_regions = models.IntegerField(null=False, blank=False)
    # SIGNATURE OF THE OFFICERS OF THE UNIVERSITY
    signature_officers = models.FileField(null=False, blank=False)
    # ATTACHMENTS
    financial_control = models.FileField(null=False, blank=False)
    detailed_programmes = models.FileField(null=False, blank=False)
    facilities = models.FileField(null=False, blank=False)

    def __str__(self):
        return self.institution
    
    def save(self, *args, **kwargs):
        if not self.application_code:
            self.application_code = self.generate_code()
        super().save(*args, **kwargs)   

    def generate_code(self):
        # Academic year format (e.g., 2024-2025)
        year = timezone.now().year
        if timezone.now().month >= 7:  # financial year starts in July
            academic_year = f"{year}-{year+1}"
        else:
            academic_year = f"{year-1}-{year}"

        # Get last sequence number for this year
        last_app = OTIProvisional.objects.filter(
            code__contains=academic_year
        ).order_by("id").last()

        if last_app:
            last_number = int(last_app.code.split("/")[-1])
        else:
            last_number = 0

        new_number = str(last_number + 1).zfill(5)  # zero-padded

        return f"UTIP/{academic_year}/{new_number}"
    

class CharterApplicationDocoment(models.Model):
    application = models.ForeignKey(CharterApplication, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=False, blank=False)
    document = models.FileField(null=False, blank=False)

    def __str__(self):
        return f"{self.name} - {self.oti_provisional.institution.name}"





    