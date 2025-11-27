from django.contrib import admin
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _
from simple_history.admin import SimpleHistoryAdmin
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.forms.widgets import ArrayWidget, WysiwygWidget
from unfold.paginator import InfinitePaginator

from .models import ProgrammeAccreditation


@admin.register(ProgrammeAccreditation)
class ProgrammeAccreditationAdmin(ModelAdmin):
    '''Admin interface for Programme Accreditation'''
    list_display = ("id","application_number", "programme_name", "institution","status","date_submitted")

