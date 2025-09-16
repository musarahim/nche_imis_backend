from django.contrib import admin
from import_export.admin import ExportActionModelAdmin, ImportExportModelAdmin
from unfold.admin import ModelAdmin
from unfold.contrib.import_export.forms import (ExportForm, ImportForm,
                                                SelectableFieldsExportForm)

from .models import Institution


# Register your models here.
@admin.register(Institution)
class InstitutionAdmin(ModelAdmin, ExportActionModelAdmin):
    export_form_class = SelectableFieldsExportForm
    list_display = ("name", "district","institution_type","landline", "user__email")
    search_fields = ("name", "district__name", "user__email")
    #actions = ["export_as_csv"]
    filter = ('institution_type',)  # 
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
    ordering = ['name']



