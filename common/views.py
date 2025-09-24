from django.shortcuts import render
from django.views.generic import TemplateView
from rest_framework import permissions, viewsets

from .models import District, Region
from .serializers import DistrictSerializer, RegionSerializer

# Create your views here.


class HomePageView(TemplateView):
    template_name = "email.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message'] = "Welcome to our website!"
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
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]  
    pagination_class = None  

    
