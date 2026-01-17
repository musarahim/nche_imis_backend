from django.shortcuts import render
from institutions.models import Institution
from payments.ura_payment import UraMdaPaymentService
from rest_framework import filters, parsers, permissions, status, viewsets
from rest_framework.response import Response

from .models import (CertificationAndClassification, CharterApplication,
                     InterimDiscussion, IntrimAuthority, OTIProvisional,
                     ProvisionalLicenseODIA, PublicationYear,
                     UniversityProvisionalLicense)
from .serializers import (CertificationAndClassificationSerializer,
                          CharterApplicationSerializer,
                          InterimDiscussionSerializer,
                          IntrimAuthoritySerializer, OTIProvisionalSerializer,
                          ProvisionalLicenseODIASerializer,
                          UniversityProvisionalLicenseSerializer)


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
    
    def create(self, request):
        '''Set institution to the logged in user's institution'''
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            user = self.request.user
            institution = Institution.objects.get(user=user)
            
            serializer.save(institution=institution, status="draft")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    

class IntrimAuthorityViewset(viewsets.ModelViewSet):
    '''Interim Authority Application'''
    queryset = IntrimAuthority.objects.all()
    serializer_class = IntrimAuthoritySerializer
    permissions_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['application_code','institution__name','status','application_date']
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
    
    def partial_update(self, request, pk=None):
        '''Partial update of the Interim Authority Application'''
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            service = UraMdaPaymentService()
            # You can call service methods here if needed, e.g., service.get_prn(...)
            prn_check=service.check_prn_status(prn="2240015259832")  # Example call
            print(prn_check, "result from URA PRN check")
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class InterimDiscussionViewset(viewsets.ModelViewSet):
    '''Interim Discussion Viewset'''
    queryset = InterimDiscussion.objects.all()
    serializer_class = InterimDiscussionSerializer
    permissions_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    pagination_class = None
    search_fields = ['institution__name','discussion_date','remarks']
    
    def get_queryset(self):
        '''return documents for the logged in institution'''
        queryset = self.queryset
        data = queryset  # Initialize data with default value
        
        if self.request.user.is_superuser or self.request.user.groups.filter(name='System Administrator').exists():
            data = queryset
        
        # Filter by application parameter if provided in request
        application = self.request.query_params.get('application_id', None)
        if application is not None:
            data = queryset.filter(application=application)
        
        return data
    
    
class UniversityProvisionalLicenseViewset(viewsets.ModelViewSet):
    '''University Provisional License Application'''
    queryset = UniversityProvisionalLicense.objects.all()
    serializer_class = UniversityProvisionalLicenseSerializer
    permissions_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['application_code','institution__name','status','application_date']
    
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
    


class CharterApplicationViewset(viewsets.ModelViewSet):
    '''University Grant Charter Application'''
    queryset = CharterApplication.objects.all()
    serializer_class = CharterApplicationSerializer
    permissions_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['application_code','institution__name','status','application_date']
    
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
    
class ProvisionalLicenseODIAViewset(viewsets.ModelViewSet):
    '''Provisional License ODIA Application'''
    queryset = ProvisionalLicenseODIA.objects.all()
    serializer_class = ProvisionalLicenseODIASerializer
    permissions_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['application_code','institution__name','status','application_date']
    
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
    

class OTIProvisionalViewset(viewsets.ModelViewSet):
    '''OTI Provisional License Application'''
    queryset = OTIProvisional.objects.all()
    serializer_class = OTIProvisionalSerializer
    permissions_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['application_code','institute__name','status','application_date']
    
    def get_queryset(self):
        '''return documents for the logged in institution'''
        queryset = self.queryset
        if self.request.user.is_superuser or self.request.user.groups.filter(name='System Administrator').exists():
            data = queryset
        else:
            if hasattr(self.request.user, 'institution'):
                data = queryset.filter(institute=self.request.user.institution)
            else:
                data = None
        return data
    
    def create(self, request):
        '''Set institution to the logged in user's institution'''
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            user = self.request.user
            institution = Institution.objects.get(user=user)
            
            serializer.save(institute=institution, status="draft")
            return Response(serializer.data, status=status.HTTP_201_CREATED)


        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)