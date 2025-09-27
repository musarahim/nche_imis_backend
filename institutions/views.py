from django.shortcuts import render
from rest_framework import permissions, viewsets

from .models import Institution, OtherDocuments, PublicationYear
from .serializers import (InstitutionSerializer, OtherDocumentsSerializer,
                          PublicationYearSerializer)


# Create your views here.
class InstitutionViewSet(viewsets.ModelViewSet):
    '''Institution viewset'''
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['name',"institution_type"]

    def get_queryset(self):
        '''Return only active institutions'''
        queryset = Institution.objects.all().order_by('name')
        if self.request.user.is_superuser or self.request.user.groups.filter(name='System Administrator').exists():
            data = queryset
            
        else:
            data = queryset.filter(user=self.request.user)
        return data
        

class PublicationYearViewSet(viewsets.ModelViewSet):
    '''publication year'''
    queryset = PublicationYear.objects.all()
    serializer_class = PublicationYearSerializer
    permissions_classes = [permissions.IsAuthenticated]
    pagination_class = None

class OtherDocumentsViewset(viewsets.ModelViewSet):
    '''Institution other documents'''
    queryset = OtherDocuments.objects.all()
    serializer_class = OtherDocumentsSerializer
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
    


