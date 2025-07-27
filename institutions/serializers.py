from rest_framework import serializers

from .models import Institution


class InstitutionSerializer(serializers.ModelSerializer):
    '''Serializer for Institution model.'''
    
    class Meta:
        '''Meta class for Institution Serializer'''
        model = Institution
        fields = [
            'id', 'user', 'name', 'district', 'institution_type',
            'landline', 'contact_person', 'contact_person_phone',
            'alternative_contact_person', 'alternative_contact_person_phone',
            'logo'
        ]
        read_only_fields = ['id', 'user']