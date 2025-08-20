"""
URL configuration for nche_imis project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from common.views import HomePageView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
   openapi.Info(
      title="UNCHE IMIS API",
      default_version='v3',
      description="Uganda API",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="rwandera@unche.or.ug"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path('', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('portal/', admin.site.urls),
    path('home/', HomePageView.as_view(), name='home'),
    path("api/accounts/", include("accounts.urls", namespace="accounts")),
    path('api/auth/', include('trench.urls.jwt')),
    path('api/', include('djoser.urls')),
    path('api/common/', include('common.urls', namespace='common')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
