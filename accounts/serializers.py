from django.contrib.auth.models import Group, Permission
from django.utils.translation import gettext_lazy as _
from djoser.serializers import UserCreatePasswordRetypeSerializer
from institutions.models import Institution
from institutions.serializers import InstitutionSerializer
from rest_framework import serializers

from .models import User


class PermissionSerializer(serializers.ModelSerializer):
    name = serializers.CharField()

    class Meta:
        model = Permission
        fields = ['name','codename']
        ref_name='user permission'


class GroupSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    permissions = PermissionSerializer(many=True)

    class Meta:
        model = Group
        fields = ['name','permissions']
        ref_name='user group'


class UserSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(many=True)

    class Meta:
        model = User
        fields = ['username','email','first_name','last_name','other_names',
                  'account_expiry_date','phone','alternative_phone_number','profile_pic',
                  'groups','employee']
        ref_name='user'


class UserRegistrationSerializer(UserCreatePasswordRetypeSerializer):
    '''User registration serializer'''
    groups = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(), many=True, required=False
    )
    
    class Meta(UserCreatePasswordRetypeSerializer.Meta):
        '''Meta class for UserRegistrationSerializer'''
        model = User
        fields = ['username','email','first_name','last_name',
                  'account_expiry_date','phone','alternative_phone_number','profile_pic',
                    'groups','password']
        ref_name='user registration'
        extra_kwargs = {
            'password': {'write_only': True},
            'groups': {'write_only': True}
        }
        help_texts = {
            'email': _('Enter a valid email address'),
            'password': _('Password must be at least 8 characters long')

        }
        

class RegisterInstitutionSerializer(serializers.ModelSerializer):
    '''Serializer for Institution registration'''
    institution = InstitutionSerializer()

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'alternative_phone_number',
                  'institution','password']
        extra_kwargs = {
            'password': {'write_only': True},
            'institution': {'required': True}
        }
    
    def create(self, validated_data):
        institution_data = validated_data.pop('institution')
        user = User.objects.create_user(**validated_data)
        Institution.objects.create(user=user, **institution_data)
        return user
    
    def update(self, instance, validated_data):
        '''Override update method to handle nested updates'''
        institution_data = validated_data.pop('institution', None)
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update institution fields if provided
        if institution_data:
            institution = instance.institution
            for attr, value in institution_data.items():
                setattr(institution, attr, value)
            institution.save()

        return instance
    
    def partial_update(self, instance, validated_data):
        '''Override partial_update method to handle nested updates'''
        return self.update(instance, validated_data)
    
 
    