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
    is_paid = models.BooleanField(default=True)

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
        # Display employee username, leave type, and year for clarity plus balance
        return f"{self.employee.system_account.username} - {self.leave_type.name} ({self.year}): {self.total_available} days available"

    class Meta:
        # Ensures an employee only has one balance record per leave type per year
        unique_together = ('employee', 'leave_type', 'year')
        verbose_name_plural = "Leave Balances"

  


class LeaveApplication(TimeStampedModel):
    '''Model representing a leave application by an employee.'''
    APPROVE_REJECT = [
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('submitted', 'Submitted'),
        ('delegation_accepted', 'Delegation Accepted'),
        ('delegation_rejected', 'Delegation Rejected'),
        ('supervisor_approved', 'Supervisor Approved'),
        ('supervisor_rejected', 'Supervisor Rejected'),
        ('hr_approved', 'HR Approved'),
        ('hr_rejected', 'HR Rejected'),
        ('director_approved', 'Director Approved'),
        ('director_rejected', 'Director Rejected'),
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    leave_days = models.PositiveIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    return_date = models.DateField(blank=True, null=True)
    reason = models.TextField(null=True, blank=True)
     # 3. Delegation Workflow Tracking (Crucial Step)
    delegated_to = models.ForeignKey(Employee, related_name='delegated_duties', on_delete=models.SET_NULL, null=True, blank=True)
    delegation_accepted = models.BooleanField(default=False)
    delegation_acceptance_date = models.DateTimeField(null=True, blank=True)
    delegatee_remarks = models.TextField(null=True, blank=True)

    # 4. Approval Workflow Tracking
    supervisor = models.ForeignKey(Employee, related_name='leave_approvals', on_delete=models.SET_NULL, null=True, blank=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    supervisor_approved = models.BooleanField(default=False)
    supervisor_comments = models.TextField(null=True, blank=True)
    # Director's Approval
    director_approval_date = models.DateTimeField(null=True, blank=True)
    director_comments = models.TextField(null=True, blank=True)
    director_approved = models.BooleanField(default=False)
    director = models.ForeignKey(Employee, related_name='director_leave_approvals', on_delete=models.SET_NULL, null=True, blank=True)

    # HR Approval
    hr_approval_date = models.DateTimeField(null=True, blank=True)
    hr_approved = models.BooleanField(default=False)
    hr_comments = models.TextField(null=True, blank=True)
    hr = models.ForeignKey(Employee, related_name='hr_leave_approvals', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, default='submitted', choices=STATUS_CHOICES)

    class Meta:
        ordering = ['-created']
        permissions = [
            ("can_approve_leave", "Can approve leave applications"),
            ("director_approve_leave", "Can approve leave applications as Director"),
            ("hr_approve_leave", "Can approve leave applications as HR"),
        ]

    def __str__(self):
        return f"{self.employee} - {self.leave_type} from {self.start_date} to {self.end_date}"
    
    
    


class LeaveEvent(TimeStampedModel):    
    '''Model representing leave approved.'''
    leave_application = models.ForeignKey(LeaveApplication, on_delete=models.CASCADE)
    start = models.DateField()
    end = models.DateField()
    leave_days = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.leave_application.leave_type.name} from {self.start} to {self.end}"
    
