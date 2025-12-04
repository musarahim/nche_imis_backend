from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from unfold.admin import ModelAdmin

from .models import LeaveApplication, LeaveBalance, LeaveType


# Register your models here.
@admin.register(LeaveType)
class LeaveTypeAdmin(SimpleHistoryAdmin,ModelAdmin):
    '''Admin interface for LeaveType model.'''
    list_display = ('code', 'name', 'max_days', 'exclude_weekends', 'gender_restriction', 'created', 'modified')
    fields = ('code', 'name', 'max_days', 'exclude_weekends', 'gender_restriction','is_paid')
    search_fields = ('code', 'name')
    ordering = ('name',)
    readonly_fields = ('created', 'modified','deleted_at')
    list_per_page = 10

@admin.register(LeaveBalance)
class LeaveBalanceAdmin(SimpleHistoryAdmin,ModelAdmin):
    '''Admin interface for LeaveBalance model.'''
    list_display = ('employee', 'leave_type', 'annual_entitlement', 'carried_forward_days', 'days_used', 'year', 'total_available', 'created', 'modified')
    fields = ('employee', 'leave_type', 'annual_entitlement', 'carried_forward_days', 'days_used', 'year')
    search_fields = ('employee__system_account__first_name', 'employee__system_account__last_name', 'leave_type__name')
    ordering = ('employee__system_account__last_name', 'leave_type__name')
    filter_fields = ('year', 'leave_type')
    readonly_fields = ('created', 'modified','deleted_at')
    list_per_page = 10


@admin.register(LeaveApplication)
class LeaveApplicationAdmin(SimpleHistoryAdmin,ModelAdmin):
    '''Admin interface for LeaveApplication model.'''
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'status', 'created', 'modified')
    fields = (
        'employee', 'leave_type', 'delegated_to', 'start_date', 'end_date', 'reason',
        'supervisor', 'supervisor_approval', 'supervisor_comments', 'approval_date',
        'hr_approval', 'hr_comments', 'hr_approval_date',
        'ed_approval', 'ed_comments', 'ed_approval_date'
    )
    search_fields = ('employee__first_name', 'employee__last_name', 'leave_type__name')
    ordering = ('-created',)
    filter_fields = ('leave_type', 'supervisor_approval', 'hr_approval', 'ed_approval')
    readonly_fields = ('created', 'modified','deleted_at')
    list_per_page = 10