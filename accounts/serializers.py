from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from djoser.serializers import UserCreatePasswordRetypeSerializer
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
                  'account_expiry_date','phone','alternative_phone_number',
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
                  'account_expiry_date','phone','alternative_phone_number',
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
        