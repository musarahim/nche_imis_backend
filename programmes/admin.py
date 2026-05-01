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

from .models import Program, ProgramAccreditation


@admin.register(ProgramAccreditation)
class ProgramAccreditationAdmin(ModelAdmin):
    '''Admin interface for Programme Accreditation'''
    list_display = ("id","application_number", "program_name", "institution","status","date_submitted")
    fields = ("institution","application_type","program_level","program_name","duration_semester","campus","program_structure","letter_of_submission","program_to_renew","preliminary_reviewer","status")



@admin.register(Program)
class ProgramAdmin(ModelAdmin, ExportActionModelAdmin, ImportExportModelAdmin):
    '''Admin interface for Programs under an Accreditation'''
    export_form_class = SelectableFieldsExportForm
    import_form_class = ImportForm
    list_display = ("id","program_name","institution", "program_level", "accreditation_date", "expiry_date", "status_display")
    fields = ("applications","institution","program_name","program_level","accreditation_date","expiry_date")
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