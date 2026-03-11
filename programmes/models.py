from accounts.models import User
from common.choices import PROGRAMME_LEVELS
from django.db import models
from institutions.models import Institution
from tinymce.models import HTMLField


# Create your models here.
class ProgramAccreditation(models.Model):
    '''Model to represent a programme accreditation application.'''
    STATUS = [
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    APPLICATION_TYPE=[
        ('new', 'New'),
        ('renewal', 'Renewal'),

    ]
    institution = models.ForeignKey(Institution, on_delete=models.RESTRICT, related_name='programme_accreditations', blank=True)
    #  PGAC/2024-2025/00715
    application_number = models.CharField(max_length=100, unique=True, blank=True)
    application_type = models.CharField(max_length=100, choices=APPLICATION_TYPE, default='new')
    program_level = models.CharField(max_length=100, choices=PROGRAMME_LEVELS)
    program_name = models.CharField(max_length=255)
    duration_semester = models.PositiveIntegerField()
    campus = models.CharField(max_length=255, blank=True, null=True)
    date_submitted = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=STATUS, default='submitted', blank=True)
    #Attach detailed Programme(Course) Structure 
    program_structure = models.FileField(upload_to='programmes/', blank=True, null=True)
    letter_of_submission = models.FileField(upload_to='programmes/', blank=True, null=True)
    # program to renew 
    program_to_renew = models.ForeignKey('programmes.Program', on_delete=models.SET_NULL, null=True, blank=True, related_name='renewals')
    preliminary_reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='preliminary_reviews')

    class Meta:
        ordering = ['-date_submitted']
        verbose_name = 'Programme Accreditation Application'
        verbose_name_plural = 'Programme Accreditation Applications'
        permissions = [
            ('can_assign_reviewers', 'Can assign reviewers to applications'),
            ('can_assign_accessors', 'Can assign Accessors to applications'),
            ('can_review_programme_accreditation', 'Can review programme accreditation applications'),
            ('can_access_programme',' Can Access Programmes')
        ]

    def __str__(self):
        return self.application_number
    
    def save(self, *args, **kwargs):
        if not self.application_number:
            last_id = ProgramAccreditation.objects.all().order_by('id').last()
            if last_id:
                new_id = last_id.id + 1
            else:
                new_id = 1
            self.application_number = f"PGAC/{self.get_academic_year()}/{str(new_id).zfill(4)}"
        super().save(*args, **kwargs)

    def get_academic_year(self):
        from datetime import datetime
        now = datetime.now()
        year = now.year
        month = now.month
        if month >= 8:  # Assuming academic year starts in August
            return f"{year}-{year + 1}"
        else:
            return f"{year - 1}-{year}"
        
# assign accessors to a programme accreditation application
class ProgramAccessor(models.Model):
    '''Programme accreditation accessors'''
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='programme_accessors')
    program_accreditation = models.ForeignKey(ProgramAccreditation, on_delete=models.CASCADE, related_name='accessors')
    group_leader = models.BooleanField(default=False)
    assigned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.program_accreditation.application_number} - {'Leader' if self.group_leader else 'Accessor'}"



class Program(models.Model):
    '''Model to represent individual programs under an accreditation.'''
    STATUS = (
      ('active','Active'),
      ('under_review','Under Review'),
      ('expired','Expired')
    )
    applications = models.ManyToManyField(ProgramAccreditation, related_name='programs')
    program_name = models.CharField(max_length=50)
    program_level = models.CharField(max_length=255, blank=True, null=True, choices=PROGRAMME_LEVELS)
    accreditation_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=15, null=False, blank=True,default='under_review')

    def __str__(self):
        return f"{self.program_name} - {self.program_level}"


class PreliminaryReview(models.Model):
    '''Model to represent preliminary review for programme accreditation applications.'''
    YES_NO_CHOICES = (
        (True, 'Yes'),
        (False, 'No'),
    )
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='preliminary_reviewers')
    application = models.ForeignKey(ProgramAccreditation, on_delete=models.CASCADE, related_name='preliminary_reviewers')
    type_of_entry_summary = HTMLField(blank=False, null=True)
    type_of_entry_comments = models.TextField(blank=True, null=True)
    entry_requirements_summary = HTMLField(blank=False, null=True)
    entry_requirements_comments = models.TextField(blank=True, null=True)
    human_resource_summary = HTMLField(blank=False, null=True)
    human_resource_comments = models.TextField(blank=True, null=True)
    facilities_summary = HTMLField(blank=False, null=True)
    facilities_comments = models.TextField(blank=True, null=True)
    programme_duration_summary = HTMLField(blank=False, null=True)
    programme_duration_comments = models.TextField(blank=True, null=True)
    minimum_graduation_load_summary = HTMLField(blank=False, null=True)
    minimum_graduation_load_comments = models.TextField(blank=True, null=True)
    day_students = models.PositiveIntegerField(blank=True, null=True)
    evening_students = models.PositiveIntegerField(blank=True, null=True)
    weekend_students = models.PositiveIntegerField(blank=True, null=True)
    student_comment = models.TextField(blank=True, null=True)
    expert_progression = models.BooleanField(default=False, choices=YES_NO_CHOICES)
    reviewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reviewer.first_name} {self.reviewer.last_name} - {self.application.application_number} - Preliminary Reviewer"