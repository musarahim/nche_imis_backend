from common.choices import PROGRAMME_LEVELS
from django.db import models
from institutions.models import Institution


# Create your models here.
class ProgrammeAccreditation(models.Model):
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
    programme_level = models.CharField(max_length=100, choices=PROGRAMME_LEVELS)
    programme_name = models.CharField(max_length=255)
    duration_semester = models.PositiveIntegerField()
    campus = models.CharField(max_length=255, blank=True, null=True)
    date_submitted = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=STATUS, default='submitted', blank=True)
    #Attach detailed Programme(Course) Structure 
    programme_structure = models.FileField(upload_to='programmes/', blank=True, null=True)
    letter_of_submission = models.FileField(upload_to='programmes/', blank=True, null=True)

    def __str__(self):
        return self.application_number
    
    def save(self, *args, **kwargs):
        if not self.application_number:
            last_id = ProgrammeAccreditation.objects.all().order_by('id').last()
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
