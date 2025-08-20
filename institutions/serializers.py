from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from .models import Institution


class InstitutionSerializer(serializers.ModelSerializer):
    '''Serializer for Institution model.'''
    logo = Base64ImageField(
        max_length=None, use_url=True, required=True, allow_null=True
    )
    class Meta:
        '''Meta class for Institution Serializer'''
        model = Institution
        fields = [
            'id', 'user', 'name', 'district', 'institution_type',"alternative_email",
            'landline', 'contact_person', 'contact_person_phone',
            'alternative_contact_person', 'alternative_contact_person_phone',
            'logo'
        ]
        read_only_fields = ['id', 'user']