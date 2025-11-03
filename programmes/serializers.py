from rest_framework import serializers

from .models import ProgrammeAccreditation


class ProgrammeAccreditationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgrammeAccreditation
        fields = '__all__'
        read_only_fields = ['application_number', 'date_submitted', 'status']

    def to_representation(self, instance):
        '''Custom representation to include institution name and display choices'''
        response = super().to_representation(instance)
        response['institution'] = instance.institution.name if instance.institution else None
        response['application_type'] = instance.get_application_type_display()
        response['programme_level'] = instance.get_programme_level_display()
        response['status'] = instance.get_status_display()
        response['date_submitted'] = instance.date_submitted.strftime('%d-%m-%Y') if instance.date_submitted else None
        return response



        