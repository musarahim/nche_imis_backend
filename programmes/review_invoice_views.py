from io import BytesIO
from smtplib import SMTPException

from accounts.models import User
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import Q
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from rest_framework import filters, parsers, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError
from rest_framework.response import Response

from .invoice_permissions import can_create_review_invoices, can_manage_review_invoices
from .models import ProgrammeAssessmentInvoice
from .serializers import ProgrammeAssessmentInvoiceSerializer, ReviewInvoicePaymentSerializer


class InvoiceNotificationError(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'The email notification could not be sent. No invoice status change was saved. Please try again.'


class ProgrammeAssessmentInvoiceViewset(viewsets.ModelViewSet):
    """Draft -> issued -> payment submitted -> acknowledged by accounts."""
    queryset = ProgrammeAssessmentInvoice.objects.all()
    serializer_class = ProgrammeAssessmentInvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['application__application_number', 'invoice_number', 'application__institution__name', 'status', 'payment_reference']
    ordering_fields = ['invoice_date', 'invoice_number', 'status', 'grand_total']
    http_method_names = ['get', 'post', 'patch', 'put', 'head', 'options']

    def get_queryset(self):
        queryset = self.queryset.select_related('application', 'application__institution', 'application__institution__user')
        user = self.request.user
        if can_create_review_invoices(user) or user.has_perm('programmes.view_programmeassessmentinvoice'):
            return queryset.order_by('-invoice_date', '-pk')
        institution = getattr(user, 'institution', None)
        if institution:
            return queryset.filter(application__institution=institution).exclude(status='draft').order_by('-invoice_date', '-pk')
        return queryset.none()

    def _require_accounts(self):
        if not can_manage_review_invoices(self.request.user):
            raise PermissionDenied('Only accounts staff can perform this action.')

    def _locked_invoice(self):
        # get_object applies institution scoping before taking the row lock.
        invoice = self.get_object()
        return ProgrammeAssessmentInvoice.objects.select_for_update().get(pk=invoice.pk)

    @staticmethod
    def _require_status(invoice, expected):
        if invoice.status != expected or invoice.cleared:
            raise ValidationError(f'This action requires an {expected} invoice that has not been acknowledged.')

    @staticmethod
    def _institution_email(invoice):
        institution = invoice.application.institution
        recipient = getattr(getattr(institution, 'user', None), 'email', None) or institution.email
        if not recipient:
            raise ValidationError('The institution needs an email address before this action can be completed.')
        return recipient

    @staticmethod
    def _send_email(invoice, recipients, subject, message, attach_invoice=False):
        body = (
            f'{message}\n\nInvoice: {invoice.invoice_number}\n'
            f'Application: {invoice.application.application_number}\n'
            f'Institution: {invoice.application.institution.name}\n'
            f'Programme: {invoice.application.program_name}\n'
            f'Total (UGX): {invoice.grand_total:,.2f}\n'
            f'Payment reference: {invoice.payment_reference or "-"}\n'
        )
        email = EmailMessage(subject=subject, body=body, to=recipients)
        if attach_invoice:
            buffer = BytesIO()
            pdf = canvas.Canvas(buffer, pagesize=A4)
            pdf.setFont('Helvetica-Bold', 14)
            pdf.drawString(45, 790, 'NCHE Programme Accreditation Review Invoice')
            pdf.setFont('Helvetica', 10)
            lines = [
                f'Invoice: {invoice.invoice_number}',
                f'Date: {invoice.invoice_date}',
                f'Application: {invoice.application.application_number}',
                f'Institution: {invoice.application.institution.name}',
                f'Desk review fee (UGX): {invoice.desk_review_fee:,.2f}',
                f'Administrative fee (10%) (UGX): {invoice.administrative_fee:,.2f}',
                f'Total (UGX): {invoice.grand_total:,.2f}',
                'Submit your receipt and payment reference through the institution portal.',
            ]
            for index, line in enumerate(lines):
                pdf.drawString(45, 760 - index * 22, line)
            pdf.save()
            email.attach(f'{invoice.invoice_number.replace("/", "-")}.pdf', buffer.getvalue(), 'application/pdf')
        try:
            if email.send(fail_silently=False) != 1:
                raise InvoiceNotificationError()
        except (SMTPException, OSError) as exc:
            raise InvoiceNotificationError() from exc

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        if not can_create_review_invoices(request.user):
            raise PermissionDenied('Only programme or accounts staff can create review invoices.')
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = serializer.validated_data['application']
        # Serialize creation for an application and avoid duplicate active invoices.
        application = type(application).objects.select_for_update().get(pk=application.pk)
        if application.assessment_invoices.exclude(status='cancelled').exists():
            raise ValidationError('This application already has a review invoice.')
        invoice = serializer.save(status='draft', cleared=False)
        application.status = 'invoiced'
        application.save(update_fields=['status'])
        return Response(self.get_serializer(invoice).data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        self._require_accounts()
        invoice = self._locked_invoice()
        self._require_status(invoice, 'draft')
        serializer = self.get_serializer(invoice, data=request.data, partial=kwargs.pop('partial', False))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='send-invoice')
    @transaction.atomic
    def send_invoice(self, request, pk=None):
        self._require_accounts()
        invoice = self._locked_invoice()
        self._require_status(invoice, 'draft')
        if invoice.desk_review_fee <= 0:
            raise ValidationError('Enter a desk review fee greater than zero before sending the invoice.')
        recipient = self._institution_email(invoice)
        invoice.status = 'issued'
        invoice.save()
        self._send_email(invoice, [recipient], 'NCHE Programme Review Invoice',
                         'Your review invoice is ready. Log in to your institution portal and open Desk Review Invoices to view it and submit proof of payment.',
                         attach_invoice=True)
        return Response(self.get_serializer(invoice).data)

    @action(detail=True, methods=['post'], url_path='add-payment-details')
    @transaction.atomic
    def add_payment_details(self, request, pk=None):
        invoice = self._locked_invoice()
        if getattr(request.user, 'institution', None) != invoice.application.institution:
            raise PermissionDenied('Only the institution that owns this invoice can submit payment details.')
        self._require_status(invoice, 'issued')
        serializer = ReviewInvoicePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipients = list(User.objects.filter(is_active=True).filter(
            Q(groups__name='Finance Officer')
            | Q(groups__permissions__content_type__app_label='programmes', groups__permissions__codename__in=['can_manage_invoices', 'change_programmeassessmentinvoice'])
            | Q(user_permissions__content_type__app_label='programmes', user_permissions__codename__in=['can_manage_invoices', 'change_programmeassessmentinvoice'])
        ).exclude(email='').values_list('email', flat=True).distinct())
        if not recipients:
            raise ValidationError('No accounts notification recipient is configured. Please contact NCHE accounts.')
        for field, value in serializer.validated_data.items():
            setattr(invoice, field, value)
        invoice.status = 'paid'
        # Notify before storing the file so notification failures do not leave an orphan upload.
        self._send_email(invoice, recipients, 'NCHE Review Invoice Payment Submitted',
                         'Payment proof has been submitted. Open Desk Review Invoices in IMIS to inspect the receipt and acknowledge the payment.')
        invoice.save()
        return Response(self.get_serializer(invoice).data)

    @action(detail=True, methods=['post'], url_path='reconcile-invoice')
    @transaction.atomic
    def reconcile_invoice(self, request, pk=None):
        self._require_accounts()
        invoice = self._locked_invoice()
        self._require_status(invoice, 'paid')
        if not invoice.payment_receipt or not invoice.payment_reference:
            raise ValidationError('A receipt and payment reference are required before acknowledgement.')
        invoice.status = 'reconciled'
        invoice.cleared = True
        invoice.save()
        application = invoice.application
        application.status = 'invoice_reconciled'
        application.is_paid = True
        application.save(update_fields=['status', 'is_paid'])
        self._send_email(invoice, [self._institution_email(invoice)], 'NCHE Review Invoice Payment Acknowledged',
                         'Accounts has verified and acknowledged your payment. Your programme application can proceed to the next stage.')
        return Response(self.get_serializer(invoice).data)
