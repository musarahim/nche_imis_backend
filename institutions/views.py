from accounts.serializers import RegisterInstitutionSerializer
from django.shortcuts import render
from rest_framework import permissions, viewsets

from .models import Institution, OtherDocuments
from .serializers import InstitutionSerializer, OtherDocumentsSerializer


# Create your views here.
class InstitutionViewSet(viewsets.ModelViewSet):
    '''Institution viewset'''
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    search_fields = ['name',"institution_type"]

    def get_serializer_class(self):
        '''Return different serializers based on action'''
        if self.action == 'partial_update':
            return RegisterInstitutionSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        '''Return only active institutions'''
        queryset = Institution.objects.all().order_by('name')
        
        # Check if user is authenticated first
        if not self.request.user.is_authenticated:
            return queryset.none()  # Return empty queryset for unauthenticated users
            
        if self.request.user.is_superuser or self.request.user.groups.filter(name='System Administrator').exists():
            data = queryset
        else:
            data = queryset.filter(user=self.request.user)
        return data
    
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
        

class OtherDocumentsViewset(viewsets.ModelViewSet):
    '''Institution other documents'''
    queryset = OtherDocuments.objects.all()
    serializer_class = OtherDocumentsSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        '''return documents for the logged in institution'''
        queryset = self.queryset
        
        # Check if user is authenticated first
        if not self.request.user.is_authenticated:
            return queryset.none()  # Return empty queryset for unauthenticated users
            
        if self.request.user.is_superuser or self.request.user.groups.filter(name='System Administrator').exists():
            data = queryset
        else:
            if hasattr(self.request.user, 'institution'):
                data = queryset.filter(institution=self.request.user.institution)
            else:
                data = queryset.none()  # Return empty queryset if user has no institution
        return data
    


