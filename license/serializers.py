from drf_extra_fields.fields import Base64FileField
from rest_framework import serializers

from .models import (CertificationAndClassification, IntrimAuthority,
                     UniversityProvisionalLicense)


class CertificationAndClassificationSerializer(serializers.ModelSerializer):
    '''Serializer for CertificationAndClassification model.'''
    class Meta:
        '''Meta class for CertificationAndClassification Serializer'''
        model = CertificationAndClassification
        fields = "__all__"
        read_only_fields = ['id']


class IntrimAuthoritySerializer(serializers.ModelSerializer):
    '''Serializer for IntrimAuthority model.'''
    class Meta:
        '''Meta class for IntrimAuthority Serializer'''
        model = IntrimAuthority
        fields = "__all__"
        read_only_fields = ['id']


    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['institution'] = instance.institution.name
        return response

class UniversityProvisionalLicenseSerializer(serializers.ModelSerializer):
    '''Serializer for UniversityProvisionalLicense model.'''

    class Meta:
        '''Meta class for UniversityProvisionalLicense Serializer'''
        model = UniversityProvisionalLicense
        fields = "__all__"
        read_only_fields = ['id', 'application_code', 'status']


    def to_representation(self, instance):
        '''Custom representation to include institution name'''
        response = super().to_representation(instance)
        response['institution'] = instance.institution.name
        return response