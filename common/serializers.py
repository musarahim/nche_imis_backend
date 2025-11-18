from rest_framework import serializers

from .models import (County, District, EducationLevel, FinanceYear, Holiday,
                     Nationality, Parish, Region, Religion, SubCounty, Title,
                     Tribe, Village)


class DistrictSerializer(serializers.ModelSerializer):
    '''Serializer for District model.'''
    class Meta:
        '''Meta class for District Serializer'''
        model = District
        fields = ['id','region', 'name']
        

class RegionSerializer(serializers.ModelSerializer):
    '''Serializer for Region model.'''
    class Meta:
        '''Meta class for Region Serializer'''
        model = Region
        fields = ['id', 'name', 'code']
        read_only_fields = ['name', 'code']

class NationalitySerializer(serializers.ModelSerializer):
    '''Serializer for Nationality model.'''
    class Meta:
        '''Meta class for Nationality Serializer'''
        model = Nationality
        fields = ['id', 'name']

class TribeSerializer(serializers.ModelSerializer):
    '''Serializer for Tribe model.'''
    class Meta:
        '''Meta class for Tribe Serializer'''
        model = Tribe
        fields = ['id', 'name']

class CountySerializer(serializers.ModelSerializer):
    """Counties serializers"""
    class Meta:
        '''meta class for county serializer'''
        model = County
        fields = ['id','district','name']
        
        
class SubCountySerializer(serializers.ModelSerializer):
    """Sub Counties serializers"""
    class Meta:
        '''meta class for SubCounty serializer'''
        model = SubCounty
        fields = ['id','county','name']
        
        
class ParishSerializer(serializers.ModelSerializer):
    """Parish serializer"""
    class Meta:
        '''meta class for Parish serializer'''
        model = Parish
        fields = ['id','sub_county','name']
        

class VillageSerializer(serializers.ModelSerializer):
    """Village serializers"""
    class Meta:
        '''meta class for Village serializer'''
        model = Village
        fields = ['id','parish','name']

class EducationLevelSerializer(serializers.ModelSerializer):
    """Education Level serializer"""
    class Meta:
        '''meta class for Education Level serializer'''
        model = EducationLevel
        fields = ['id','name']

class TitleSerializer(serializers.ModelSerializer):
    """Title serializer"""
    class Meta:
        '''meta class for Title serializer'''
        model = Title
        fields = ['id','name']

class ReligionSerializer(serializers.ModelSerializer):
    """Religion serializer"""
    class Meta:
        '''meta class for Religion serializer'''
        model = Religion
        fields = ['id','name']

class FinanceYearSerializer(serializers.ModelSerializer):
    """Finance Year serializer"""
    class Meta:
        '''meta class for Finance Year serializer'''
        model = FinanceYear
        fields = ['id','name']

class HolidaySerializer(serializers.ModelSerializer):
    """Holiday serializer"""
    class Meta:
        '''meta class for Holiday serializer'''
        model = Holiday
        fields = ['id','name','date']