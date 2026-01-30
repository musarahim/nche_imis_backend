from drf_extra_fields.fields import Base64FileField
from rest_framework import serializers

from .models import (CertificationAndClassification, CharterApplication,
                     InterimDiscussion, IntrimAuthority, OTIProvisional,
                     OTIProvisionalAward, UniversityProvisionalLicense)


class CertificationAndClassificationSerializer(serializers.ModelSerializer):
    '''Serializer for CertificationAndClassification model.'''
    class Meta:
        '''Meta class for CertificationAndClassification Serializer'''
        model = CertificationAndClassification
        fields = "__all__"
        read_only_fields = ['id']

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['institution'] = instance.institution.name
        return response


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
    
class InterimDiscussionSerializer(serializers.ModelSerializer):
    '''Serializer for InterimDiscussion model.'''
    class Meta:
        '''Meta class for InterimDiscussion Serializer'''
        model = InterimDiscussion
        fields = "__all__"
        read_only_fields = ['id', 'created_at', 'updated_at']


    def to_representation(self, instance):
        '''Custom representation to include institution name'''
        response = super().to_representation(instance)
        response['applicant_name'] = instance.application.institution.name
        response['reviewer_name'] = instance.reviewer.get_full_name() if instance.reviewer else None

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

        #response['publication_years'] = ', '.join(instance.publication_years) if instance.publication_years else ''
        return response
    

class CharterApplicationSerializer(serializers.ModelSerializer):
    '''Serializer for CharterApplication model.'''

    class Meta:
        '''Meta class for CharterApplication Serializer'''
        model = CharterApplication
        fields = "__all__"
        read_only_fields = ['id', 'application_code', 'status']


    def to_representation(self, instance):
        '''Custom representation to include institution name'''
        response = super().to_representation(instance)
        response['institution'] = instance.institution.name
        return response
    

    
class OTIProvisionalSerializer(serializers.ModelSerializer):
    '''Serializer for OTIProvisional model.'''

    class Meta:
        '''Meta class for OTIProvisional Serializer'''
        model = OTIProvisional
        fields = "__all__"
        read_only_fields = ['id', 'application_code', 'status']


    def to_representation(self, instance):
        '''Custom representation to include institution name'''
        response = super().to_representation(instance)
        response['institute'] = instance.institute.name
        return response
    
class OTIProvisionalAwardSerializer(serializers.ModelSerializer):
    '''Serializer for OTIProvisionalAward model.'''

    class Meta:
        '''Meta class for OTIProvisionalAward Serializer'''
        model = OTIProvisionalAward
        fields = "__all__"
        read_only_fields = ['id']


    def to_representation(self, instance):
        '''Custom representation to include institution name'''
        response = super().to_representation(instance)
        response['institution'] = instance.institution.name
        return response