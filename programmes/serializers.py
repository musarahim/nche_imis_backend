import json
from decimal import Decimal
from pathlib import Path
from accounts.serializers import UserReviewerSerializer
from institutions.models import Institution

from django.utils import timezone
from rest_framework import serializers

from .models import (InvoiceItem, InvoiceItemType, PreliminaryReview, Program,
                     ProgramAccreditation, ProgrammeAssessment,
                     ProgrammeAssessmentInvoice, ProgrammeInvoice, DeskReviewInvoiceLine)


class ProgrammeReviewerWorkloadSerializer(UserReviewerSerializer):
    assigned_application_count = serializers.IntegerField(read_only=True)

    class Meta(UserReviewerSerializer.Meta):
        fields = ['id', 'name', 'assigned_application_count']
        ref_name = 'programme reviewer workload'


class ProgrammeAssessorWorkloadSerializer(ProgrammeReviewerWorkloadSerializer):
    class Meta(ProgrammeReviewerWorkloadSerializer.Meta):
        ref_name = 'programme assessor workload'


class ProgrammeAccreditationSerializer(serializers.ModelSerializer):
    '''Serializer for Programme Accreditation applications'''
    can_approve = serializers.SerializerMethodField()

    class Meta:
        model = ProgramAccreditation
        fields = '__all__'
        read_only_fields = ['application_number', 'date_submitted', 'institution', 'status',
                            'preliminary_reviewer', 'assessor', 'pod_comment', 'pod_comment_date',
                            'director_comment', 'director_comment_date', 'is_paid', 'rejection_reason',
                            'previous_accreditation_date', 'previous_expiry_date',
                            'decision_date', 'approved_expiry_date']

    def get_can_approve(self, instance):
        request = self.context.get('request')
        return bool(request and request.user.has_perm('programmes.can_approve_programme_at_management_level')
                    and instance.status == 'progressed_to_management')

    def validate(self, attrs):
        request = self.context.get('request')
        institution = getattr(request.user, 'institution', None) if request else None
        application_type = attrs.get('application_type', self.instance.application_type if self.instance else 'accredit')
        programme = attrs.get('program_to_renew', self.instance.program_to_renew if self.instance else None)

        if self.instance and ('application_type' in attrs or 'program_to_renew' in attrs):
            raise serializers.ValidationError('The application type and linked programme cannot be changed after submission.')
        if self.instance:
            if application_type in ('re-accredit', 'renewal') and programme and (
                attrs.get('programme_name', self.instance.programme_name) != programme.programme_name
                or attrs.get('program_level', self.instance.program_level) != programme.program_level
            ):
                raise serializers.ValidationError({'program_to_renew': 'The programme name and level must match the selected programme.'})
            return attrs
        if application_type == 're-accredit':
            if not programme:
                raise serializers.ValidationError({'program_to_renew': 'Select an accredited programme for re-accreditation.'})
            if not institution or programme.institution_id != institution.pk:
                raise serializers.ValidationError({'program_to_renew': 'Select a programme belonging to your institution.'})
            if not programme.accreditation_date or not programme.expiry_date:
                raise serializers.ValidationError({'program_to_renew': 'This programme has not been accredited.'})
            if ProgramAccreditation.objects.filter(program_to_renew=programme).exclude(status__in=['approved', 'rejected']).exists():
                raise serializers.ValidationError({'program_to_renew': 'This programme already has an open re-accreditation application.'})
            if attrs.get('programme_name', programme.programme_name) != programme.programme_name or attrs.get('program_level', programme.program_level) != programme.program_level:
                raise serializers.ValidationError({'program_to_renew': 'The programme name and level must match the selected programme.'})
        elif programme:
            raise serializers.ValidationError({'program_to_renew': 'Only re-accreditation applications can select an existing programme.'})
        elif application_type == 'accredit' and institution and Program.objects.filter(
            institution=institution, programme_name=attrs.get('programme_name')
        ).exists():
            raise serializers.ValidationError({'programme_name': 'This programme already exists. Apply for re-accreditation instead.'})
        return attrs

    def to_representation(self, instance):
        '''Custom representation to include institution name and display choices'''
        response = super().to_representation(instance)
        response['institution'] = instance.institution.name if instance.institution else None
        response['application_type'] = instance.get_application_type_display()
        response['program_level'] = instance.get_program_level_display()
        response['status'] = instance.get_status_display()
        response['programme_category'] = instance.get_programme_category_display() if instance.programme_category else None
        response['date_submitted'] = instance.date_submitted.strftime('%d-%m-%Y') if instance.date_submitted else None
        request = self.context.get('request')
        response['program_structure'] = request.build_absolute_uri(instance.program_structure.url) if instance.program_structure and request else (instance.program_structure.url if instance.program_structure else None)
        response['financial_implications_certificate'] = request.build_absolute_uri(instance.financial_implications_certificate.url) if instance.financial_implications_certificate and request else (instance.financial_implications_certificate.url if instance.financial_implications_certificate else None)
        response['letter_of_submission'] = request.build_absolute_uri(instance.letter_of_submission.url) if instance.letter_of_submission and request else (instance.letter_of_submission.url if instance.letter_of_submission else None)
        response['review_date'] = instance.preliminary_reviewers.first().reviewed_at.strftime('%d-%m-%Y') if instance.preliminary_reviewers.first() and instance.preliminary_reviewers.first().reviewed_at else None
        response['expert_progression'] = instance.preliminary_reviewers.first().get_expert_progression_display() if instance.preliminary_reviewers.first() and instance.preliminary_reviewers.first().expert_progression else None
        response['review_id'] = instance.preliminary_reviewers.first().id if instance.preliminary_reviewers.first() else None
        response['duration_type'] = instance.get_duration_type_display()
        if instance.program_to_renew_id:
            programme = instance.program_to_renew
            response['renewed_programme'] = {
                'id': programme.pk,
                'programme_name': programme.programme_name,
                'accreditation_date': instance.previous_accreditation_date.isoformat() if instance.previous_accreditation_date else None,
                'expiry_date': instance.previous_expiry_date.isoformat() if instance.previous_expiry_date else None,
            }
        return response
    

class ProgramSerializer(serializers.ModelSerializer):
    '''Programs'''
    can_renew = serializers.SerializerMethodField()

    class Meta:
        model = Program
        fields = ('id','applications','institution','programme_name','program_level', 'accreditation_date','expiry_date','status','can_renew')

    def get_can_renew(self, instance):
        request = self.context.get('request')
        institution = getattr(request.user, 'institution', None) if request else None
        return bool(institution and instance.institution_id == institution.pk
                    and instance.accreditation_date and instance.expiry_date
                    and not any(renewal.status not in ('approved', 'rejected') for renewal in instance.renewals.all()))

    def to_representation(self, instance):
        '''Custom representation to include institution name and display choices'''
        response = super().to_representation(instance)
        response['institution'] = instance.institution.name if instance.institution else None
        response['program_level'] = instance.get_program_level_display()
        response['status'] = instance.get_status_display()
        response['accreditation_date'] = instance.accreditation_date.strftime('%d-%b-%Y') if instance.accreditation_date else None
        response['expiry_date'] = instance.expiry_date.strftime('%d-%b-%Y') if instance.expiry_date else None
        return response




class AssessorAssignmentApplicationSerializer(ProgrammeAccreditationSerializer):
    tier_displine = serializers.CharField(read_only=True, allow_null=True)
    tier_displine_display = serializers.SerializerMethodField()

    class Meta(ProgrammeAccreditationSerializer.Meta):
        ref_name = 'assessor assignment application'

    def get_tier_displine_display(self, instance):
        return dict(PreliminaryReview.DISPLINE_CHOICE).get(instance.tier_displine)


class PreliminaryReviewSerializer(serializers.ModelSerializer):
    '''Preliminary Review Serializer'''
    reviewer_name = serializers.CharField(source='reviewer.get_full_name', read_only=True)
    application_number = serializers.CharField(source='application.application_number', read_only=True)
    review_date = serializers.DateTimeField(source='reviewed_at', read_only=True, format='%d-%m-%Y')

    class Meta:
        '''Serializer for Preliminary Review'''
        model = PreliminaryReview
        fields = "__all__"
        read_only_fields = ['reviewed_at','reviewer']

    def to_representation(self, instance):
        '''Custom representation to include reviewer name and application number'''
        response = super().to_representation(instance)
        response['expert_progression'] = instance.get_expert_progression_display() if instance.expert_progression else None
        response['institution'] = instance.application.institution.name if instance.application and instance.application.institution else None
        response['programme'] = instance.application.programme_name if instance.application and instance.application.programme_name else None
        response["student_total"] = instance.student_total if instance.student_total is not None else None
        response['application_status'] = instance.application.get_status_display() if instance.application and instance.application.status else None
        response['type_of_entry']  = instance.get_type_of_entry_display() if instance.type_of_entry else None
        response['institution_category'] = instance.application.institution.get_category_display() if instance.application and instance.application.institution and instance.application.institution.category else None
        return response
    

class ProgrammeAssessmentSerializer(serializers.ModelSerializer):
    '''Serializer for Programme Assessment'''
    assessor_name = serializers.CharField(source='assessor.get_full_name', read_only=True)
    application_number = serializers.CharField(source='application.application_number', read_only=True)
    assessment_date = serializers.DateField(read_only=True, format='%d %B, %Y')

    class Meta:
        '''Serializer for Programme Assessment'''
        model = ProgrammeAssessment
        fields = "__all__"
        read_only_fields = ['assessment_date','assessor']

    def to_representation(self, instance):
        '''Custom representation to include assessor name and application number'''
        response = super().to_representation(instance)
        response['recommendation'] = instance.get_recommendation_display() if instance.recommendation else None
        response['institution'] = instance.application.institution.name if instance.application and instance.application.institution else None
        response['programme'] = instance.application.programme_name if instance.application and instance.application.programme_name else None
        response['status'] = instance.application.get_status_display() if instance.application and instance.application.status else None
        response['pod_comment'] = instance.application.pod_comment if instance.application and instance.application.pod_comment else None
        return response


class ProgressedToDirectorateSerializer(serializers.ModelSerializer):
    '''Serializer for Programme Accreditation applications progressed to directorate stage'''
    preliminary_review = PreliminaryReviewSerializer(read_only=True, source='preliminary_reviewers.first')
    assessment = ProgrammeAssessmentSerializer(read_only=True, source='programme_assessments.first')
    class Meta:
        model = ProgramAccreditation
        fields = '__all__'
        read_only_fields = ['application_number', 'date_submitted', 'status']

    def to_representation(self, instance):
        '''Custom representation to include institution name and display choices'''
        response = super().to_representation(instance)
        response['institution'] = instance.institution.name if instance.institution else None
        response['application_type'] = instance.get_application_type_display()
        response['program_level'] = instance.get_program_level_display()
        response['status'] = instance.get_status_display()
        latest_invoice = instance.programme_invoices.order_by('-invoice_date', '-id').first()
        response['invoice_status'] = latest_invoice.get_status_display() if latest_invoice else None
        response['date_submitted'] = instance.date_submitted.strftime('%d-%m-%Y') if instance.date_submitted else None
        request = self.context.get('request')
        response['program_structure'] = request.build_absolute_uri(instance.program_structure.url) if instance.program_structure and request else (instance.program_structure.url if instance.program_structure else None)
        response['letter_of_submission'] = request.build_absolute_uri(instance.letter_of_submission.url) if instance.letter_of_submission and request else (instance.letter_of_submission.url if instance.letter_of_submission else None)
        return response
    
class InvoiceItemTypeSerializer(serializers.ModelSerializer):
    '''Serializer for Invoice Item Type'''
    class Meta:
        model = InvoiceItemType
        fields = '__all__'


class InvoiceItemSerializer(serializers.ModelSerializer):
    '''Serializer for Invoice Item'''
    item_type = InvoiceItemTypeSerializer(read_only=True)
    class Meta:
        model = InvoiceItem
        fields = ('id', 'invoice', 'item_type', 'persons_number', 'number_of_days', 'total')

    
    def to_representation(self, instance):
        '''Custom representation to include item type name'''
        response = super().to_representation(instance)
        response['item_type'] = instance.item_type.name if instance.item_type else None
        return response

# invoicing serializer
class ProgrammeInvoiceSerializer(serializers.ModelSerializer):
    '''Serializer for invoicing Programme Accreditation applications'''
    invoice_items = InvoiceItemSerializer(many=True, read_only=True)
    class Meta:
        model = ProgrammeInvoice
        fields = ('id','application','status','invoice_number','invoice_date','grand_total','payment_date','cleared','invoice_items','payment_reference','payment_receipt')
        extra_kwargs = {
            'invoice_number': {'required': False, 'allow_blank': True},
            'grand_total': {'required': False},
        }

    def _parse_invoice_items(self):
        """Accept invoice items from JSON string or list and normalize payload."""
        raw_items = self.initial_data.get('invoice_items', [])

        if isinstance(raw_items, str):
            try:
                raw_items = json.loads(raw_items)
            except json.JSONDecodeError:
                raw_items = []

        if isinstance(raw_items, dict):
            raw_items = [raw_items]

        if not isinstance(raw_items, list):
            return []

        normalized = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue

            item_type = item.get('item_type')
            if isinstance(item_type, dict):
                item_type = item_type.get('id')

            normalized.append({
                'item_type_id': item_type,
                'persons_number': int(item.get('persons_number') or 1),
                'number_of_days': int(item.get('number_of_days') or 1),
                'rate': item.get('rate') or 0,
            })

        return normalized
    
    def save(self, **kwargs):
        '''Override save to handle nested invoice items'''
        invoice_items_data = self._parse_invoice_items()
        invoice = super().save(**kwargs)

        for item_data in invoice_items_data:
            InvoiceItem.objects.create(invoice=invoice, **item_data)

        invoice.recalculate_grand_total(commit=True)
        return invoice
    def to_representation(self, instance):
        '''Custom representation to include institution name and display choices'''
        response = super().to_representation(instance)
        response['application_id'] = instance.application.id if instance.application else None
        response['application'] = instance.application.application_number if instance.application else None
        response['status'] = instance.get_status_display() if instance.status else None
        response['invoice_date'] = instance.invoice_date.strftime('%d-%m-%Y') if instance.invoice_date else None
        response['invoice_items'] = InvoiceItemSerializer(instance.items.all(), many=True).data
        response['institution'] = instance.application.institution.name if instance.application and instance.application.institution else None
        return response


class DeskReviewInvoiceLineSerializer(serializers.ModelSerializer):
    application = serializers.PrimaryKeyRelatedField(queryset=ProgramAccreditation.objects.all())
    desk_review_fee = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'), max_value=Decimal('90909090.90'))

    class Meta:
        model = DeskReviewInvoiceLine
        fields = ('application', 'application_number', 'programme_name', 'desk_review_fee')
        read_only_fields = ('application_number', 'programme_name')


class ProgrammeAssessmentInvoiceSerializer(serializers.ModelSerializer):
    '''Serializer for invoicing Programme Assessments'''
    can_manage = serializers.SerializerMethodField()
    can_send = serializers.SerializerMethodField()
    institution_id = serializers.PrimaryKeyRelatedField(source='institution', queryset=Institution.objects.all())
    institution = serializers.CharField(source='institution.name', read_only=True)
    lines = DeskReviewInvoiceLineSerializer(many=True, allow_empty=False)
    outstanding_balance = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    verifications = serializers.SerializerMethodField()

    def get_verifications(self, instance):
        return [{
            'verified_total': str(item.verified_total),
            'verified_by': ' '.join(filter(None, [item.verified_by.first_name, item.verified_by.last_name])) or item.verified_by.username,
            'verified_at': item.verified_at.isoformat(),
            'payment_reference': item.payment_reference,
            'payment_receipt': self.context['request'].build_absolute_uri(item.payment_receipt.url) if item.payment_receipt and self.context.get('request') else None,
        } for item in instance.verifications.select_related('verified_by').all()]

    def get_can_send(self, instance):
        from .invoice_permissions import can_create_review_invoices
        request = self.context.get('request')
        return can_create_review_invoices(request.user if request else None)

    def get_can_manage(self, instance):
        from .invoice_permissions import can_manage_review_invoices
        request = self.context.get('request')
        return can_manage_review_invoices(request.user if request else None)

    class Meta:
        model = ProgrammeAssessmentInvoice
        fields = ('id','institution_id','institution','lines','status','invoice_number','desk_review_fee','administrative_fee','invoice_date','grand_total','payment_date','cleared','payment_reference','payment_receipt','can_manage','can_send','verified_amount','outstanding_balance','verifications')
        read_only_fields = ('status', 'invoice_number', 'desk_review_fee', 'administrative_fee', 'invoice_date', 'grand_total', 'payment_date', 'cleared', 'payment_reference', 'payment_receipt', 'verified_amount')

    def validate(self, attrs):
        forbidden = set(self.initial_data) - {'institution_id', 'lines'}
        if forbidden:
            raise serializers.ValidationError('Only the institution and programme lines can be edited. Use invoice actions for payment details.')
        institution = attrs.get('institution', getattr(self.instance, 'institution', None))
        if self.instance and institution != self.instance.institution:
            raise serializers.ValidationError({'institution_id': 'An invoice cannot be moved to another institution.'})
        if 'lines' in attrs:
            ids = [line['application'].pk for line in attrs['lines']]
            if len(ids) != len(set(ids)):
                raise serializers.ValidationError({'lines': 'Select each programme only once.'})
            if any(line['application'].institution_id != institution.pk for line in attrs['lines']):
                raise serializers.ValidationError({'lines': 'All programmes must belong to the selected institution.'})
            total = sum(line['desk_review_fee'] for line in attrs['lines'])
            if total > Decimal('90909090.90'):
                raise serializers.ValidationError({'lines': 'The combined desk review fee exceeds the invoice amount limit.'})
        return attrs

    def _save_lines(self, invoice, lines):
        invoice.lines.all().delete()
        DeskReviewInvoiceLine.objects.bulk_create([
            DeskReviewInvoiceLine(invoice=invoice, application=line['application'],
                application_number=line['application'].application_number,
                programme_name=line['application'].programme_name, desk_review_fee=line['desk_review_fee'])
            for line in lines
        ])

    def create(self, validated_data):
        lines = validated_data.pop('lines')
        invoice = ProgrammeAssessmentInvoice.objects.create(**validated_data,
            desk_review_fee=sum(line['desk_review_fee'] for line in lines))
        self._save_lines(invoice, lines)
        return invoice

    def update(self, instance, validated_data):
        lines = validated_data.pop('lines', None)
        if lines is not None:
            self._save_lines(instance, lines)
            instance.desk_review_fee = sum(line['desk_review_fee'] for line in lines)
        instance.save()
        return instance

    def to_representation(self, instance):
        '''Custom representation to include institution name and display choices'''
        response = super().to_representation(instance)
        response['status'] = instance.get_status_display() if instance.status else None
        response['invoice_date'] = instance.invoice_date.strftime('%d-%m-%Y') if instance.invoice_date else None
        response['application'] = ', '.join(line.application_number for line in instance.lines.all())
        response['programme_count'] = instance.lines.count()
        from .review_invoice_pdf import payment_details, amount_in_words
        response['payment_instructions'] = payment_details()
        response['amount_in_words'] = amount_in_words(instance.grand_total)
        response['institution_address'] = instance.institution.postal_address or ''
        return response


class ReviewInvoiceVerificationSerializer(serializers.Serializer):
    verified_amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))


class ReviewInvoicePaymentSerializer(serializers.Serializer):
    payment_reference = serializers.CharField(max_length=255, trim_whitespace=True)
    payment_receipt = serializers.FileField()
    payment_date = serializers.DateField()

    def validate_payment_date(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError('Payment date cannot be in the future.')
        return value

    def validate_payment_receipt(self, value):
        if value.size > 2 * 1024 * 1024:
            raise serializers.ValidationError('Receipt must be no larger than 2 MB.')
        if Path(value.name).suffix.lower() not in {'.pdf', '.jpg', '.jpeg', '.png'}:
            raise serializers.ValidationError('Upload a PDF, JPG or PNG receipt.')
        signature = value.read(8)
        value.seek(0)
        expected = {'.pdf': b'%PDF-', '.jpg': b'\xff\xd8\xff', '.jpeg': b'\xff\xd8\xff', '.png': b'\x89PNG\r\n\x1a\n'}
        if not signature.startswith(expected[Path(value.name).suffix.lower()]):
            raise serializers.ValidationError('The receipt contents do not match its file type.')
        return value
