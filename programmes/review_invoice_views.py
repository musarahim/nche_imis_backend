from io import BytesIO
from smtplib import SMTPException

from accounts.models import User
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import Q
from institutions.models import Institution
from django.http import FileResponse
from rest_framework import filters, parsers, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError
from rest_framework.response import Response

from .invoice_permissions import can_create_review_invoices, can_manage_review_invoices
from .models import ProgrammeAssessmentInvoice, ProgramAccreditation, DeskReviewInvoiceLine, DeskReviewPaymentVerification
from .serializers import ProgrammeAssessmentInvoiceSerializer, ReviewInvoicePaymentSerializer, ReviewInvoiceVerificationSerializer


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
    search_fields = ['lines__application_number', 'lines__programme_name', 'invoice_number', 'institution__name', 'status', 'payment_reference']
    ordering_fields = ['invoice_date', 'invoice_number', 'status', 'grand_total']
    http_method_names = ['get', 'post', 'patch', 'put', 'head', 'options']

    def get_queryset(self):
        queryset = self.queryset.select_related('institution', 'institution__user').prefetch_related('lines', 'verifications__verified_by')
        user = self.request.user
        if can_create_review_invoices(user) or can_manage_review_invoices(user) or user.has_perm('programmes.view_programmeassessmentinvoice'):
            return queryset.order_by('-invoice_date', '-pk')
        institution = getattr(user, 'institution', None)
        if institution:
            return queryset.filter(institution=institution).exclude(status='draft').order_by('-invoice_date', '-pk')
        return queryset.none()

    def _require_accounts(self):
        if not can_manage_review_invoices(self.request.user):
            raise PermissionDenied('Only accounts staff can perform this action.')

    def _require_programme_head(self):
        if not can_create_review_invoices(self.request.user):
            raise PermissionDenied('Only Head Programme Accreditation staff can prepare and send review invoices.')

    @staticmethod
    def _available_programmes_queryset():
        invoiced = DeskReviewInvoiceLine.objects.exclude(invoice__status='cancelled').values('application_id')
        return ProgramAccreditation.objects.filter(status='reviewed').exclude(pk__in=invoiced)

    @action(detail=False, methods=['get'], url_path='creation-options')
    def creation_options(self, request):
        from .review_invoice_pdf import payment_details
        allowed = can_create_review_invoices(request.user)
        return Response({'can_create': allowed, 'institutions': list(
            Institution.objects.filter(pk__in=self._available_programmes_queryset().values('institution_id'))
            .order_by('name').values('id', 'name')
        ) if allowed else [], 'payment_instructions': payment_details() if allowed else None})

    @action(detail=False, methods=['get'], url_path='available-programmes')
    def available_programmes(self, request):
        self._require_programme_head()
        institution_id = request.query_params.get('institution_id', '')
        if not institution_id.isdigit():
            raise ValidationError({'institution_id': 'Select an institution.'})
        applications = self._available_programmes_queryset().filter(
            institution_id=institution_id,
        ).order_by('programme_name', 'pk')
        return Response(list(applications.values('id', 'application_number', 'programme_name', 'program_level')))

    def _validate_lines(self, lines, invoice=None):
        ids = [line['application'].pk for line in lines]
        applications = list(ProgramAccreditation.objects.select_for_update().filter(pk__in=ids).order_by('pk'))
        existing_ids = set(invoice.lines.values_list('application_id', flat=True)) if invoice else set()
        duplicates = DeskReviewInvoiceLine.objects.filter(application_id__in=ids).exclude(invoice__status='cancelled')
        if invoice:
            duplicates = duplicates.exclude(invoice=invoice)
        if duplicates.exists():
            raise ValidationError({'lines': 'One or more programmes already have an active desk review invoice.'})
        if any(app.status != ('invoiced' if app.pk in existing_ids else 'reviewed') for app in applications):
            raise ValidationError({'lines': 'Only reviewed programmes may be selected for desk review invoicing.'})
        return ids

    def _locked_invoice(self):
        # get_object applies institution scoping before taking the row lock.
        invoice = self.get_object()
        return ProgrammeAssessmentInvoice.objects.select_for_update().get(pk=invoice.pk)

    @action(detail=True, methods=['get'], url_path='pdf')
    def download_pdf(self, request, pk=None):
        from .review_invoice_pdf import build_review_invoice_pdf
        invoice = self.get_object()
        return FileResponse(BytesIO(build_review_invoice_pdf(invoice)), content_type='application/pdf',
            as_attachment=True, filename=f'{invoice.invoice_number.replace("/", "-")}.pdf')

    @staticmethod
    def _require_status(invoice, expected):
        if invoice.status != expected or invoice.cleared:
            raise ValidationError(f'This action requires an {expected} invoice that has not been acknowledged.')

    @staticmethod
    def _institution_email(invoice):
        institution = invoice.institution
        recipient = getattr(getattr(institution, 'user', None), 'email', None) or institution.email
        if not recipient:
            raise ValidationError('The institution needs an email address before this action can be completed.')
        return recipient

    @staticmethod
    def _send_email(invoice, recipients, subject, message, attach_invoice=False):
        body = (
            f'{message}\n\nInvoice: {invoice.invoice_number}\n'
            f'Institution: {invoice.institution.name}\n'
            + ''.join(f'Programme: {line.programme_name} ({line.application_number}) - UGX {line.desk_review_fee:,.2f}\n' for line in invoice.lines.all()) +
            f'Total (UGX): {invoice.grand_total:,.2f}\n'
            f'Payment reference: {invoice.payment_reference or "-"}\n'
        )
        email = EmailMessage(subject=subject, body=body, to=recipients)
        if attach_invoice:
            from .review_invoice_pdf import build_review_invoice_pdf
            email.attach(f'{invoice.invoice_number.replace("/", "-")}.pdf', build_review_invoice_pdf(invoice), 'application/pdf')
        try:
            if email.send(fail_silently=False) != 1:
                raise InvoiceNotificationError()
        except (SMTPException, OSError) as exc:
            raise InvoiceNotificationError() from exc

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        self._require_programme_head()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application_ids = self._validate_lines(serializer.validated_data['lines'])
        invoice = serializer.save(status='draft', cleared=False)
        ProgramAccreditation.objects.filter(pk__in=application_ids).update(status='invoiced', is_paid=False)
        return Response(self.get_serializer(invoice).data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        self._require_programme_head()
        invoice = self._locked_invoice()
        self._require_status(invoice, 'draft')
        serializer = self.get_serializer(invoice, data=request.data, partial=kwargs.pop('partial', False))
        serializer.is_valid(raise_exception=True)
        if 'lines' in serializer.validated_data:
            old_ids = set(invoice.lines.values_list('application_id', flat=True))
            new_ids = set(self._validate_lines(serializer.validated_data['lines'], invoice))
            ProgramAccreditation.objects.filter(pk__in=old_ids - new_ids, status='invoiced').update(status='reviewed', is_paid=False)
            ProgramAccreditation.objects.filter(pk__in=new_ids).update(status='invoiced', is_paid=False)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='send-invoice')
    @transaction.atomic
    def send_invoice(self, request, pk=None):
        self._require_programme_head()
        invoice = self._locked_invoice()
        self._require_status(invoice, 'draft')
        if not invoice.lines.exists() or invoice.desk_review_fee <= 0:
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
        if getattr(request.user, 'institution', None) != invoice.institution:
            raise PermissionDenied('Only the institution that owns this invoice can submit payment details.')
        if not (invoice.status == 'paid' and invoice.verified_amount > 0 and not invoice.cleared):
            self._require_status(invoice, 'issued')
        serializer = ReviewInvoicePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipients = list(User.objects.filter(is_active=True).filter(
            Q(groups__name='Finance Officer')
            | Q(groups__permissions__content_type__app_label='programmes', groups__permissions__codename='can_manage_invoices')
            | Q(user_permissions__content_type__app_label='programmes', user_permissions__codename='can_manage_invoices')
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
        serializer = ReviewInvoiceVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data['verified_amount']
        if amount <= invoice.verified_amount or amount > invoice.grand_total:
            raise ValidationError({'verified_amount': 'Enter a cumulative verified total above the previous verified amount and no greater than the invoice total.'})
        invoice.verified_amount = amount
        invoice.cleared = amount == invoice.grand_total
        invoice.status = 'reconciled' if invoice.cleared else 'paid'
        invoice.save()
        DeskReviewPaymentVerification.objects.create(invoice=invoice, verified_total=amount,
            verified_by=request.user, payment_reference=invoice.payment_reference,
            payment_receipt=invoice.payment_receipt.name, payment_date=invoice.payment_date)
        if invoice.cleared:
            ProgramAccreditation.objects.filter(desk_review_invoice_lines__invoice=invoice).update(status='invoice_reconciled', is_paid=True)
        self._send_email(invoice, [self._institution_email(invoice)], 'NCHE Review Invoice Payment Acknowledged',
                         f'Accounts has verified UGX {amount:,.2f}. Outstanding balance: UGX {invoice.outstanding_balance:,.2f}. '
                         + ('All programmes on this invoice are cleared for assessor assignment.' if invoice.cleared else 'Programmes remain blocked until the full invoice is verified.'))
        return Response(self.get_serializer(invoice).data)
