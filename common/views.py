from django.shortcuts import render
from django.views.generic import TemplateView
from rest_framework import permissions, viewsets

from .models import District
from .serializers import DistrictSerializer

# Create your views here.


class HomePageView(TemplateView):
    template_name = "email.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message'] = "Welcome to our website!"
        return context
    

class DistrictViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing District instances.
    """
    queryset = District.objects.order_by('name')
    serializer_class = DistrictSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]  
    pagination_class = None  

    
