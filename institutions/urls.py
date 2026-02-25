from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'institutions'
# Create a router and register our viewset with it.
router = DefaultRouter()
router.register(r'institutions', views.InstitutionViewSet)
router.register(r'other-documents', views.OtherDocumentsViewset)
router.register(r'license-types', views.LicenseTypeViewset)


urlpatterns = [
    path('', include(router.urls)),
]