from django.shortcuts import render
from rest_framework import permissions, viewsets

from .models import (CertificationAndClassification, Institution,
                     PublicationYear)
from .serializers import CertificationAndClassificationSerializer


# Create your views here.
class CertificationAndClassificationViewset(viewsets.ModelViewSet):
    '''Institution certification and classification'''
    queryset = CertificationAndClassification.objects.all()
    serializer_class = CertificationAndClassificationSerializer
    permissions_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        '''return documents for the logged in institution'''
        queryset = self.queryset
        if self.request.user.is_superuser or self.request.user.groups.filter(name='System Administrator').exists():
            data = queryset
        else:
            if hasattr(self.request.user, 'institution'):
                data = queryset.filter(institution=self.request.user.institution)
            else:
                data = None
        return data