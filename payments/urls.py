from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'payments'
# Create a router and register our viewset with it.
router = DefaultRouter()

router.register(r'application-prns', views.ApplicationPRNSViewSet, basename='application-prns')


urlpatterns = [
    path('', include(router.urls)),
    
    # External API endpoints for third-party integration
    path('external/generate-prn/', views.ExternalPRNGenerationAPIView.as_view(), name='external-generate-prn'),
    path('external/check-prn-status/', views.ExternalPRNStatusAPIView.as_view(), name='external-check-prn-status'),
    path('get-tin-details/', views.TINDetailsView.as_view(), name='external-get-tin-details'),
]