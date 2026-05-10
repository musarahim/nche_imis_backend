from rest_framework import serializers

from .models import (PreliminaryReview, Program, ProgramAccreditation,
                     ProgrammeAssessment)


class ProgrammeAccreditationSerializer(serializers.ModelSerializer):
    '''Serializer for Programme Accreditation applications'''
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
        response['date_submitted'] = instance.date_submitted.strftime('%d-%m-%Y') if instance.date_submitted else None
        request = self.context.get('request')
        response['program_structure'] = request.build_absolute_uri(instance.program_structure.url) if instance.program_structure and request else (instance.program_structure.url if instance.program_structure else None)
        response['letter_of_submission'] = request.build_absolute_uri(instance.letter_of_submission.url) if instance.letter_of_submission and request else (instance.letter_of_submission.url if instance.letter_of_submission else None)
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
        response['date_submitted'] = instance.date_submitted.strftime('%d-%m-%Y') if instance.date_submitted else None
        request = self.context.get('request')
        response['program_structure'] = request.build_absolute_uri(instance.program_structure.url) if instance.program_structure and request else (instance.program_structure.url if instance.program_structure else None)
        response['letter_of_submission'] = request.build_absolute_uri(instance.letter_of_submission.url) if instance.letter_of_submission and request else (instance.letter_of_submission.url if instance.letter_of_submission else None)
        return response
    

# invoicing serializer
class ProgrammeInvoiceSerializer(serializers.ModelSerializer):
    '''Serializer for invoicing Programme Accreditation applications'''
    class Meta:
        model = ProgramAccreditation
        fields = ('id','invoice_file','invoice_number','invoice_amount')

    # def to_representation(self, instance):
    #     '''Custom representation to include institution name and display choices'''
    #     response = super().to_representation(instance)
    #     response['institution'] = instance.institution.name if instance.institution else None
    #     response['application_type'] = instance.get_application_type_display()
    #     response['program_level'] = instance.get_program_level_display()
    #     response['status'] = instance.get_status_display()
    #     response['date_submitted'] = instance.date_submitted.strftime('%d-%m-%Y') if instance.date_submitted else None
    #     request = self.context.get('request')
    #     response['program_structure'] = request.build_absolute_uri(instance.program_structure.url) if instance.program_structure and request else (instance.program_structure.url if instance.program_structure else None)
    #     response['letter_of_submission'] = request.build_absolute_uri(instance.letter_of_submission.url) if instance.letter_of_submission and request else (instance.letter_of_submission.url if instance.letter_of_submission else None)
    #     return response