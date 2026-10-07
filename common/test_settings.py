"""Isolated common API tests: python -m django test common.tests --settings=common.test_settings."""

import os

SECRET_KEY = 'common-tests-only'
INSTALLED_APPS = [
    'django.contrib.auth', 'django.contrib.contenttypes', 'simple_history',
    'accounts', 'common', 'institutions', 'programmes', 'hr', 'leave', 'license',
]
# The license models imported by common.views include PostgreSQL array fields.
DATABASES = {'default': {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': os.environ.get('POSTGRES_DB'),
    'USER': os.environ.get('POSTGRES_USER'),
    'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
    'HOST': os.environ.get('POSTGRES_HOST'),
    'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    'TEST': {'NAME': 'test_common_api'},
}}
AUTH_USER_MODEL = 'accounts.User'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
ROOT_URLCONF = 'common.urls'
USE_TZ = True
TIME_ZONE = 'Africa/Kampala'
ALLOWED_HOSTS = ['testserver']
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
MIGRATION_MODULES = {
    app: None for app in ['auth', 'contenttypes', 'accounts', 'common', 'institutions', 'programmes', 'hr', 'leave', 'license']
}
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework.authentication.BasicAuthentication'],
}
