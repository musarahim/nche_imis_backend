from django.urls import path

from . import views

app_name = 'contacts'


urlpatterns = [
    path("login/jwt/", views.CustomTokenObtainPairView.as_view(), name="generate-token-jwt"),
    path('jwt/refresh/', views.CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('jwt/verify/', views.CustomTokenVerifyView.as_view(), name='token_verify'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
]