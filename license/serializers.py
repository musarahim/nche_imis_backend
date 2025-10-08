from drf_extra_fields.fields import Base64FileField
from rest_framework import serializers

from .models import CertificationAndClassification, IntrimAuthority


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

    