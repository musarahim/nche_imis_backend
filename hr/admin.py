from django.contrib import admin
from django.contrib.postgres.fields import ArrayField
from django.db import models
from simple_history.admin import SimpleHistoryAdmin
from unfold.admin import ModelAdmin
from unfold.contrib.forms.widgets import ArrayWidget, WysiwygWidget

from .forms import EmployeeForm
from .models import (Department, Dependent, Designation, Directorate,
                     EducationHistory, Employee, Referee, WorkHistory)


# Register your models here.
@admin.register(Directorate)
class DirectorateAdmin(SimpleHistoryAdmin,ModelAdmin):
    '''Admin interface for Directorate model.'''
    list_display = ('name', 'short_code', 'created', 'modified')
    fields = ('name', 'short_code')
    search_fields = ('name', 'code')
    ordering = ('name',)
    readonly_fields = ('created', 'modified','deleted_at')

@admin.register(Department)
class DepartmentAdmin(SimpleHistoryAdmin,ModelAdmin):
    '''Admin interface for Department model.'''
    list_display = ('name', 'short_code', 'created', 'modified')
    fields = ('name', 'short_code', 'directorate')
    search_fields = ('name', 'code')
    ordering = ('name',)
    filter_fields = ('directorate',)
    readonly_fields = ('created', 'modified','deleted_at')

@admin.register(Designation)
class DesignationAdmin(SimpleHistoryAdmin,ModelAdmin):
    '''Admin interface for Designation model.'''
    list_display = ('name', 'created', 'modified')
    fields = ('name', 'description')
    search_fields = ('name',)
    ordering = ('name',)
    readonly_fields = ('created', 'modified','deleted_at')


@admin.register(Employee)
class EmployeeAdmin(SimpleHistoryAdmin,ModelAdmin):
    '''Admin interface for Employee model.'''
    list_display = ('employee_number', 'system_account', 'department', 'designation', 'created', 'modified')
    compressed_fields = False
    warn_unsaved_form = True
    list_fullwidth = True
    form = EmployeeForm
    # fieldsets = (
    #     (
    #         None,
    #         {
    #             "fields": [
    #                 "system_account",
    #                 "department",
    #                 "employee_number",
    #                 "designation",
    #                 "title",
    #                 "date_of_birth",
    #                 "gender",
    #                 "nationality",
    #                 "religion",
    #                 "tribe",
    #                 "joining_date",
    #             ],
    #         },
    #     ),
        # (
        #     _("Tab 1"),
        #     {
        #         "classes": ["tab"],
        #         "fields": [
        #             "field_3",
        #             "field_4",
        #         ],
        #     },
        # ),
        # (
        #     _("Tab 2"),
        #     {
        #         "classes": ["tab"],
        #         "fields": [
        #             "field_5",
        #             "field_6",
        #         ],
        #     },
        # ),
    #)
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
