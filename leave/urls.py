from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'hr'
# Create a router and register our viewset with it.
router = DefaultRouter()
router.register(r'leave-types', views.LeaveTypeViewset, basename='leave-type')
router.register(r'leave-applications', views.LeaveApplicationViewSet, basename='leave-application')

urlpatterns = [
    path('', include(router.urls)),
]