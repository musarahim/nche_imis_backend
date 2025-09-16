from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from .models import Institution, OtherDocuments, PublicationYear


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

    def to_representation(self, instance):
        '''Override to_representation method for proper representation of data'''
        representation = super().to_representation(instance)
        representation['district'] = instance.district.name
        return representation


class PublicationYearSerializer(serializers.ModelSerializer):
    '''Serializer for PublicationYear model.'''
    class Meta:
        '''Meta class for PublicationYear Serializer'''
        model = PublicationYear
        fields = ['id', 'year']
        read_only_fields = ['id']


class OtherDocumentsSerializer(serializers.ModelSerializer):
    '''Serializer for OtherDocuments model.'''
    class Meta:
        '''Meta class for OtherDocuments Serializer'''
        model = OtherDocuments
        fields = ['id', 'document_name', 'document']
        read_only_fields = ['id']
