from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'common'
# Create a router and register our viewset with it.
router = DefaultRouter()
router.register(r'districts', views.DistrictViewSet)

urlpatterns = [
    path('', include(router.urls)),
]