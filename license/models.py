from common.models import TimeStampedModel
from django.db import models
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
    staff_houses_number = models.IntegerField(null=True, blank=False)
    administrative_staff_area = models.IntegerField(null=True, blank=False)
    area_for_staff_use = models.IntegerField(null=True, blank=False)
    administrative_block_area = models.IntegerField(null=True, blank=False)
    student_Welfare_offices = models.IntegerField(null=True, blank=False)
    sick_bay_area = models.IntegerField(null=True, blank=False)
    hostels_area = models.IntegerField(null=True, blank=False)
    meeting_hall_area = models.IntegerField(null=True, blank=False)
    master_plan = models.FileField(upload_to='land_titles/', null=True, blank=False)
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
    master_plan = models.FileField(upload_to='land_titles/', null=True, blank=False)
    #   ,[VEHICLES]
    # Facilities
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
    institution_ownership = HTMLField(null=True, blank=False)


   
    #   ,[TOTAL_STAFF_ACADEMIC]
    #   ,[TOTAL_STAFF_EXP]
    #   ,[TOTAL_TAFF_VISIT]
    #   ,[TOTAL_STAFF_PHD]
    #   ,[TOTAL_STAFF_MASTER]
    #   ,[TOTAL_STAFF_BACHELORS]
    #   ,[TOTAL_STAFF_DIPLOMA]
    #   ,[STAFF_STUDENT_RATIO]
    #   ,[STAFF_OVERLOAD]
    #   ,[TOTAL_STAFF_ADMIN]
    #   ,[TOTAL_STAFF_SUPPORT]
    #   ,[GC_CHAIRPERSON]
    #   ,[GC_VICECHAIRPERSON]
    #   ,[PRINCIPAL]
    #   ,[REGISTRAR]
    #   ,[HEAD_DIVISION]
    #   ,[ACADEMIC_BOARD_MEMBER]
    #   ,[INST_OWNERS]
    #   ,[INST_PROMOTERS]
    #   ,[ANNUALBUDGET]
    #   ,[BUDGET_PERCENT_FEES]
    #   ,[INCOME_SUPPORT]
    #   ,[BUDGET_INFRASTRUCTURE]
    #   ,[BUDGET_RD]
    #   ,[BUDGET_COMPUTER]
    #   ,[BUDGET_LAB]
    #   ,[BUDGET_STAFF]
    #   ,[BUDGET_LIBRARY]
    #   ,[BUDGET_PERCENT_SALARY]
    #   ,[BANKS]
    #   ,[MISSION]
    #   ,[VISION]
    #   ,[OBJECTIVES]
    #   ,[PROGRAM_INTEND]
    #   ,[COMPETENCE_INTEND]
    #   ,[PLANNED_PROGRAM]
    #   ,[TOTAL_STUDENT_EXP]
    #   ,[PROGRAM_STUDENT_DIST]
    #   ,[YEAR_CODE]
    #   ,[STATUS]
    #   ,[INTSTATUS]
    #   ,[INTINST]
    #   ,[ACRONYM]


    
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
    staff_houses_number = models.IntegerField(null=True, blank=False)
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
    application_code = models.CharField(max_length=30, null=True, blank=False)
    institution = models.ForeignKey(Institution, on_delete=models.DO_NOTHING, null=False, blank=False)
    has_title_deed = models.BooleanField(null=False, blank=False)
    title_deed = models.FileField(null=False, blank=False)
    names_of_promoters = HTMLField(null=True, blank=False)
    # VISION, MISSION, OBJECTIVES AND PHILOSOPHY
    vision = models.TextField(null=False, blank=False)
    mission = models.TextField(null=False, blank=False)
    objectives = models.TextField(null=False, blank=False)
    philosophy = models.TextField(null=False, blank=False)
    governance_structure = HTMLField(null=True, blank=False)
    human_resources = HTMLField(null=True, blank=False)
    source_of_finance = models.TextField(null=False, blank=False)
    action_plan = HTMLField(null=True, blank=False)
    infrastructure = HTMLField(null=True, blank=False)
    programmes = HTMLField(null=True, blank=False)
    promoters = models.FileField(null=True, blank=False)
    project_proposal = models.FileField(null=True, blank=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', blank=False)
    application_date = models.DateField(null=True, blank=True, auto_now=True)
    

    def __str__(self):
        """
        Returns the institution name as a string representation of the model.
        """
        return self.institution
    
class IntrimAuthorityDocument(TimeStampedModel):
    '''Documents for Intrim Authority'''
    intrim_authority = models.ForeignKey(IntrimAuthority, on_delete=models.CASCADE, related_name='documents', blank=False)
    title = models.CharField(max_length=255, null=False, blank=False)
    document = models.FileField(upload_to='intrim_authority_documents/', null=False, blank=False)

    def __str__(self):
        return f"{self.name} - {self.intrim_authority.institution.name}"