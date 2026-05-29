from django.contrib import admin
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _
from import_export.admin import ExportActionModelAdmin, ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.forms.widgets import ArrayWidget, WysiwygWidget
from unfold.contrib.import_export.forms import (ExportForm, ImportForm,
                                                SelectableFieldsExportForm)
from unfold.paginator import InfinitePaginator

from .models import (InvoiceItem, InvoiceItemType, PreliminaryReview, Program,
                     ProgramAccreditation, ProgrammeInvoice)


@admin.register(ProgramAccreditation)
class ProgramAccreditationAdmin(ModelAdmin):
    '''Admin interface for Programme Accreditation'''
    list_display = ("application_number", "program_name", "institution","status","date_submitted")
    fields = ("institution","application_type","program_level","program_name","duration_semester","campus","program_structure","letter_of_submission","program_to_renew","preliminary_reviewer","status", "invoice_file", "invoice_number", "invoice_amount","invoice_status","invoice_date","dep_meeting_minutes")



@admin.register(Program)
class ProgramAdmin(ModelAdmin, ExportActionModelAdmin, ImportExportModelAdmin):
    '''Admin interface for Programs under an Accreditation'''
    export_form_class = SelectableFieldsExportForm
    import_form_class = ImportForm
    list_display = ("id","program_name","institution", "program_level", "accreditation_date", "expiry_date", "status_display")
    fields = ("applications","institution","program_name","program_level","accreditation_date","expiry_date","status")
    search_fields = ("program_name", "institution__name")
    list_filter = ('status', 'institution')

    def status_display(self, obj):
        '''Display human-readable status value instead of key'''
        return obj.get_status_display()
    status_display.short_description = 'Status'
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
    list_per_page = 20
    list_max_show_all = 1000


@admin.register(PreliminaryReview)
class PreliminaryReviewAdmin(ModelAdmin):
    '''Admin interface for Preliminary Reviews'''
    list_display = ("application","reviewer",  "expert_progression", "reviewed_at")
    fields = ("application","reviewer","type_of_entry_summary","type_of_entry_comments","entry_requirements_summary","entry_requirements_comments","human_resource_summary","human_resource_comments","facilities_summary","facilities_comments","programme_duration_summary","programme_duration_comments","minimum_graduation_load_summary","minimum_graduation_load_comments","day_students","evening_students","weekend_students","student_comment","expert_progression")
    search_fields = ("program_accreditation__application_number", "reviewer__username")
    list_filter = ('application', 'reviewer')
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
    list_per_page = 20
    list_max_show_all = 1000

@admin.register(ProgrammeInvoice)
class ProgrammeInvoiceAdmin(ModelAdmin):
    '''Admin interface for Programme Invoices'''
    list_display = ("application","invoice_number", "grand_total", "status", "invoice_date")
    fields = ("application","invoice_number", "grand_total", "status", "invoice_date", "invoice_file")
    search_fields = ("application__application_number", "invoice_number")
    list_filter = ('status', 'application')
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
    list_per_page = 20
    list_max_show_all = 1000

@admin.register(InvoiceItem)
class InvoiceItemAdmin(ModelAdmin):
    '''Admin interface for Invoice Items'''
    list_display = ("invoice","item_type", "persons_number", "number_of_days")
    fields = ("invoice","item_type", "persons_number", "number_of_days")
    search_fields = ("invoice__application__application_number", "item_type__name")
    list_filter = ('item_type', 'invoice')
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
    list_per_page = 20
    list_max_show_all = 1000

@admin.register(InvoiceItemType)
class InvoiceItemTypeAdmin(ModelAdmin):
    '''Admin interface for Invoice Item Types'''
    list_display = ("name", "default_rate",'is_active')
    fields = ("name", "default_rate", "is_active")
    search_fields = ("name",)
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
    list_per_page = 20
    list_max_show_all = 1000