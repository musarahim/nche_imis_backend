from django.contrib import admin
from import_export.admin import ExportActionModelAdmin, ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin
from unfold.admin import ModelAdmin
from unfold.contrib.import_export.forms import (ExportForm, ImportForm,
                                                SelectableFieldsExportForm)

from .models import Institution, LicenseType


@admin.register(LicenseType)
class LicenseTypeAdmin(SimpleHistoryAdmin,ModelAdmin,ExportForm):
    '''Admin interface for District model.'''
    list_display = ('code','name', 'created', 'modified')
    fields = ( 'code','name')
    search_fields = ('name', 'code')
    ordering = ('name',)
    readonly_fields = ('created', 'modified','deleted_at')
    list_disable_select_all = False
    list_per_page = 10
    list_max_show_all = 1000
    # def has_delete_permission(self, request, obj=None):
    #     return False
    # def has_add_permission(self, request):
    #     return False
    # def has_change_permission(self, request, obj=None):
    #     return False
    # def has_view_permission(self, request, obj=None):
    #     return True


# Register your models here.
@admin.register(Institution)
class InstitutionAdmin(ModelAdmin, ExportActionModelAdmin, ImportExportModelAdmin):
    export_form_class = SelectableFieldsExportForm
    import_form_class = ImportForm
    list_display = ("name","tin", "district","institution_type","landline", "user__email")
    search_fields = ("name", "district__name", "user__email")
    #actions = ["export_as_csv"]
    filter = ('institution_type',)  # 
    compressed_fields = False
    # Warn before leaving unsaved changes in changeform
    warn_unsaved_form = True  # Default: False
     # Display submit button in filters
    list_filter_submit = True
    fields=("user","name","acroynm","region","district","institution_type","alternative_email",
            "landline","website","postal_address","contact_person","contact_person_phone","alternative_contact_person","alternative_contact_person_phone","logo","tin", "license","is_closed")
    # Display changelist in fullwidth
    list_fullwidth = False
     # Position horizontal scrollbar in changelist at the top
    list_horizontal_scrollbar_top = False

    # Dsable select all action in changelist
    list_disable_select_all = False
    list_per_page = 10
    list_max_show_all = 1000
    ordering = ['name']



