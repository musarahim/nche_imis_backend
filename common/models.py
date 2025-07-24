from django.db import models
from django.utils import timezone

# Create your models here.

class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    'created' and 'modified' fields.
    """
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
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

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Districts"
        ordering = ['name']
