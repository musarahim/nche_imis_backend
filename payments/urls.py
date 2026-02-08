from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'payments'
# Create a router and register our viewset with it.
router = DefaultRouter()

router.register(r'application-prns', views.ApplicationPRNSViewSet, basename='application-prns')


urlpatterns = [
    path('', include(router.urls)),
]