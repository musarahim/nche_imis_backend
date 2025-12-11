from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from import_export.admin import ExportActionModelAdmin, ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin
from unfold.admin import ModelAdmin
from unfold.contrib.import_export.forms import (ExportForm, ImportForm,
                                                SelectableFieldsExportForm)

from .models import (CertificationAndClassification, CharterApplication,
                     IntrimAuthority, UniversityProvisionalLicense)

# Register your models here.


@admin.register(CertificationAndClassification)
class CertificationAndClassificationAdmin(ModelAdmin, ExportActionModelAdmin):
    export_form_class = SelectableFieldsExportForm
    list_display = ("institution__name",)
    search_fields = ("institution__name",)
    #actions = ["export_as_csv"]
    filter = ('institution__name',)  # 
    compressed_fields = True
    # Warn before leaving unsaved changes in changeform
    warn_unsaved_form = True  # Default: False
     # Display submit button in filters
    list_filter_submit = True

    # Display changelist in fullwidth
    list_fullwidth = False
     # Position horizontal scrollbar in changelist at the top
    list_horizontal_scrollbar_top = False

    # Dsable select all action in changelist
    list_disable_select_all = False
    list_per_page = 10
    list_max_show_all = 1000
    ordering = ['institution__name']
    change_form_show_cancel_button = True
    fieldsets = (
        ("Institution", {
            "classes": ["tab", "wide", "extrapretty"],
            'fields': (
                'institution',
                'institution_name',
                'acronym',
                'postal_address',
                'email_address',
                'website',
                'landline',
                'mobile',
                
            ),
        }),
        ("location", {
            "classes": ["tab", "wide", "extrapretty"],
            'fields': (
                "provisional_license",
                'location',
                'amount_of_land',
                'land_title',
                'land_in_use',
                'land_for_future_use',
                'year_obtained',
                'leased_or_rented',
                'lease_or_rent_agreement',
            ),
            
        }),
        ("Infrastructure", {
            "classes": ["tab", "wide", "extrapretty"],
            'fields': (
                'classrooms',
                'libraries',
                'science_labs',
                'computer_labs',
                'staff_houses',
                'staff_houses_number',
                'administrative_staff_area',
                'area_for_staff_use',
                'administrative_block_area',
                'student_Welfare_offices',
                'sick_bay_area',
                'hostels_area',
                'meeting_hall_area',
                'master_plan',
            ),
            
            
        }),
        ("Ground", {
            "classes": ["tab", "wide", "extrapretty"],
            'fields': (
                'area_of_playground',
                'available_playgrounds',
                'area_of_empty_space',
                'total_roads_mileage',
                'water_source',
                'power_source',
                'has_cultivable_land',
                'cultivable_land'
            ),
        }),
        ("Facilities", {
            "classes": ["tab", "wide", "extrapretty"],
            'fields': (
                'library_books',
                'text_books',
                'publication_years',
                'computers_in_use',
                'computers_in_library',
                'academic_staff_computers',
                'administrative_staff_computers',
                'library_computer_software',
                'students_have_access',
                'has_internet_access',
                'library_seats',
                'classroom_seats',
                'laboratories_seats',
                'administration_block_seats',
                'student_facilities'
            ),
        }),
        ("Academic Staff", {
            "classes": ["tab", "wide", "extrapretty"],
            'fields': (
                'full_time_staff',
                'intended_full_time_staff',
                'full_time_staff_qualification',
                'part_time_staff',
                'part_time_staff_qualification',
                'phd_holders',
                'phd_holder_discipline',
                'masters_holders',
                'masters_holders_discipline',
                'bachelor_holders',
                'bachelor_holders_discipline',
                'diploma_holders',
                'diploma_holders_discipline',
                'average_staff_student_ratio',
                'programme_staff_student_ratio',
                'staff_overload',
                'administrative_staff',
                'support_staff',
                'council_members',
                'senate_members'    
            ),
        }),
        ("Management", {
            "classes": ["tab", "wide", "extrapretty"],
            'fields': (
                'governing_council_chairperson',
                'governing_council_vice',
                'principal',
                'academic_registrar',
                'heads_of_academic_divisions',
                'academic_board_members',
                'institution_ownership',
            ),
        }),
        ("Fanancial", {
            "classes": ["tab", "wide", "extrapretty"],
            'fields': (
                'other_assets',
                'anual_budget',
                'previous_financial_year_accounts',
                'fee_structure',
                'fees_percent_budget',
                'other_institution_income',
                'infrastructure_development',
                'research_development',
                'computer_hardware_software',
                'science_lab_equipment',
                'library_equipment',
                'staff_development',
                'staff_salaries',
                'current_bankers',
            ),
        }),
        ("Other Info", {
            "classes": ["tab", "wide", "extrapretty"],
            'fields': (
                'vision',
                'mission',
                'specific_objectives',
                'logo',
                'stractegic_plan',
                'current_programmes',
                'area_of_competence',
                'feature_programmes',
                'total_number_of_students',
                'programme_distribution',
                'eastern_students',
                'western_students',
                'northern_students',
                'central_students',
                'east_africans_students',
                'other_students'
            ),
        }),
        ("Payment", {
            "classes": ["tab", "wide", "extrapretty"],
            'fields': (
                
            ),
        }),

    )


@admin.register(IntrimAuthority)
class IntrimAuthorityAdmin(ModelAdmin, SimpleHistoryAdmin):
    list_display = ('application_code','institution__name', 'status', 'created')
    search_fields = ("institution__name",)
    # fieldset
    fieldsets = (
        (_("Institution"), {
            "classes": ["tab", "wide", "extrapretty"],
            'fields': (
                'institution',
                'has_title_deed',
                'title_deed',
                'names_of_promoters',  
            ),
        }),
           (_("Vision & Mission"), {
            "classes": ["tab", "wide", "extrapretty"],
            'fields': (
                'vision',
                'mission',
                'objectives',
                'philosophy',  
            ),
        }),
         (_("Governance Structure"), {
            "classes": ["tab", "wide", "extrapretty"],
            'fields': (
                'governance_structure',
                'human_resources',
                'source_of_finance',
                'action_plan',  
                'infrastructure',
                'programmes',
                'promoters',
                'project_proposal',
                'status'
            ),
        }),
    )

@admin.register(UniversityProvisionalLicense)
class UniversityProvisionalLicenseAdmin(ModelAdmin, SimpleHistoryAdmin):
    list_display = ('application_code','institution__name', 'status', 'created')
    search_fields = ("institution__name",)
    #actions = ["export_as_csv"]
    filter = ('institution',)  # 
    compressed_fields = False
    # Warn before leaving unsaved changes in changeform
    warn_unsaved_form = True  # Default: False
     # Display submit button in filters
    list_filter_submit = True

    # Display changelist in fullwidth
    list_fullwidth = False
     # Position horizontal scrollbar in changelist at the top
    list_horizontal_scrollbar_top = False

    # Dsable select all action in changelist
    list_disable_select_all = False
    list_per_page = 10
    list_max_show_all = 1000
    ordering = ['institution__name']
    #change_form_show_cancel_button = True


@admin.register(CharterApplication)
class CharterApplicationAdmin(ModelAdmin, SimpleHistoryAdmin):
    list_display = ('application_code','institution__name', 'status', 'created')
    search_fields = ("institution__name",)
    #actions = ["export_as_csv"]
    filter = ('institution',)  # 
    compressed_fields = False
    # Warn before leaving unsaved changes in changeform
    warn_unsaved_form = True  # Default: False
     # Display submit button in filters
    list_filter_submit = True

    # Display changelist in fullwidth
    list_fullwidth = False
     # Position horizontal scrollbar in changelist at the top
    list_horizontal_scrollbar_top = False

    # Dsable select all action in changelist
    list_disable_select_all = False
    list_per_page = 10
    list_max_show_all = 1000
    ordering = ['institution__name']
    #change_form_show_cancel_button = True
