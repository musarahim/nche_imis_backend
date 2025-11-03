from django.shortcuts import render
from institutions.models import Institution
from rest_framework import filters, parsers, permissions, status, viewsets
from rest_framework.response import Response

from .models import ProgrammeAccreditation
from .serializers import ProgrammeAccreditationSerializer


# Create your views here.
class ProgrammeAccreditationViewset(viewsets.ModelViewSet):
    '''Programme Accreditation Applications'''
    queryset = ProgrammeAccreditation.objects.all()
    serializer_class = ProgrammeAccreditationSerializer
    permissions_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['application_number','programme_name','programme_level','status','institution__name']
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
    
    def create(self, request):
        '''Set institution to the logged in user's institution'''
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            user = self.request.user
            institution = Institution.objects.get(user=user)
            serializer.save(institution=institution)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
