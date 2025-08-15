from rest_framework import serializers

from .models import District


class DistrictSerializer(serializers.ModelSerializer):
    '''Serializer for District model.'''
    class Meta:
        '''Meta class for District Serializer'''
        model = District
        fields = ['id', 'name', 'code']
        read_only_fields = ['name', 'code']
        