from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from unfold.admin import ModelAdmin

from .models import (County, District, EducationLevel, Nationality, Parish,
                     Region, Religion, SubCounty, Title, Tribe, Village)

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
    
@admin.register(County)
class CountyAdmin(SimpleHistoryAdmin,ModelAdmin):
    '''Admin interface for District model.'''
    list_display = ('code', 'name', 'district', 'modified')
    fields = ('code','name', 'district' )
    search_fields = ('name', 'code')
    ordering = ('name',)
    filter_fields = ('district',)
    readonly_fields = ('created', 'modified','deleted_at')

@admin.register(SubCounty)
class SubCountyAdmin(SimpleHistoryAdmin,ModelAdmin):
    '''Admin interface for District model.'''
    list_display = ('name', 'code', 'county', 'created', 'modified')
    fields = ('name', 'code', 'county')
    search_fields = ('name', 'code')
    ordering = ('name',)
    filter_fields = ('county',)
    readonly_fields = ('created', 'modified','deleted_at')

@admin.register(Parish)
class ParishAdmin(SimpleHistoryAdmin,ModelAdmin):
    '''Admin interface for District model.'''
    list_display = ('name', 'code', 'sub_county', 'created', 'modified')
    fields = ('name', 'code', 'sub_county')
    search_fields = ('name', 'code')
    ordering = ('name',)
    filter_fields = ('sub_county',)
    readonly_fields = ('created', 'modified','deleted_at')
    
@admin.register(Village)
class VillageAdmin(SimpleHistoryAdmin,ModelAdmin):
    '''Admin interface for District model.'''
    list_display = ('name', 'code', 'parish', 'created', 'modified')
    fields = ('name', 'code', 'parish')
    search_fields = ('name', 'code')
    ordering = ('name',)
    filter_fields = ('parish',)
    readonly_fields = ('created', 'modified','deleted_at')
    

@admin.register(EducationLevel)
class EducationLevelAdmin(SimpleHistoryAdmin,ModelAdmin):
    '''Admin interface for District model.'''
    list_display = ('name', 'created', 'modified')
    fields = ('name',)
    search_fields = ('name',)
    ordering = ('name',)
    readonly_fields = ('created', 'modified','deleted_at')


@admin.register(Title)
class TitleAdmin(SimpleHistoryAdmin,ModelAdmin):
    '''Admin interface for District model.'''
    list_display = ('name', 'created', 'modified')
    fields = ('name',)
    search_fields = ('name',)
    ordering = ('name',)
    readonly_fields = ('created', 'modified','deleted_at')

@admin.register(Tribe)
class TribeAdmin(SimpleHistoryAdmin,ModelAdmin):
    '''Admin interface for District model.'''
    list_display = ('name', 'created', 'modified')
    fields = ('name',)
    search_fields = ('name',)
    ordering = ('name',)
    readonly_fields = ('created', 'modified','deleted_at')


@admin.register(Religion)
class ReligionAdmin(SimpleHistoryAdmin,ModelAdmin):
    '''Admin interface for District model.'''
    list_display = ('name', 'created', 'modified')
    fields = ('name',)
    search_fields = ('name',)
    ordering = ('name',)
    readonly_fields = ('created', 'modified','deleted_at')



@admin.register(Region)
class RegionAdmin(SimpleHistoryAdmin,ModelAdmin):
    '''Admin interface for Region model.'''
    list_display = ('name', 'code', 'created', 'modified')
    fields = ('name', 'code')
    search_fields = ('name', 'code')
    ordering = ('name',)
    readonly_fields = ('created', 'modified','deleted_at')
    
    def get_queryset(self, request):
        """
        Override to ensure that only active regions are shown.
        """
        return super().get_queryset(request).filter(deleted_at__isnull=True)
    
@admin.register(Nationality)
class NationalityAdmin(SimpleHistoryAdmin,ModelAdmin):
    '''Admin interface for District model.'''
    list_display = ('name', 'created', 'modified')
    fields = ('name',)
    search_fields = ('name',)
    ordering = ('name',)
    readonly_fields = ('created', 'modified','deleted_at')
    def get_queryset(self, request):
        """
        Override to ensure that only active nationalities are shown.
        """
        return super().get_queryset(request).filter(deleted_at__isnull=True)