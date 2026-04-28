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
    list_display = ("id","program_name", "program_level", "accreditation_date", "expiry_date", "status")
    fields = ("applications","program_name","program_level","accreditation_date","expiry_date")