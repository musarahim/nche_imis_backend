from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'common'
# Create a router and register our viewset with it.
router = DefaultRouter()
router.register(r'districts', views.DistrictViewSet, basename='district')
router.register(r'regions', views.RegionViewSet, basename='region')
router.register(r'nationalities', views.NationalityViewSet, basename='nationality')
router.register(r'tribes', views.TribeViewSet, basename='tribe')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', views.HomePageView.as_view(), name='home'),
]