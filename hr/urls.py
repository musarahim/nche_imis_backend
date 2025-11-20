from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'hr'
# Create a router and register our viewset with it.
router = DefaultRouter()
router.register(r'directorates', views.DirectorateViewSet, basename='directorate')
router.register(r'departments', views.DepartmentViewSet, basename='department')
router.register(r'designations', views.DesignationViewSet, basename='designation')
router.register(r'grade-scales', views.GradeScaleViewSet, basename='grade-scale')
router.register(r'dependents', views.DependentViewSet, basename='dependent')
router.register(r'education-histories', views.EducationHistoryViewSet, basename='education-history')
router.register(r'work-histories', views.WorkHistoryViewSet, basename='work-history')
router.register(r'referees', views.RefereeViewSet, basename='referee')
router.register(r'employees', views.EmployeeViewSet, basename='employee')
urlpatterns = [
    path('', include(router.urls)),
]