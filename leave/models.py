from common.models import TimeStampedModel
from django.db import models
from hr.models import Employee

# Create your models here.

class LeaveType(TimeStampedModel):
    '''Model representing different types of leave.'''
    
    GENDER_CHOICES = [
        ('both', 'Both Male and Female'),
        ('male', 'Male Only'),
        ('female', 'Female Only'),
    ]
    
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100, unique=True)
    max_days = models.PositiveIntegerField()
    exclude_weekends = models.BooleanField(
        default=True,
        help_text="If checked, weekends will be excluded from leave calculation (only working days counted). If unchecked, all days including weekends will be counted."
    )
    gender_restriction = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        default='both',
        help_text="Specify which gender can apply for this leave type."
    )

    def __str__(self):
        return self.name

class LeaveBalance(TimeStampedModel):
    '''Model representing leave balance for an employee.'''
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
     # Total days allocated for the current period (e.g., 21 days annual leave)
    annual_entitlement = models.FloatField(default=0)
    # Days carried forward from the previous year
    carried_forward_days = models.FloatField(default=0)
    
    # Total days consumed by approved applications
    days_used = models.FloatField(default=0)
    
    # Year this balance applies to (important for carry forward logic)
    year = models.IntegerField(default=2025) 
    @property
    def total_available(self):
        """Calculates the current available balance."""
        return self.annual_entitlement + self.carried_forward_days - self.days_used

    def __str__(self):
        return f"{self.user.username}'s {self.leave_type.name} Balance ({self.year})"

    class Meta:
        # Ensures an employee only has one balance record per leave type per year
        unique_together = ('employee', 'leave_type', 'year')
        verbose_name_plural = "Leave Balances"

    def __str__(self):
        return f"{self.employee} - {self.leave_type}: {self.balance} days remaining"


class LeaveApplication(TimeStampedModel):
    '''Model representing a leave application by an employee.'''
    APPROVE_REJECT = [
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('delegation_accepted', 'Delegation Accepted'),
        ('delegation_rejected', 'Delegation Rejected'),
        ('supervisor_approved', 'Supervisor Approved'),
        ('supervisor_rejected', 'Supervisor Rejected'),
        ('hr_approved', 'HR Approved'),
        ('hr_rejected', 'HR Rejected'),
        ('ed_approved', 'ED Approved'),
        ('ed_rejected', 'ED Rejected'),
       
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    delegated_to = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='delegated_leaves', null=True, blank=True)
    leave_days = models.PositiveIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    return_date = models.DateField()
    reason = models.TextField()
     # 3. Delegation Workflow Tracking (Crucial Step)
    delegatee = models.ForeignKey(Employee, related_name='delegated_duties', on_delete=models.SET_NULL, null=True, blank=True)
    delegation_accepted = models.BooleanField(default=False)
    delegation_acceptance_date = models.DateTimeField(null=True, blank=True)
    delegatee_remarks = models.TextField(null=True, blank=True)

    # 4. Approval Workflow Tracking
    supervisor = models.ForeignKey(Employee, related_name='leave_approvals', on_delete=models.SET_NULL, null=True, blank=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    supervisor_approval = models.CharField(max_length=10, choices=APPROVE_REJECT, null=True, blank=True)
    supervisor_comments = models.TextField(null=True, blank=True)

    # HR Approval
    hr_approval_date = models.DateTimeField(null=True, blank=True)
    hr_approval = models.CharField(max_length=10, choices=APPROVE_REJECT, null=True, blank=True)
    hr_comments = models.TextField(null=True, blank=True)

    # Ed final Approval
    ed_approval_date = models.DateTimeField(null=True, blank=True)
    ed_approval = models.CharField(max_length=10, choices=APPROVE_REJECT, null=True, blank=True)
    ed_comments = models.TextField(null=True, blank=True)
    ed_approved = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default='submitted')

    def __str__(self):
        return f"{self.employee} - {self.leave_type} from {self.start_date} to {self.end_date}"
    
