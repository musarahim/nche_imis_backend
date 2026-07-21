from datetime import datetime

from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone
from django.views.generic import TemplateView
from institutions.models import Institution
from programmes.models import Program, ProgramAccreditation
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (County, District, EducationLevel, FinanceYear, Holiday,
                     Nationality, Parish, Region, Relationship, Religion,
                     SubCounty, Title, Tribe, Village)
from .serializers import (CountySerializer, DistrictSerializer,
                          EducationLevelSerializer, FinanceYearSerializer,
                          HolidaySerializer, NationalitySerializer,
                          ParishSerializer, RegionSerializer,
                          RelationshipSerializer, ReligionSerializer,
                          SubCountySerializer, TitleSerializer,
                          TribeSerializer, VillageSerializer)

# Import other models
try:
    from hr.models import Employee
except ImportError:
    Employee = None

try:
    from leave.models import LeaveApplication
except ImportError:
    LeaveApplication = None

try:
    from institutions.models import Institution
except ImportError:
    Institution = None

try:
    from license.models import UniversityProvisionalLicense
except ImportError:
    UniversityProvisionalLicense = None

# Create your views here.


class HomePageView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get dashboard statistics
        context['total_employees'] = Employee.objects.count() if Employee else 0
        context['pending_leaves'] = LeaveApplication.objects.filter(ed_approved=False).count() if LeaveApplication else 0
        context['total_institutions'] = Institution.objects.count() if Institution else 0
        
        # Get monthly applications (current month)
        current_month = timezone.now().replace(day=1)
        if UniversityProvisionalLicense:
            context['monthly_applications'] = UniversityProvisionalLicense.objects.filter(
                created__gte=current_month
            ).count()
        else:
            context['monthly_applications'] = 0
        
        # Get recent leave applications (last 5)
        if LeaveApplication:
            context['recent_leaves'] = LeaveApplication.objects.select_related(
                'employee', 'leave_type'
            ).order_by('-created')[:5]
        else:
            context['recent_leaves'] = []
        
        return context
    
class RegionViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Region instances.
    """
    queryset = Region.objects.order_by('name')
    serializer_class = RegionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]  
    pagination_class = None
    
class DistrictViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing District instances.
    """
    queryset = District.objects.order_by('name')
    serializer_class = DistrictSerializer
    permission_classes = [permissions.AllowAny]  
    pagination_class = None  

class NationalityViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Nationality instances.
    """
    queryset = Nationality.objects.order_by('name')
    serializer_class = NationalitySerializer
    permission_classes = [permissions.AllowAny]  
    pagination_class = None  

class TribeViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Tribe instances.
    """
    queryset = Tribe.objects.order_by('name')
    serializer_class = TribeSerializer
    permission_classes = [permissions.AllowAny]  
    pagination_class = None

class CountyViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing County instances.
    """
    queryset = County.objects.order_by('name')
    serializer_class = CountySerializer
    permission_classes = [permissions.AllowAny]  
    pagination_class = None

    def get_queryset(self):
        """
        Optionally restricts the returned counties to a given district,
        by filtering against a `district_id` query parameter in the URL.
        """
        queryset = self.queryset
        district_id = self.request.query_params.get('district_id', None)
        if district_id is not None:
            queryset = queryset.filter(district__id=district_id)
        return queryset
    
class SubCountyViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Sub-County instances.
    """
    queryset = SubCounty.objects.order_by('name')
    serializer_class = SubCountySerializer
    permission_classes = [permissions.AllowAny]  
    pagination_class = None

    def get_queryset(self):
        """
        Optionally restricts the returned sub-counties to a given county,
        by filtering against a `county_id` query parameter in the URL.
        """
        queryset = self.queryset
        county_id = self.request.query_params.get('county_id', None)
        if county_id is not None:
            queryset = queryset.filter(county__id=county_id)
        return queryset
    

class ParishViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Parish instances.
    """
    queryset = Parish.objects.order_by('name')
    serializer_class = ParishSerializer
    permission_classes = [permissions.AllowAny]  
    pagination_class = None

    def get_queryset(self):
        """
        Optionally restricts the returned parishes to a given sub-county,
        by filtering against a `sub_county_id` query parameter in the URL.
        """
        queryset = self.queryset
        sub_county_id = self.request.query_params.get('sub_county_id', None)
        if sub_county_id is not None:
            queryset = queryset.filter(sub_county__id=sub_county_id)
        return queryset
    
class VillageViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Village instances.
    """
    queryset = Village.objects.order_by('name')
    serializer_class = VillageSerializer
    permission_classes = [permissions.AllowAny]  
    pagination_class = None

    def get_queryset(self):
        """
        Optionally restricts the returned villages to a given parish,
        by filtering against a `parish_id` query parameter in the URL.
        """
        queryset = self.queryset
        parish_id = self.request.query_params.get('parish_id', None)
        if parish_id is not None:
            queryset = queryset.filter(parish__id=parish_id)
        return queryset

class EducationLevelViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Education Level instances.
    """
    queryset = EducationLevel.objects.order_by('name')
    serializer_class = EducationLevelSerializer
    permission_classes = [permissions.AllowAny]  
    pagination_class = None

class TitleViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Title instances.
    """
    queryset = Title.objects.order_by('name')
    serializer_class = TitleSerializer
    permission_classes = [permissions.AllowAny]  
    pagination_class = None

class ReligionViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Religion instances.
    """
    queryset = Religion.objects.order_by('name')
    serializer_class = ReligionSerializer
    permission_classes = [permissions.AllowAny]  
    pagination_class = None

class FinanceYearViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Finance Year instances.
    """
    queryset = FinanceYear.objects.order_by('name')
    serializer_class = FinanceYearSerializer
    permission_classes = [permissions.AllowAny]  
    pagination_class = None

class HolidayViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Holiday instances.
    """
    queryset = Holiday.objects.order_by('name')
    serializer_class = HolidaySerializer
    permission_classes = [permissions.AllowAny]  
    pagination_class = None

class RelationshipViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Relationship instances.
    """
    queryset = Relationship.objects.order_by('name')
    serializer_class = RelationshipSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None


# Institutional Dashboard View
class InstitutionalDashboard(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Get institution-specific statistics
        user = request.user  # Assuming user has an institution field
        institution = Institution.objects.filter(user=user).first()
        programs = Program.objects.filter(institution=institution)
        active_programmes = programs.filter(status='active').count()
        expired_programmes = programs.filter(status='due_for_review').count()
        under_review_programmes = programs.filter(status='under_review').count()
        
        data = {
            'current_license': "CHARTERED",
            'active_programmes': active_programmes,
            'expired_programmes': expired_programmes,
            'under_review_programmes': under_review_programmes,
        }
        return Response(data)

