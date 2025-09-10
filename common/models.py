from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords

# Create your models here.

class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    'created' and 'modified' fields.
    """
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True, editable=False)
    history = HistoricalRecords()
    class Meta:
        abstract = True
        ordering = ['-created']
    
    def delete(self):
        """
        Soft delete the model instance by setting is_active to False.
        """
        self.deleted_at = timezone.now()
        self.save()
    
    def hard_delete(self):
        """
        Hard delete the model instance.
        """
        super().delete()
    
class District(TimeStampedModel):
    '''District model to represent a district in the system.'''
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=100, unique=True)
    history = HistoricalRecords()
    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Districts"
        ordering = ['name']




class EducationLevel(TimeStampedModel):
    '''Educational Level'''
    name = models.CharField(max_length=50, null=False, blank=False)

    def __str__(self):
        return self.name
    
class Title(TimeStampedModel):
    '''Title'''
    name = models.CharField(max_length=50, null=False, blank=False)

    def __str__(self):
        return self.name
    
class Religion(TimeStampedModel):
    '''Religion'''
    name = models.CharField(max_length=50, null=False, blank=False)

    def __str__(self):
        return self.name