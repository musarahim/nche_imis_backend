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

    def to_representation(self, instance):
        '''Custom representation to include nested leave type details'''
        representation = super().to_representation(instance)
        representation['leave_type'] = instance.leave_type.name
        representation['employee'] = instance.employee.full_name
        representation['delegated_to'] = instance.delegated_to.full_name if instance.delegated_to else None
        representation['supervisor'] = instance.supervisor.full_name if instance.supervisor else None
        return representation


class LeaveScheduleSerializer(serializers.ModelSerializer):
    '''Leave Application serializer'''
    class Meta:
        '''Leave Application serializer meta data'''
        model = LeaveApplication
        fields = [
            'id', 'leave_type', 'leave_days',
            'start_date', 'end_date','status',
        ]
        read_only_fields = ['status']
        
        