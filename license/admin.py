from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from unfold.admin import ModelAdmin

from .models import LicenseType


# Register your models here.
@admin.register(LicenseType)
class LicenseTypeAdmin(SimpleHistoryAdmin,ModelAdmin):
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