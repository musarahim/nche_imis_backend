from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import (AdditionalQualification, ImprovementArea,
                     InitialQualification, NextYearPerformancePlan,
                     PerformanceAppraisal)


# Register your models here.
@admin.register(PerformanceAppraisal)
class PerformanceAppraisalAdmin(ModelAdmin):
    list_display = ('appraisee', 'start_date', 'end_date', 'status', 'appraiser', 'reviewer', 'director', 'executive_director')
    list_filter = ('status', 'start_date')
    search_fields = ('appraisee__employee_number', 'appraiser__employee_number')

@admin.register(ImprovementArea)
class ImprovementAreaAdmin(ModelAdmin):
    pass

@admin.register(NextYearPerformancePlan)
class NextYearPerformancePlanAdmin(ModelAdmin):
    pass

@admin.register(InitialQualification)
class InitialQualificationAdmin(ModelAdmin):
    pass

@admin.register(AdditionalQualification)
class AdditionalQualificationAdmin(ModelAdmin):
    pass
