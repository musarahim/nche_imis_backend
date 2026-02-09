from django.contrib import admin
from import_export.admin import ExportActionModelAdmin, ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin
from unfold.admin import ModelAdmin
from unfold.contrib.import_export.forms import SelectableFieldsExportForm

from .models import ApplicationPRNS, PaymentCode

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

@admin.register(ApplicationPRNS)
class ApplicationPRNSAdmin(SimpleHistoryAdmin, ModelAdmin, ExportActionModelAdmin):
    """Admin interface for ApplicationPRNS model (Read-only)."""

    list_display = ("referenceNo", "amount", "assessmentDate", "paymentType", "prn", "statusCode")
    readonly_fields = (
        "referenceNo",
        "amount",
        "assessmentDate",
        "paymentType",
        "tin",
        "srcSystem",
        "taxHead",
        "taxSubHead",
        "email",
        "taxPayerName",
        "plot",
        "buildingName",
        "street",
        "tradeCentre",
        "district",
        "county",
        "subCounty",
        "parish",
        "village",
        "localCouncil",
        "contactNo",
        "paymentPeriod",
        "expiryDays",
        "mobileMoneyNumber",
        "mobileNo",
        "expiryDate",
        "statusCode",
        "statusDesc",
        "searchCode",
        "prn",
    )
    fields = (
        "referenceNo",
        "amount",
        "assessmentDate",
        "paymentType",
        "tin",
        "srcSystem",
        "taxHead",
        "taxSubHead",
        "email",
        "taxPayerName",
        "plot",
        "buildingName",
        "street",
        "tradeCentre",
        "district",
        "county",
        "subCounty",
        "parish",
        "village",
        "localCouncil",
        "contactNo",
        "paymentPeriod",
        "expiryDays",
        "mobileMoneyNumber",
        "mobileNo",
        "expiryDate",
        "statusCode",
        "statusDesc",
        "searchCode",
        "prn",
    )
    search_fields = ("referenceNo", "prn", "tin")
    list_filter = ("statusCode", "paymentType", "taxHead")
    ordering = ("-assessmentDate",)
    export_form_class = SelectableFieldsExportForm
    list_per_page = 10

    def has_add_permission(self, request):
        """Disable adding new records."""
        return False

    def has_change_permission(self, request, obj=None):
        """Disable editing records."""
        return False

    # def has_delete_permission(self, request, obj=None):
    #     """Disable deleting records."""
    #     return False
