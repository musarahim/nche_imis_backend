from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from unfold.admin import ModelAdmin

from .models import (County, District, EducationLevel, Holiday, Nationality,
                     Parish, Region, Relationship, Religion, SubCounty, Title,
                     Tribe, Village)

# Register your models here.

@admin.register(District)
class DistrictAdmin(SimpleHistoryAdmin,ModelAdmin):
    '''Admin interface for District model.'''
    list_display = ('name', 'created', 'modified')
    fields = ('name',)
    search_fields = ('name',)
    ordering = ('name',)
    list_per_page = 10
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
    list_display = ('name', 'district', 'modified')
    fields = ('name', 'district' )
    search_fields = ('name',)
    ordering = ('name',)
    filter_fields = ('district',)
    list_per_page = 10
    readonly_fields = ('created', 'modified','deleted_at')

@admin.register(SubCounty)
class SubCountyAdmin(SimpleHistoryAdmin,ModelAdmin):
    '''Admin interface for District model.'''
    list_display = ('name', 'county', 'created', 'modified')
    fields = ('name', 'county')
    search_fields = ('name',)
    ordering = ('name',)
    filter_fields = ('county',)
    list_per_page = 10
    readonly_fields = ('created', 'modified','deleted_at')

@admin.register(Parish)
class ParishAdmin(SimpleHistoryAdmin,ModelAdmin):
    '''Admin interface for District model.'''
    list_display = ('name', 'sub_county', 'created', 'modified')
    fields = ('name', 'sub_county')
    search_fields = ('name',)
    ordering = ('name',)
    filter_fields = ('sub_county',)
    list_per_page = 10
    readonly_fields = ('created', 'modified','deleted_at')
    
@admin.register(Village)
class VillageAdmin(SimpleHistoryAdmin,ModelAdmin):
    '''Admin interface for District model.'''
    list_display = ('name', 'parish', 'created', 'modified')
    fields = ('name', 'parish')
    search_fields = ('name',)
    ordering = ('name',)
    filter_fields = ('parish',)
    list_per_page = 10
    readonly_fields = ('created', 'modified','deleted_at')
    

@admin.register(EducationLevel)
class EducationLevelAdmin(SimpleHistoryAdmin,ModelAdmin):
    '''Admin interface for District model.'''
    list_display = ('name', 'created', 'modified')
    fields = ('name',)
    search_fields = ('name',)
    ordering = ('name',)
    list_per_page = 10
    readonly_fields = ('created', 'modified','deleted_at')


@admin.register(Title)
class TitleAdmin(SimpleHistoryAdmin,ModelAdmin):
    '''Admin interface for District model.'''
    list_display = ('name', 'created', 'modified')
    fields = ('name',)
    search_fields = ('name',)
    ordering = ('name',)
    list_per_page = 10
    readonly_fields = ('created', 'modified','deleted_at')

@admin.register(Tribe)
class TribeAdmin(SimpleHistoryAdmin,ModelAdmin):
    '''Admin interface for District model.'''
    list_display = ('name', 'created', 'modified')
    fields = ('name',)
    search_fields = ('name',)
    ordering = ('name',)
    list_per_page = 10
    readonly_fields = ('created', 'modified','deleted_at')


@admin.register(Religion)
class ReligionAdmin(SimpleHistoryAdmin,ModelAdmin):
    '''Admin interface for District model.'''
    list_display = ('name', 'created', 'modified')
    fields = ('name',)
    search_fields = ('name',)
    ordering = ('name',)
    list_per_page = 10
    readonly_fields = ('created', 'modified','deleted_at')



@admin.register(Region)
class RegionAdmin(SimpleHistoryAdmin,ModelAdmin):
    '''Admin interface for Region model.'''
    list_display = ('name', 'code', 'created', 'modified')
    fields = ('name', 'code')
    search_fields = ('name', 'code')
    ordering = ('name',)
    list_per_page = 10
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
    list_per_page = 10
    def get_queryset(self, request):
        """
        Override to ensure that only active nationalities are shown.
        """
        return super().get_queryset(request).filter(deleted_at__isnull=True)
    
@admin.register(Holiday)
class HolidayAdmin(SimpleHistoryAdmin,ModelAdmin):
    '''Admin interface for Holiday model.'''
    list_display = ('name', 'date', 'created', 'modified')
    fields = ('name', 'date')
    search_fields = ('name',)
    ordering = ('date',)
    readonly_fields = ('created', 'modified','deleted_at')
    list_per_page = 10
    

@admin.register(Relationship)
class RelationshipAdmin(SimpleHistoryAdmin,ModelAdmin):
    '''Admin interface for Relationship model.'''
    list_display = ('name', 'created', 'modified')
    fields = ('name',)
    search_fields = ('name',)
    ordering = ('name',)
    readonly_fields = ('created', 'modified','deleted_at')
    list_per_page = 10