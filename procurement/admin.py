from django.contrib import admin
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _
from import_export.admin import ExportActionModelAdmin, ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin
from unfold.admin import ModelAdmin, TabularInline

# Register your models here.
from .models import ProcurementBudget, ProcurementExpenditure, ProcurementItem


@admin.register(ProcurementItem)
class ProcurementItemAdmin(SimpleHistoryAdmin, ModelAdmin):
    list_display = ('name', 'created', 'modified')
    search_fields = ('name',)
    readonly_fields = ('created', 'modified', 'deleted_at')

@admin.register(ProcurementBudget)
class ProcurementBudgetAdmin(SimpleHistoryAdmin, ModelAdmin):
    list_display = ('item__name', 'amount', 'current_balance', 'fiscal_year', 'department', 'created', 'modified')
    search_fields = ('item__name',)
    readonly_fields = ('created', 'modified', 'deleted_at')

@admin.register(ProcurementExpenditure)
class ProcurementExpenditureAdmin(SimpleHistoryAdmin, ModelAdmin):
    list_display = ('budget__item__name', 'budget', 'amount', 'created', 'modified')
    search_fields = ('budget__item__name',)
    readonly_fields = ('created', 'modified', 'deleted_at')
