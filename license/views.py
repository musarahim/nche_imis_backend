from django.shortcuts import render
from django.utils import timezone
from institutions.models import Institution
from payments.ura_payment import UraMdaPaymentService
from rest_framework import filters, parsers, permissions, status, viewsets
from rest_framework.response import Response

from .models import (CertificationAndClassification, CharterApplication,
                     InterimDiscussion, IntrimAuthority, OTIProvisional,
                     OTIProvisionalAward, UniversityProvisionalLicense)
from .serializers import (CertificationAndClassificationSerializer,
                          CharterApplicationSerializer,
                          InterimDiscussionSerializer,
                          IntrimAuthoritySerializer,
                          OTIProvisionalAwardSerializer,
                          OTIProvisionalSerializer,
                          UniversityProvisionalLicenseSerializer)

service = UraMdaPaymentService()
# Create your views here.

class CertificationAndClassificationViewset(viewsets.ModelViewSet):
    '''Institution certification and classification'''
    queryset = CertificationAndClassification.objects.all()
    serializer_class = CertificationAndClassificationSerializer
    permission_classes = [permissions.IsAuthenticated]
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
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def partial_update(self, request, pk=None):
        '''Partial update of the Certification and Classification Application'''
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            if serializer.validated_data.get('status') == 'submitted':
                print("Status is submitted, checking PRN...")
                prn_check = service.generate_and_save_prn(
                    {
                    "amount": 200000,
                    "assessmentDate": timezone.now().isoformat(),
                    "paymentType": "DT",
                    "referenceNo": instance.application_code,
                    "tin": instance.institution.tin,
                    "srcSystem": "Imis",
                    "taxHead": "NCHE001",
                    "taxSubHead": "",
                    "email": instance.institution.user.email or instance.institution.alternative_email,
                    "taxPayerName": instance.institution.name,
                    "plot": "",
                    "buildingName": "",
                    "street": "",
                    "tradeCentre": "",
                    "district": instance.institution.district.name if instance.institution.district else "",
                    "county": "",
                    "subCounty": "",
                    "parish": "",
                    "village": "",
                    "localCouncil": "",
                    "contactNo": f'0{instance.institution.contact_person_phone.national_number}' if instance.institution.contact_person_phone else "",
                    "paymentPeriod": "",
                    "expiryDays": "",
                    "mobileMoneyNumber": "",
                    "mobileNo": f'0{instance.institution.contact_person_phone.national_number}' if instance.institution.contact_person_phone else ""
                })  # Example call
                print(prn_check, "result from URA PRN check")
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
    

class IntrimAuthorityViewset(viewsets.ModelViewSet):
    '''Interim Authority Application'''
    queryset = IntrimAuthority.objects.filter(is_odai=False)
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
            # check if status is submitted, then call service method to generate PRN
            if serializer.validated_data.get('status') == 'submitted':
                print("Status is submitted, checking PRN...")
                prn_check=service.generate_and_save_prn(
                    {
                    "amount": 200000,
                    "assessmentDate": timezone.now().isoformat(),
                    "paymentType": "DT",
                    "referenceNo": instance.application_code,
                    "tin": instance.institution.tin,
                    "srcSystem": "Imis",
                    "taxHead": "NCHE001",
                    "taxSubHead": "",
                    "email": instance.institution.alternative_email or instance.institution.user.email,
                    "taxPayerName": instance.institution.name,
                    "plot": "",
                    "buildingName": "",
                    "street": "",
                    "tradeCentre": "",
                    "district": "",
                    "county": "",
                    "subCounty": "",
                    "parish": "",
                    "village": "",
                    "localCouncil": "",
                    "contactNo": f'0{instance.institution.contact_person_phone.national_number}' if instance.institution.contact_person_phone else "",
                    "paymentPeriod": "",
                    "expiryDays": "",
                    "mobileMoneyNumber": "",
                    "mobileNo": f'0{instance.institution.contact_person_phone.national_number}' if instance.institution.contact_person_phone else ""
                })  # Example call
                print(prn_check, "result from URA PRN check")
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# intrim authority ODI
class IntrimAuthorityODIViewset(viewsets.ModelViewSet):
    '''ODI Interim Authority Application'''
    queryset = IntrimAuthority.objects.filter(is_odai=True)
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
            
            serializer.save(institution=institution, status="draft", is_odai=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)


        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def partial_update(self, request, pk=None):
        '''Partial update of the Interim Authority Application'''
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            # You can call service methods here if needed, e.g., service.get_prn(...)
            if serializer.validated_data.get('status') == 'submitted':
                print("Status is submitted, checking PRN...")
                prn_check=service.generate_and_save_prn(
                    {
                    "amount": 200000,
                    "assessmentDate": timezone.now().isoformat(),
                    "paymentType": "DT",
                    "referenceNo": instance.application_code,
                    "tin": instance.institution.tin,
                    "srcSystem": "Imis",
                    "taxHead": "NCHE001",
                    "taxSubHead": "",
                    "email": instance.institution.alternative_email or instance.institution.user.email,
                    "taxPayerName": instance.institution.name,
                    "plot": "",
                    "buildingName": "",
                    "street": "",
                    "tradeCentre": "",
                    "district": "",
                    "county": "",
                    "subCounty": "",
                    "parish": "",
                    "village": "",
                    "localCouncil": "",
                    "contactNo": f'0{instance.institution.contact_person_phone.national_number}' if instance.institution.contact_person_phone else "",
                    "paymentPeriod": "",
                    "expiryDays": "",
                    "mobileMoneyNumber": "",
                    "mobileNo": f'0{instance.institution.contact_person_phone.national_number}' if instance.institution.contact_person_phone else ""
                })  # Example call
                print(prn_check, "result from URA PRN check")
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class InterimDiscussionViewset(viewsets.ModelViewSet):
    '''Interim Discussion Viewset'''
    queryset = InterimDiscussion.objects.all()
    serializer_class = InterimDiscussionSerializer
    permission_classes = [permissions.IsAuthenticated]
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
    queryset = UniversityProvisionalLicense.objects.filter(is_odai=False)
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
    
    def partial_update(self, request, pk=None):
        '''Partial update of the University Provisional License Application'''
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            # You can call service methods here if needed, e.g., service.get_prn(...)
            if serializer.validated_data.get('status') == 'submitted':
                print("Status is submitted, checking PRN...")
                prn_check=service.generate_and_save_prn(
                    {
                    "amount": 200000,
                    "assessmentDate": timezone.now().isoformat(),
                    "paymentType": "DT",
                    "referenceNo": instance.application_code,
                    "tin": instance.institution.tin,
                    "srcSystem": "Imis",
                    "taxHead": "NCHE001",
                    "taxSubHead": "",
                    "email": instance.institution.alternative_email or instance.institution.user.email,
                    "taxPayerName": instance.institution.name,
                    "plot": "",
                    "buildingName": "",
                    "street": "",
                    "tradeCentre": "",
                    "district": "",
                    "county": "",
                    "subCounty": "",
                    "parish": "",
                    "village": "",
                    "localCouncil": "",
                    "contactNo": f'0{instance.institution.contact_person_phone.national_number}' if instance.institution.contact_person_phone else "",
                    "paymentPeriod": "",
                    "expiryDays": "",
                    "mobileMoneyNumber": "",
                    "mobileNo": f'0{instance.institution.contact_person_phone.national_number}' if instance.institution.contact_person_phone else ""
                })  # Example call
                print(prn_check, "result from URA PRN check")
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# provisional license ODI
class ODAIProvisionalLicenseViewset(viewsets.ModelViewSet):
    '''University Provisional License Application'''
    queryset = UniversityProvisionalLicense.objects.filter(is_odai=True)
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
            
            serializer.save(institution=institution, status="draft", is_odai=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)


        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

    def partial_update(self, request, pk=None):
        '''Partial update of the University Provisional License Application'''
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            # You can call service methods here if needed, e.g., service.get_prn(...)
            if serializer.validated_data.get('status') == 'submitted':
                print("Status is submitted, checking PRN...")
                prn_check=service.generate_and_save_prn(
                    {
                    "amount": 200000,
                    "assessmentDate": timezone.now().isoformat(),
                    "paymentType": "DT",
                    "referenceNo": instance.application_code,
                    "tin": instance.institution.tin,
                    "srcSystem": "Imis",
                    "taxHead": "NCHE001",
                    "taxSubHead": "",
                    "email": instance.institution.alternative_email or instance.institution.user.email,
                    "taxPayerName": instance.institution.name,
                    "plot": "",
                    "buildingName": "",
                    "street": "",
                    "tradeCentre": "",
                    "district": "",
                    "county": "",
                    "subCounty": "",
                    "parish": "",
                    "village": "",
                    "localCouncil": "",
                    "contactNo": f'0{instance.institution.contact_person_phone.national_number}' if instance.institution.contact_person_phone else "",
                    "paymentPeriod": "",
                    "expiryDays": "",
                    "mobileMoneyNumber": "",
                    "mobileNo": f'0{instance.institution.contact_person_phone.national_number}' if instance.institution.contact_person_phone else ""
                })  # Example call
                print(prn_check, "result from URA PRN check")
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CharterApplicationViewset(viewsets.ModelViewSet):
    '''University Grant Charter Application'''
    queryset = CharterApplication.objects.filter(is_odai=False)
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


    def partial_update(self, request, pk=None):
        '''Partial update of the Charter Application'''
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            # You can call service methods here if needed, e.g., service.get_prn(...)
            if serializer.validated_data.get('status') == 'submitted':
                print("Status is submitted, checking PRN...")
                prn_check=service.generate_and_save_prn(
                    {
                    "amount": 200000,
                    "assessmentDate": timezone.now().isoformat(),
                    "paymentType": "DT",
                    "referenceNo": instance.application_code,
                    "tin": instance.institution.tin,
                    "srcSystem": "Imis",
                    "taxHead": "NCHE001",
                    "taxSubHead": "",
                    "email": instance.institution.alternative_email or instance.institution.user.email,
                    "taxPayerName": instance.institution.name,
                    "plot": "",
                    "buildingName": "",
                    "street": "",
                    "tradeCentre": "",
                    "district": "",
                    "county": "",
                    "subCounty": "",
                    "parish": "",
                    "village": "",
                    "localCouncil": "",
                    "contactNo": f'0{instance.institution.contact_person_phone.national_number}' if instance.institution.contact_person_phone else "",
                    "paymentPeriod": "",
                    "expiryDays": "",
                    "mobileMoneyNumber": "",
                    "mobileNo": f'0{instance.institution.contact_person_phone.national_number}' if instance.institution.contact_person_phone else ""
                })  # Example call
                print(prn_check, "result from URA PRN check")
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

# ODI charter application
class ODICharterApplicationViewset(viewsets.ModelViewSet):
    '''University Grant Charter Application'''
    queryset = CharterApplication.objects.filter(is_odai=True)
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
            
            serializer.save(institution=institution, status="draft", is_odai=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def partial_update(self, request, pk=None):
        '''Partial update of the Charter Application'''
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            # You can call service methods here if needed, e.g., service.get_prn(...)
            if serializer.validated_data.get('status') == 'submitted':
                print("Status is submitted, checking PRN...")
                prn_check=service.generate_and_save_prn(
                    {
                    "amount": 200000,
                    "assessmentDate": timezone.now().isoformat(),
                    "paymentType": "DT",
                    "referenceNo": instance.application_code,
                    "tin": instance.institution.tin,
                    "srcSystem": "Imis",
                    "taxHead": "NCHE001",
                    "taxSubHead": "",
                    "email": instance.institution.alternative_email or instance.institution.user.email,
                    "taxPayerName": instance.institution.name,
                    "plot": "",
                    "buildingName": "",
                    "street": "",
                    "tradeCentre": "",
                    "district": "",
                    "county": "",
                    "subCounty": "",
                    "parish": "",
                    "village": "",
                    "localCouncil": "",
                    "contactNo": f'0{instance.institution.contact_person_phone.national_number}' if instance.institution.contact_person_phone else "",
                    "paymentPeriod": "",
                    "expiryDays": "",
                    "mobileMoneyNumber": "",
                    "mobileNo": f'0{instance.institution.contact_person_phone.national_number}' if instance.institution.contact_person_phone else ""
                })  # Example call
                print(prn_check, "result from URA PRN check")
            return Response(serializer.data, status=status.HTTP_200_OK)
        
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
    
    def partial_update(self, request, pk=None):
        '''Partial update of the Interim Authority Application'''
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            # You can call service methods here if needed, e.g., service.get_prn(...)
            if serializer.validated_data.get('status') == 'submitted':
                print("Status is submitted, checking PRN...")
                prn_check=service.generate_and_save_prn(
                    {
                    "amount": 200000,
                    "assessmentDate": timezone.now().isoformat(),
                    "paymentType": "DT",
                    "referenceNo": instance.code,
                    "tin": instance.institute.tin,
                    "srcSystem": "Imis",
                    "taxHead": "NCHE001",
                    "taxSubHead": "",
                    "email": instance.institute.alternative_email or instance.institute.user.email,
                    "taxPayerName": instance.institute.name,
                    "plot": "",
                    "buildingName": "",
                    "street": "",
                    "tradeCentre": "",
                    "district": "",
                    "county": "",
                    "subCounty": "",
                    "parish": "",
                    "village": "",
                    "localCouncil": "",
                    "contactNo": f'0{instance.institute.contact_person_phone.national_number}' if instance.institute.contact_person_phone else "",
                    "paymentPeriod": "",
                    "expiryDays": "",
                    "mobileMoneyNumber": "",
                    "mobileNo": f'0{instance.institute.contact_person_phone.national_number}' if instance.institute.contact_person_phone else ""
                })  # Example call
                print(prn_check, "result from URA PRN check")
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class OTIProvisionalAwardViewset(viewsets.ModelViewSet):
    '''OTI Provisional Award Letters'''
    queryset = OTIProvisionalAward.objects.all()
    serializer_class = OTIProvisionalAwardSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    pagination_class = None
    search_fields = ['oti_provisional__application_code','oti_provisional__institute__name','code','issue_date']
    
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