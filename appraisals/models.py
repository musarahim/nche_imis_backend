from common.models import TimeStampedModel
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from hr.models import Employee

# Create your models here.

class PerformanceAppraisal(TimeStampedModel):
    """Main appraisal record"""
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('self_assessment', 'Self Assessment Submitted'),
        ('appraiser_review', 'Under Appraiser Review'),
        ('reviewer_review', 'Under Reviewer Review'),
        ('director_review', 'Under Director Review'),
        ('executive_review', 'Under Executive Review'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    )
    start_date = models.DateField()
    end_date = models.DateField()
    appraisee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='appraisals_as_appraisee')
    appraiser = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='appraisals_as_appraiser')
    reviewer = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews_as_reviewer')
    director = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews_as_director')
    executive_director = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews_as_executive')

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')
    date_submitted = models.DateTimeField(null=True, blank=True)

    # Section B - Overall scores
    output_total_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    output_average = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    output_weighted_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # out of 70

    # Section C
    competency_total_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    competency_average = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    competency_weighted_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # out of 30

    overall_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Final 1-5 scale
    overall_level = models.CharField(max_length=20, blank=True)  # Excellent, Very Good, etc.

    # Text fields
    additional_tasks = models.TextField(blank=True)  # Section B.c
    skills_needed = models.TextField(blank=True)     # Section B.d
    challenges = models.TextField(blank=True)        # Section B.e

    supervisor_remarks = models.TextField(blank=True)



    class Meta:
        unique_together = ('start_date', 'end_date', 'appraisee')
        ordering = ['-created']

    def __str__(self):
        return f"{self.appraisee} - {self.period}"


class AppraisalOutput(models.Model):
    """Agreed outputs (max 10 per appraisal)"""
    appraisal = models.ForeignKey(PerformanceAppraisal, on_delete=models.CASCADE, related_name='outputs')

    output = models.TextField()
    performance_indicator = models.TextField()
    performance_target = models.TextField()

    self_score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    appraiser_score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    agreed_score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)

    comments = models.TextField(blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"Output for {self.appraisal.appraisee}"


class CompetencyRating(models.Model):
    """Ratings for the 10 competencies"""
    appraisal = models.ForeignKey(PerformanceAppraisal, on_delete=models.CASCADE, related_name='competencies')

    COMPETENCY_CHOICES = [
        (1, 'Technical/Job Knowledge'),
        (2, 'Financial Management'),
        (3, 'Creativity, Personal Drive and Initiative'),
        (4, 'Customer Relations'),
        (5, 'Leadership and Motivational Ability'),
        (6, 'Team Work'),
        (7, 'Attendance and Punctuality'),
        (8, 'Communication'),
        (9, 'Integrity/Honesty'),
        (10, 'Confidentiality'),
    ]

    competency_number = models.IntegerField(choices=COMPETENCY_CHOICES)
    score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])

    class Meta:
        unique_together = ('appraisal', 'competency_number')
        ordering = ['competency_number']


# performance improvement plan

class ImprovementArea(models.Model):
    """Areas of Improvement"""
    appraisal = models.ForeignKey(PerformanceAppraisal, on_delete=models.CASCADE, related_name='improvement_areas')

    performance_gap = models.TextField()
    agreed_action = models.TextField()
    time_frame = models.CharField(max_length=200)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"Improvement Area for {self.appraisal.appraisee}"

# performance improvement plan
class NextYearPerformancePlan(models.Model):
    """Performance Plan for Next Financial Year"""
    appraisal = models.ForeignKey(PerformanceAppraisal, on_delete=models.CASCADE, related_name='next_year_plans')

    key_output = models.TextField()
    performance_indicator = models.TextField()
    target = models.TextField()

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"Next Year Performance Plan for {self.appraisal.appraisee}"


# Qualifications gained 
class InitialQualification(models.Model):
    """SECTION A.2 - All qualifications before the review period"""
    appraisal = models.ForeignKey(PerformanceAppraisal, on_delete=models.CASCADE, related_name='initial_qualifications')
    
    date_period = models.CharField(max_length=100, blank=True)
    institution = models.CharField(max_length=300)
    qualification_attained = models.CharField(max_length=300)

    class Meta:
        ordering = ['date_period']


class AdditionalQualification(models.Model):
    """SECTION A.3 - Additional qualifications attained DURING the review period"""
    appraisal = models.ForeignKey(PerformanceAppraisal, on_delete=models.CASCADE, related_name='additional_qualifications')
    
    date_period = models.CharField(max_length=100, blank=True)
    institution = models.CharField(max_length=300)
    qualification_attained = models.CharField(max_length=300)

    class Meta:
        ordering = ['date_period']


# Training attended
class Training(models.Model):
    """SECTION A.4 - Additional Trainings/Seminars/Conferences"""
    appraisal = models.ForeignKey(PerformanceAppraisal, on_delete=models.CASCADE, related_name='trainings')
    
    date_period = models.CharField(max_length=100)
    organiser = models.CharField(max_length=300)
    attainment = models.CharField(max_length=500)  # e.g., "Certificate in Project Management"

    class Meta:
        ordering = ['date_period']

    def __str__(self):
        return f"{self.attainment} - {self.organiser}"

class AppraisalComment(TimeStampedModel):
    """Multi-level comments"""
    appraisal = models.ForeignKey(PerformanceAppraisal, on_delete=models.CASCADE, related_name='comments')

    COMMENTER_CHOICES = (
        ('appraisee', 'Appraisee'),
        ('appraiser', 'Appraiser'),
        ('reviewer', 'Reviewer'),
        ('director', 'Director'),
        ('executive', 'Executive Director'),
    )

    commenter = models.ForeignKey(Employee, on_delete=models.CASCADE)
    commenter_role = models.CharField(max_length=20, choices=COMMENTER_CHOICES)
    comment = models.TextField()
   

    class Meta:
        verbose_name_plural = "Appraisal Comments"

    def __str__(self):
        return f"Comment by {self.commenter} ({self.commenter_role}) on {self.appraisal}"