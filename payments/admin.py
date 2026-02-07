from django.contrib import admin
from import_export.admin import ExportActionModelAdmin, ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin
from unfold.admin import ModelAdmin
from unfold.contrib.import_export.forms import SelectableFieldsExportForm

from .models import PaymentCode

# Register your models here.


@admin.register(PaymentCode)
class PaymentCodeAdmin(
    SimpleHistoryAdmin, ModelAdmin, ExportActionModelAdmin, ImportExportModelAdmin
):
    """Admin interface for PaymentCode model."""

    list_display = ("code", "payment_tax_head", "available", "base_value")
    fields = (
        "code",
        "payment_tax_head",
        "available",
        "base_value",
        "base_value_currency",
        "tax_head_currency",
    )
    search_fields = ("code", "payment_tax_head")
    ordering = ("code",)
    export_form_class = SelectableFieldsExportForm
    list_per_page = 10
