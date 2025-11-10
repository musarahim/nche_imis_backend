from django.contrib import admin
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _
from simple_history.admin import SimpleHistoryAdmin
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.forms.widgets import ArrayWidget, WysiwygWidget
from unfold.paginator import InfinitePaginator

from .forms import EmployeeForm
from .models import (Department, Dependent, Designation, Directorate,
                     EducationHistory, Employee, Referee, WorkHistory)


# Register your models here.
@admin.register(Directorate)
class DirectorateAdmin(SimpleHistoryAdmin,ModelAdmin):
    '''Admin interface for Directorate model.'''
    list_display = ('short_code','name', 'created', 'modified')
    fields = ('name', 'short_code')
    search_fields = ('name', 'short_code')
    ordering = ('name',)
    readonly_fields = ('created', 'modified','deleted_at')
    list_per_page = 10

@admin.register(Department)
class DepartmentAdmin(SimpleHistoryAdmin,ModelAdmin):
    '''Admin interface for Department model.'''
    list_display = ('directorate','short_code','name', 'created', 'modified')
    fields = ('name', 'short_code', 'directorate')
    warn_unsaved_form = True
    list_filter_submit = False
    list_filter_sheet = False
    #paginator = InfinitePaginator
    show_full_result_count = True
    search_fields = ('name', 'short_code')
    ordering = ('name',)
    filter_fields = ('directorate',)
    readonly_fields = ('created', 'modified','deleted_at')
    list_per_page = 10

@admin.register(Designation)
class DesignationAdmin(SimpleHistoryAdmin,ModelAdmin):
    '''Admin interface for Designation model.'''
    list_display = ('code', 'name', 'created', 'modified')
    fields = ('code', 'name')
    search_fields = ('name',)
    ordering = ('name',)
    readonly_fields = ('created', 'modified','deleted_at')
    list_per_page = 10


class DependentInline(TabularInline):
    '''Inline admin for Employee Dependents'''
    model = Dependent
    fields = ('name', 'relationship', 'date_of_birth')
    extra = 1
    tab = True


class EducationHistoryInline(TabularInline):
    '''Inline admin for Employee Education History'''
    model = EducationHistory
    fields = ('institution', 'qualification', 'from_year', 'to_year', 'award_date')
    extra = 1
    tab = True


class WorkHistoryInline(TabularInline):
    '''Inline admin for Employee Work History'''
    model = WorkHistory
    fields = ('employer', 'position', 'from_date', 'to_date', 'responsibilities')
    extra = 1
    compressed_fields = False
    tab = True


class RefereeInline(TabularInline):
    '''Inline admin for Employee Referees'''
    model = Referee
    fields = ('name', 'place_of_work', 'position', 'telephone', 'email')
    extra = 1
    tab = True


@admin.register(Employee)
class EmployeeAdmin(SimpleHistoryAdmin,ModelAdmin):
    '''Admin interface for Employee model.'''
    list_display = ('employee_number', 'system_account', 'department', 'designation', 'created', 'modified')
    inlines = [DependentInline, EducationHistoryInline, WorkHistoryInline, RefereeInline]
    #compressed_fields = False
    #warn_unsaved_form = True
    #list_fullwidth = True
    #form = EmployeeForm
    fieldsets = (
        (
            _("Personal Info"),
            {
                "classes": ["tab"],
                "fields": [
                    "title",
                    "system_account",
                    "department",
                    "designation",
                    "employee_number",
                    "nssf_number",
                    "tin_number",
                    "date_of_birth",
                    "gender",
                    "nationality",
                    "religion",
                    "tribe",
                    "marital_status",
                    "spouse_name",
                    "blood_group",
                    "allergies",
                    "joining_date",
                    "supervisor",
                ],
            },
        ),
        (
            _("Residential Address"),
            {
                "classes": ["tab"],
                "fields": [
                    "district",
                    "county",
                    "sub_county",
                    "parish",
                    "village",
                    "distance_from_work",
                    "address",
                ],
            },
        ),
        (
            _("Place of Origin"),
            {
                "classes": ["tab"],
                "fields": [
                    "district_of_origin",
                    "county_of_origin",
                    "sub_county_of_origin",
                    "parish_of_origin",
                    "village_of_origin",
                    "address_of_origin",
                ],
            },
        ),
         (
            _("Next of Kin"),
            {
                "classes": ["tab"],
                "fields": [
                    "next_of_kin_name",
                    "next_of_kin_relationship",
                    "next_of_kin_date_of_birth",
                    "occupation",
                    "work_place",
                    "next_of_kin_phone_number",
                    "next_of_kin_email",
                    "next_of_kin_address",
                ],
            },
        ), 
        (
            _("Parents"),
            {
                "classes": ["tab"],
                "fields": [
                    "father_name",
                    "father_status",
                    "father_contact",
                    "mother_name",
                    "mother_status",
                    "mother_contact",
                ],
            },
        ), 
        (
            _("Identification"),
            {
                "classes": ["tab"],
                "fields": [
                    "nin",
                    "national_id_document",
                    "passport_photo",
                    "license_number",
                    "class_of_license",
                    "date_of_issue",
                    "date_of_expiry",
                    "license_document",
                    "passport_number",
                    "passport_type",
                    "issue_date",
                    "expiry_date",
                    "place_of_issue",
                ],
            },
        ),
        (
            _("Bank Details"),
            {
                "classes": ["tab"],
                "fields": [
                    "bank_name",
                    "branch",
                    "account_name",
                    "account_number",
                ],
            },
        ),
    )
    search_fields = ('employee_number', 'system_account__username', 'system_account__first_name', 'system_account__last_name')
    ordering = ('employee_number',)
    filter_fields = ('department', 'designation', 'gender', 'nationality', 'religion', 'tribe', 'district', 'county', 'sub_county', 'marital_status', 'highest_education_level')
    readonly_fields = ('created', 'modified','deleted_at')
    autocomplete_fields = ('system_account',)
    formfield_overrides = {
        # models.TextField: {
        #     "widget": WysiwygWidget,
        # },
        ArrayField: {
            "widget": ArrayWidget,
        }
    }
    list_per_page = 10
    list_max_show_all = 1000
    list_disable_select_all = False
