from rest_framework import serializers

from .models import (Department, Dependent, Designation, Directorate,
                     EducationHistory, Employee, GradeScale, Referee,
                     WorkHistory)


class DirectorateSerializer(serializers.ModelSerializer):
    '''Serializer for Directorate model.'''
    class Meta:
        '''Meta class for Directorate Serializer'''
        model = Directorate
        fields = ("id", "short_code", "name")
        read_only_fields = ['id']

class DepartmentSerializer(serializers.ModelSerializer):
    '''Serializer for Department model.'''
    class Meta:
        '''Meta class for Department Serializer'''
        model = Department
        fields = ("id", "short_code", "name", "directorate")
        read_only_fields = ['id']

    def to_representation(self, instance):
        '''Custom representation to include directorate name'''
        response = super().to_representation(instance)
        response['directorate'] = instance.directorate.name if instance.directorate else None
        return response

class DesignationSerializer(serializers.ModelSerializer):
    '''Serializer for Designation model.'''
    class Meta:
        '''Meta class for Designation Serializer'''
        model = Designation
        fields = ("id", "code", "name")
        read_only_fields = ['id']


class GradeScaleSerializer(serializers.ModelSerializer):
    '''Serializer for GradeScale model.'''
    class Meta:
        '''Meta class for GradeScale Serializer'''
        model = GradeScale
        fields = "__all__"
        read_only_fields = ['id']

class DependentSerializer(serializers.ModelSerializer):
    '''Serializer for Dependent model.'''
    class Meta:
        '''Meta class for Dependent Serializer'''
        model = Dependent
        fields = ("id", "employee", "name", "relationship", "date_of_birth","gender")
        read_only_fields = ['id']

    def to_representation(self, instance):
        '''Custom representation to include employee name'''
        response = super().to_representation(instance)
        response['employee'] = instance.employee.full_name if instance.employee else None
        response['gender'] = instance.get_gender_display() if instance.gender else None
        return response

class EducationHistorySerializer(serializers.ModelSerializer):
    '''Serializer for EducationHistory model.'''
    class Meta:
        '''Meta class for EducationHistory Serializer'''
        model = EducationHistory
        fields = ("id","institution", "qualification", "from_year", "to_year", "award_date",'certificate_document', "employee")
        read_only_fields = ['id']

    def to_representation(self, instance):
        '''Custom representation to include employee name'''
        response = super().to_representation(instance)
        response['employee'] = instance.employee.full_name if instance.employee else None
        return response

class WorkHistorySerializer(serializers.ModelSerializer):
    '''Serializer for WorkHistory model.'''
    class Meta:
        '''Meta class for WorkHistory Serializer'''
        model = WorkHistory
        fields = ("id","employer", "position", "from_date", "to_date", "responsibilities", "employee")
        read_only_fields = ['id']

    def to_representation(self, instance):
        '''Custom representation to include employee name'''
        response = super().to_representation(instance)
        response['employee'] = instance.employee.full_name if instance.employee else None
        return response

class RefereeSerializer(serializers.ModelSerializer):
    '''Serializer for Referee model.'''
    class Meta:
        '''Meta class for Referee Serializer'''
        model = Referee
        fields = ("id","name", "place_of_work", "position", "telephone", "email", "employee")
        read_only_fields = ['id']

    def to_representation(self, instance):
        '''Custom representation to include employee name'''
        response = super().to_representation(instance)
        response['employee'] = instance.employee.full_name if instance.employee else None
        return response

class EmployeeSerializer(serializers.ModelSerializer):
    '''Serializer for Employee model.'''
    class Meta:
        '''Meta class for Employee Serializer'''
        model = Employee
        #fields = "__all__"
        exclude = ['created', 'modified','deleted_at']
        read_only_fields = ['id']

    def to_representation(self, instance):
        '''Custom representation to include related fields'''
        response = super().to_representation(instance)
        response['gender'] = instance.get_gender_display() if instance.gender else None
        response['marital_status'] = instance.get_marital_status_display() if instance.marital_status else None
        response["father_status"] = instance.get_father_status_display() if instance.father_status else None
        response["mother_status"] = instance.get_mother_status_display() if instance.mother_status else None
        response['system_account'] = instance.system_account.username if instance.system_account else None
        response['department'] = instance.department.name if instance.department else None
        response['directorate'] = instance.department.directorate.name if instance.department and instance.department.directorate else None
        response['designation'] = instance.designation.name if instance.designation else None
        response['title'] = instance.title.name if instance.title else None
        response['nationality'] = instance.nationality.name if instance.nationality else None
        response['religion'] = instance.religion.name if instance.religion else None
        response['tribe'] = instance.tribe.name if instance.tribe else None
        response['district'] = instance.district.name if instance.district else None
        response['county'] = instance.county.name if instance.county else None
        response['sub_county'] = instance.sub_county.name if instance.sub_county else None
        response['parish'] = instance.parish.name if instance.parish else None
        response['village'] = instance.village.name if instance.village else None
        response['district_of_origin'] = instance.district_of_origin.name if instance.district_of_origin else None
        response['county_of_origin'] = instance.county_of_origin.name if instance.county_of_origin else None
        response['sub_county_of_origin'] = instance.sub_county_of_origin.name if instance.sub_county_of_origin else None
        response['parish_of_origin'] = instance.parish_of_origin.name if instance.parish_of_origin else None
        response['village_of_origin'] = instance.village_of_origin.name if instance.village_of_origin else None
        response['supervisor'] = instance.supervisor.full_name if instance.supervisor else None
        response['education_histories'] = EducationHistorySerializer(instance.educationhistory_set.all(), many=True).data
        response['work_histories'] = WorkHistorySerializer(instance.workhistory_set.all(), many=True).data
        response['referees'] = RefereeSerializer(instance.referee_set.all(), many=True).data
        response['dependents'] = DependentSerializer(instance.dependent_set.all(), many=True).data
        return response