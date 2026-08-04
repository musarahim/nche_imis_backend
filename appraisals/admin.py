from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import (AdditionalQualification, ImprovementArea,
                     InitialQualification, NextYearPerformancePlan,
                     PerformanceAppraisal)


# Register your models here.
@admin.register(PerformanceAppraisal)
class PerformanceAppraisalAdmin(ModelAdmin):
    pass

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
