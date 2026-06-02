import json

from rest_framework import serializers

from .models import (InvoiceItem, InvoiceItemType, PreliminaryReview, Program,
                     ProgramAccreditation, ProgrammeAssessment,
                     ProgrammeInvoice)


class ProgrammeAccreditationSerializer(serializers.ModelSerializer):
    '''Serializer for Programme Accreditation applications'''
    class Meta:
        model = ProgramAccreditation
        fields = '__all__'
        read_only_fields = ['application_number', 'date_submitted']

    def to_representation(self, instance):
        '''Custom representation to include institution name and display choices'''
        response = super().to_representation(instance)
        response['institution'] = instance.institution.name if instance.institution else None
        response['application_type'] = instance.get_application_type_display()
        response['program_level'] = instance.get_program_level_display()
        response['status'] = instance.get_status_display()
        response['date_submitted'] = instance.date_submitted.strftime('%d-%m-%Y') if instance.date_submitted else None
        request = self.context.get('request')
        response['program_structure'] = request.build_absolute_uri(instance.program_structure.url) if instance.program_structure and request else (instance.program_structure.url if instance.program_structure else None)
        response['letter_of_submission'] = request.build_absolute_uri(instance.letter_of_submission.url) if instance.letter_of_submission and request else (instance.letter_of_submission.url if instance.letter_of_submission else None)
        response['review_date'] = instance.preliminary_reviewers.first().reviewed_at.strftime('%d-%m-%Y') if instance.preliminary_reviewers.first() and instance.preliminary_reviewers.first().reviewed_at else None
        response['expert_progression'] = instance.preliminary_reviewers.first().get_expert_progression_display() if instance.preliminary_reviewers.first() and instance.preliminary_reviewers.first().expert_progression else None
        response['review_id'] = instance.preliminary_reviewers.first().id if instance.preliminary_reviewers.first() else None
        return response
    

class ProgramSerializer(serializers.ModelSerializer):
    '''Programs'''
    class Meta:
        model = Program
        fields = ('id','applications','institution','program_name','program_level', 'accreditation_date','expiry_date','status')

    def to_representation(self, instance):
        '''Custom representation to include institution name and display choices'''
        response = super().to_representation(instance)
        response['institution'] = instance.institution.name if instance.institution else None
        response['program_level'] = instance.get_program_level_display()
        response['status'] = instance.get_status_display()
        response['accreditation_date'] = instance.accreditation_date.strftime('%d-%b-%Y') if instance.accreditation_date else None
        response['expiry_date'] = instance.expiry_date.strftime('%d-%b-%Y') if instance.expiry_date else None
        return response




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
        response['programme'] = instance.application.program_name if instance.application and instance.application.program_name else None
        response["student_total"] = instance.student_total if instance.student_total is not None else None
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
        response['programme'] = instance.application.program_name if instance.application and instance.application.program_name else None
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
        response['invoice_status'] = instance.get_invoice_status_display() if instance.invoice_status else None
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
        fields = ('id','application','status','invoice_number','invoice_date','grand_total','payment_date','cleared','invoice_items')
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
        response['application'] = instance.application.application_number if instance.application else None
        response['status'] = instance.get_status_display() if instance.status else None
        response['invoice_date'] = instance.invoice_date.strftime('%d-%m-%Y') if instance.invoice_date else None
        response['invoice_items'] = InvoiceItemSerializer(instance.items.all(), many=True).data
        response['institution'] = instance.application.institution.name if instance.application and instance.application.institution else None
        return response



