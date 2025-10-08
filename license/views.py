from django.shortcuts import render
from institutions.models import Institution
from rest_framework import parsers, permissions, status, viewsets
from rest_framework.response import Response

from .models import (CertificationAndClassification, IntrimAuthority,
                     PublicationYear)
from .serializers import (CertificationAndClassificationSerializer,
                          IntrimAuthoritySerializer)


# Create your views here.
class CertificationAndClassificationViewset(viewsets.ModelViewSet):
    '''Institution certification and classification'''
    queryset = CertificationAndClassification.objects.all()
    serializer_class = CertificationAndClassificationSerializer
    permissions_classes = [permissions.IsAuthenticated]
    pagination_class = None
    parsers_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser] 

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
    

class IntrimAuthorityViewset(viewsets.ModelViewSet):
    '''Interim Authority Application'''
    queryset = IntrimAuthority.objects.all()
    serializer_class = IntrimAuthoritySerializer
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
    
    def create(self, request):
        '''Set institution to the logged in user's institution'''
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            user = self.request.user
            institution = Institution.objects.get(user=user)
            
            serializer.save(institution=institution, status="draft")
            return Response(serializer.data, status=status.HTTP_201_CREATED)


        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)