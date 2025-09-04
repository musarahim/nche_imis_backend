from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'institutions'
# Create a router and register our viewset with it.
router = DefaultRouter()
router.register(r'institutions', views.InstitutionViewSet)
router.register(r'publication-years', views.PublicationYearViewSet)
router.register(r'other-documents', views.OtherDocumentsViewset)
router.register(r'certification-and-classification', views.CertificationAndClassificationViewset)

urlpatterns = [
    path('', include(router.urls)),
]