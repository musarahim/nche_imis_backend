from rest_framework import serializers

from .models import (PreliminaryReview, Program, ProgramAccessor,
                     ProgramAccreditation)


class ProgrammeAccreditationSerializer(serializers.ModelSerializer):
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
        return response
    

class ProgramSerializer(serializers.ModelSerializer):
    '''Programs'''
    class Meta:
        model = Program
        fields = ('id','applications','program_name','program_level', 'accreditation_date','expiry_date','status')



class ProgramAccessorSerializer(serializers.ModelSerializer):
    '''Program Accessor Serializer'''
    class Meta:
        '''Serializer for Program Accessor'''
        model = ProgramAccessor
        fields = ('id', 'user', 'program_accreditation', 'group_leader', 'assigned_at')
        read_only_fields = ['assigned_at']

class PreliminaryReviewSerializer(serializers.ModelSerializer):
    '''Preliminary Review Serializer'''
    class Meta:
        '''Serializer for Preliminary Review'''
        model = PreliminaryReview
        fields = "__all__"
        read_only_fields = ['reviewed_at']