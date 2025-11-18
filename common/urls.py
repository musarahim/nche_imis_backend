from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'common'
# Create a router and register our viewset with it.
router = DefaultRouter()
router.register(r'districts', views.DistrictViewSet, basename='district')
router.register(r'counties', views.CountyViewSet, basename='counties')
router.register(r'sub-counties', views.SubCountyViewSet, basename='sub-counties')
router.register(r'parishes', views.ParishViewSet, basename='parishes')
router.register(r'villages', views.VillageViewSet, basename='villages')
router.register(r'regions', views.RegionViewSet, basename='region')
router.register(r'nationalities', views.NationalityViewSet, basename='nationality')
router.register(r'tribes', views.TribeViewSet, basename='tribe')
router.register(r'education-levels', views.EducationLevelViewSet, basename='education-level')
router.register(r'titles', views.TitleViewSet, basename='title')
router.register(r'religions', views.ReligionViewSet, basename='religion')
router.register(r'finance-years', views.FinanceYearViewSet, basename='finance-year')
router.register(r'holidays', views.HolidayViewSet, basename='holiday')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', views.HomePageView.as_view(), name='home'),
]