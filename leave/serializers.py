from rest_framework import serializers

from .models import LeaveApplication, LeaveBalance, LeaveEvent, LeaveType


class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = '__all__'

class LeaveBalanceSerializer(serializers.ModelSerializer):
    '''Leave Balance serializer'''
    class Meta:
        '''Leave Balance serializer meta data'''
        model = LeaveBalance
        fields = '__all__'

class LeaveApplicationSerializer(serializers.ModelSerializer):
    '''Leave Application serializer'''
    class Meta:
        '''Leave Application serializer meta data'''
        model = LeaveApplication
        fields = [
            'id', 'employee', 'leave_type', 'leave_days',
            'start_date', 'end_date', 'return_date',
            'reason', 'delegated_to', 'supervisor',
            'status',
        ]
        read_only_fields = ['status']
        