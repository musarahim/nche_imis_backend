from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'appraisals'

router = DefaultRouter()

router.register(r'performance-appraisals', views.PerformanceAppraisalViewSet, basename='performance-appraisal')
router.register(r'appraisal-outputs', views.AppraisalOutputViewSet, basename='appraisal-output')
router.register(r'competency-ratings', views.CompetencyRatingViewSet, basename='competency-rating')
router.register(r'improvement-areas', views.ImprovementAreaViewSet, basename='improvement-area')
router.register(r'next-year-plans', views.NextYearPerformancePlanViewSet, basename='next-year-plan')
router.register(r'initial-qualifications', views.InitialQualificationViewSet, basename='initial-qualification')
router.register(r'additional-qualifications', views.AdditionalQualificationViewSet, basename='additional-qualification')
router.register(r'trainings', views.TrainingViewSet, basename='training')
router.register(r'appraisal-comments', views.AppraisalCommentViewSet, basename='appraisal-comment')

urlpatterns = [
    path('', include(router.urls)),
]