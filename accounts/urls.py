from django.urls import include, path
from rest_framework import routers
from rest_framework.urlpatterns import format_suffix_patterns

from . import views

app_name = 'contacts'


urlpatterns = [
    path("login/jwt/code/", views.CustomMFAJWTView.as_view(), name="generate-token-jwt"),
    path('jwt/refresh/', views.CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('jwt/verify/', views.CustomTokenVerifyView.as_view(), name='token_verify'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
]