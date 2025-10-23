from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'license'
# Create a router and register our viewset with it.
router = DefaultRouter()
router.register(r'certification-and-classification', views.CertificationAndClassificationViewset)
router.register(r'intrim-authority', views.IntrimAuthorityViewset, basename='intrim-authority')
router.register(r'university-provisional-license', views.UniversityProvisionalLicenseViewset, basename='university-provisional-license')


urlpatterns = [
    path('', include(router.urls)),
]