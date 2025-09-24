from rest_framework import serializers

from .models import District, Region


class DistrictSerializer(serializers.ModelSerializer):
    '''Serializer for District model.'''
    class Meta:
        '''Meta class for District Serializer'''
        model = District
        fields = ['id','region', 'name', 'code']
        read_only_fields = ['name', 'code']
        
class RegionSerializer(serializers.ModelSerializer):
    '''Serializer for Region model.'''
    class Meta:
        '''Meta class for Region Serializer'''
        model = Region
        fields = ['id', 'name', 'code']
        read_only_fields = ['name', 'code']