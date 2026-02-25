from django.contrib import admin
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _
from simple_history.admin import SimpleHistoryAdmin
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.forms.widgets import ArrayWidget, WysiwygWidget
from unfold.paginator import InfinitePaginator

from .models import Program, ProgramAccreditation


@admin.register(ProgramAccreditation)
class ProgramAccreditationAdmin(ModelAdmin):
    '''Admin interface for Programme Accreditation'''
    list_display = ("id","application_number", "program_name", "institution","status","date_submitted")
    fields = ("institution","application_type","program_level","program_name","duration_semester","campus","program_structure","letter_of_submission","program_to_renew","status")



@admin.register(Program)
class ProgramAdmin(ModelAdmin):
    '''Admin interface for Programs under an Accreditation'''
    list_display = ("id","program_name", "program_level", "accreditation_date", "expiry_date", "status")
    fields = ("applications","program_name","program_level","accreditation_date","expiry_date")