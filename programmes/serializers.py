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
        fields = ('id','applications','program_name','program_level', 'accreditation_date','expiry_date','status')




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
        return response
