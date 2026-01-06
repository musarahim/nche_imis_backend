from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'license'
# Create a router and register our viewset with it.
router = DefaultRouter()
router.register(r'certification-and-classification', views.CertificationAndClassificationViewset)
router.register(r'intrim-authority', views.IntrimAuthorityViewset, basename='intrim-authority')
router.register(r'university-provisional-license', views.UniversityProvisionalLicenseViewset, basename='university-provisional-license')
router.register(r'charter-application', views.CharterApplicationViewset, basename='charter-application')
router.register(r'interim-discussion', views.InterimDiscussionViewset, basename='interim-discussion')
router.register(r'provisional-license-odia', views.ProvisionalLicenseODIAViewset, basename='provisional-license-odia')
router.register(r'oti-provisional', views.OTIProvisionalViewset, basename='oti-provisional')


urlpatterns = [
    path('', include(router.urls)),
]