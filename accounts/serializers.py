from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from djoser.serializers import UserCreatePasswordRetypeSerializer
from institutions.models import Institution
from institutions.serializers import InstitutionSerializer
from rest_framework import serializers

from .models import User


class GroupSerializer(serializers.ModelSerializer):
    name = serializers.CharField()

    class Meta:
        model = Group
        fields = ['name']
        ref_name='user group'


class UserSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(many=True)

    class Meta:
        model = User
        fields = ['username','email','first_name','last_name',
                  'account_expiry_date','phone','alternative_phone_number','profile_pic',
                  'groups']
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