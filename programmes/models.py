from common.choices import PROGRAMME_LEVELS
from django.db import models
from institutions.models import Institution


# Create your models here.
class ProgramAccreditation(models.Model):
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