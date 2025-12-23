from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from trench.utils import user_token_generator
from trench.views.jwt import MFASecondStepJWTView

# views 

class CustomMFAJWTView(MFASecondStepJWTView):
    '''Overiding the jwt token to include cookie based auth '''

    def post(self, request, *args, **kwargs):
        '''Overiding the jwt token to include cookie based auth '''
        print(request.data, 'request data in custom mfa view')
        response = super().post(request, *args, **kwargs)
        ephemeral_token = request.data.get('ephemeral_token')
        # getting the user from the token
        user = user_token_generator.check_token(user=None, token=ephemeral_token)
        token = RefreshToken.for_user(user=user)
        access_token = str(token.access_token)
        refresh_token = str(token)
        print(access_token, 'access_token')
        # print(refresh_token, 'refresh_token')
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
        print(refresh_token, 'refresh token')
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
    def post(self, request):
        '''logout the user by deleting the cookies'''
        response = Response(status=status.HTTP_200_OK)
        response.delete_cookie('access')
        response.delete_cookie('refresh')
        return response