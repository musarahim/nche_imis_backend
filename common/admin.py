from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from unfold.admin import ModelAdmin

from .models import District

# Register your models here.

@admin.register(District)
class DistrictAdmin(SimpleHistoryAdmin,ModelAdmin):
    '''Admin interface for District model.'''
    list_display = ('name', 'code', 'created', 'modified')
    fields = ('name', 'code')
    search_fields = ('name', 'code')
    ordering = ('name',)
    readonly_fields = ('created', 'modified','deleted_at')
    
    # def has_delete_permission(self, request, obj=None):
    #     return False
    # def has_add_permission(self, request):
    #     return False
    # def has_change_permission(self, request, obj=None):
    #     return False
    # def has_view_permission(self, request, obj=None):
    #     return True
    def get_queryset(self, request):
        """
        Override to ensure that only active districts are shown.
        """
        return super().get_queryset(request).filter(deleted_at__isnull=True)
