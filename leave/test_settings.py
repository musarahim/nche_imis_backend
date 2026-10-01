"""Isolated leave API tests, with SQLite and captured email.

Run: python -m django test leave.tests --settings=leave.test_settings
These tests cover the current models and API, not migration compatibility.
"""

SECRET_KEY = 'leave-tests-only'
INSTALLED_APPS = [
    'django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions',
    'simple_history', 'accounts', 'common', 'hr', 'leave',
]
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
AUTH_USER_MODEL = 'accounts.User'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
ROOT_URLCONF = 'leave.urls'
USE_TZ = True
TIME_ZONE = 'Africa/Kampala'
ALLOWED_HOSTS = ['testserver']
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
DEFAULT_FROM_EMAIL = 'leave@example.test'
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
MIGRATION_MODULES = {app: None for app in ['accounts', 'common', 'hr', 'leave']}
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework.authentication.BasicAuthentication'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}
