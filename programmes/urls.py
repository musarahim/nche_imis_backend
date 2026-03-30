from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'programmes'
# Create a router and register our viewset with it.
router = DefaultRouter()
router.register(r'programme-accreditation', views.ProgrammeAccreditationViewset, basename='programme-accreditation')
router.register(r'institution-programs', views.ProgramViewset, basename='programs')
router.register(r'programme-accessors', views.ProgramAccessorViewset, basename='programme-accessors')
router.register(r'programme-reviewers', views.ProgrammeReviewersViewset, basename='programme-reviewers')
router.register(r'preliminary-reviews', views.PreminaryReviewViewset, basename='preliminary-reviews')
router.register(r'programme-assessments', views.ProgrammeAssessmentViewset, basename='programme-assessments')

urlpatterns = [
    path('', include(router.urls)),
]