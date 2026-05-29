from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView, TokenVerifyView)

# views 

class CustomTokenObtainPairView(TokenObtainPairView):
    """Issue JWT pair from username/password and set auth cookies."""

    def post(self, request, *args, **kwargs):
        """Issue JWT pair from username/password and set auth cookies."""
        response = super().post(request, *args, **kwargs)
        access_token = response.data.get("access")
        refresh_token = response.data.get("refresh")

        if not access_token or not refresh_token:
            return response

        response.set_cookie(
            "access", access_token,
            max_age=settings.AUTH_COOKIE_ACCESS_MAX_AGES,
            path=settings.AUTH_COOKIE_PATH,
            secure=settings.AUTH_COOKIE_SECURE,
            httponly=settings.AUTH_COOKIE_HTTP_ONLY,
            samesite=settings.AUTH_COOKIE_SAMESITE,
        )
        response.set_cookie(
            'refresh',
            refresh_token,
            max_age=settings.AUTH_COOKIE_REFRESH_MAX_AGES,
            path=settings.AUTH_COOKIE_PATH,
            secure=settings.AUTH_COOKIE_SECURE,
            httponly=settings.AUTH_COOKIE_HTTP_ONLY,
            samesite=settings.AUTH_COOKIE_SAMESITE,
        )
        
        return response
    

class CustomTokenRefreshView(TokenRefreshView): 
    '''override the post method to set the cookie'''

    def post(self, request, *args, **kwargs):
        '''set the access token as a cookie'''
        refresh_token = request.COOKIES.get('refresh')
        if refresh_token:
            request.data['refresh'] = refresh_token
        response = super(CustomTokenRefreshView, self).post(request, *args, **kwargs)
        if response.status_code == 200:
            access_token = response.data.get('access')
            response.set_cookie(
                'access',
                access_token,
                max_age=settings.AUTH_COOKIE_ACCESS_MAX_AGES,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE,
            )

        return response
    

class CustomTokenVerifyView(TokenVerifyView):
    '''override the post method to set the cookie'''
    def post(self, request, *args, **kwargs):
        '''set the access token as a cookie'''
        access_token = request.COOKIES.get('access')
        if access_token:
            request.data['token'] = access_token
        return super(CustomTokenVerifyView, self).post(request, *args, **kwargs)
    

class LogoutView(APIView):
    '''logout the user by deleting the cookies'''
    def post(self, _request):
        '''logout the user by deleting the cookies'''
        response = Response(status=status.HTTP_200_OK)
        response.delete_cookie('access')
        response.delete_cookie('refresh')
        return response