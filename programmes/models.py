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
        ('progressed_to_experts', 'Progressed to Experts'),
        ('returned_for_review', 'Returned for Review'),
        ('under_assessment', 'Under Assessment'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    APPLICATION_TYPE=[
        ('new', 'New Programme'),
        ('renewal', 'Renewal'),
        ('revision', 'Revision'),

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
    assessor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assessments')

    class Meta:
        ordering = ['-date_submitted']
        verbose_name = 'Programme Accreditation Application'
        verbose_name_plural = 'Programme Accreditation Applications'
        permissions = [
            ('can_assign_reviewers', 'Can assign reviewers to applications'),
            ('can_assign_assessors', 'Can assign assessors to applications'),
            ('can_review_programme_accreditation', 'Can review programme accreditation applications'),
            ('can_assess_programme',' Can Assess Programmes')
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
    PROGRESSION_CHOICES = (
        ('yes', 'Yes'),
        ('no', 'No'),
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
    expert_progression = models.CharField(max_length=10, choices=PROGRESSION_CHOICES)
    reviewed_at = models.DateTimeField(auto_now_add=True)

    @property
    def student_total(self):
        '''sum number of students'''
        return self.day_students + self.evening_students + self.weekend_students

    def __str__(self):
        return f"{self.reviewer.first_name} {self.reviewer.last_name} - {self.application.application_number} - Preliminary Reviewer"
    

class ProgrammeAssessment(models.Model):
    '''Model to represent assessment details for programme accreditation applications.'''
    RECOMMENDATION_CHOICES = [
        ("accredit", "Accredit as is"),
        ("minor", "Accredit with Minor Corrections"),
        ("major", "Accredit After Major Corrections"),
        ("reject", "Don't Accredit"),
    ]
    assessor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='programme_assessors')
    application = models.ForeignKey(ProgramAccreditation, on_delete=models.CASCADE, related_name='programme_assessors')
    assessment_date = models.DateTimeField(auto_now_add=True)
    # asssessor's  comments on the programme
    programme_development_process = HTMLField(blank=False, null=True)
    rationale = HTMLField(blank=False, null=True)
    programme_objectives = HTMLField(blank=False, null=True)
    competences = HTMLField(blank=False, null=True)
    learning_outcomes = HTMLField(blank=False, null=True)
    entry_requirements = HTMLField(blank=False, null=True)
    duration = HTMLField(blank=False, null=True)
    grading_system = HTMLField(blank=False, null=True)
    curriculum_structure = HTMLField(blank=False, null=True)
    staffing_levels = HTMLField(blank=False, null=True)
    infrastructure = HTMLField(blank=False, null=True)
    cbe_allignment = HTMLField(blank=False, null=True)
    other_comments = HTMLField(blank=True, null=True)
    # course
    course_name = models.TextField(blank=False, null=True)
    course_code = models.TextField(blank=False, null=True)
    course_level = models.TextField(blank=False, null=True)
    contact_hours = models.TextField(blank=False, null=True)
    credit_units = models.TextField(blank=False, null=True)
    course_description = models.TextField(blank=False, null=True)
    course_objectives = models.TextField(blank=False, null=True)
    course_learning_outcomes = models.TextField(blank=False, null=True)
    detailed_course_content = models.TextField(blank=False, null=True)
    instructional_materials = models.TextField(blank=False, null=True)
    delivery_modes = models.TextField(blank=False, null=True)
    assessment_modes = models.TextField(blank=False, null=True)
    writing_styles_and_grammar = models.TextField(blank=False, null=True)
    minimum_standards = models.TextField(blank=False, null=True)
    # overall comments and recommendation
    institution_comments = models.TextField(blank=True, null=True)
    nche_comments = models.TextField(blank=True, null=True)
    recommendation = models.CharField(max_length=20, choices=RECOMMENDATION_CHOICES, blank=True, null=True)

    def __str__(self):
        return f"{self.assessor.first_name} {self.assessor.last_name} - {self.application.application_number} - Assessor"



