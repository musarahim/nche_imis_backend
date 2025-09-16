from rest_framework import serializers

from .models import CertificationAndClassification


class CertificationAndClassificationSerializer(serializers.ModelSerializer):
    '''Serializer for CertificationAndClassification model.'''
    class Meta:
        '''Meta class for CertificationAndClassification Serializer'''
        model = CertificationAndClassification
        fields = "__all__"
        read_only_fields = ['id']