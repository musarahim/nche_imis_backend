from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from .models import Institution, OtherDocuments


class InstitutionSerializer(serializers.ModelSerializer):
    '''Serializer for Institution model.'''
    logo = Base64ImageField(
        max_length=None, use_url=True, required=True, allow_null=True
    )
    class Meta:
        '''Meta class for Institution Serializer'''
        model = Institution
        fields = [
            'id', 'user', 'name','acroynm','region', 'district', 'institution_type',"alternative_email",
            'landline','website','postal_address', 'contact_person', 'contact_person_phone',
            'alternative_contact_person', 'alternative_contact_person_phone','location',
            'logo','tin'
        ]
        read_only_fields = ['id', 'user']

    def to_representation(self, instance):
        '''Override to_representation method for proper representation of data'''
        representation = super().to_representation(instance)
        representation['district'] = instance.district.name
        representation['region'] = instance.region.name if instance.region else None
        representation['institution_type'] = instance.get_institution_type_display()
        representation['phone'] = instance.user.phone.raw_input if instance.user else ''
        return representation



class OtherDocumentsSerializer(serializers.ModelSerializer):
    '''Serializer for OtherDocuments model.'''
    class Meta:
        '''Meta class for OtherDocuments Serializer'''
        model = OtherDocuments
        fields = ['id', 'document_name', 'document']
        read_only_fields = ['id']
