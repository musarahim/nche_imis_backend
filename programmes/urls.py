from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'programmes'
# Create a router and register our viewset with it.
router = DefaultRouter()
router.register(r'programme-accreditation', views.ProgrammeAccreditationViewset, basename='programme-accreditation')
router.register(r'institution-programs', views.ProgramViewset, basename='programs')
urlpatterns = [
    path('', include(router.urls)),
]