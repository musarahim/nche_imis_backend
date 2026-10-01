"""Isolated invoice integration tests: SQLite and in-memory email, no live services.

Run: python -m django test programmes.tests --settings=programmes.test_settings
"""
SECRET_KEY = 'invoice-tests-only'
INSTALLED_APPS = [
    'django.contrib.auth', 'django.contrib.contenttypes',
    'simple_history', 'accounts', 'common', 'institutions', 'programmes',
]
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
AUTH_USER_MODEL = 'accounts.User'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
ROOT_URLCONF = 'programmes.test_urls'
USE_TZ = True
TIME_ZONE = 'Africa/Kampala'
ALLOWED_HOSTS = ['testserver']
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
DEFAULT_FROM_EMAIL = 'accounts@example.test'
MEDIA_URL = '/media/'
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
# These tests exercise the current invoice model and API, independently of
# unrelated application migrations and production database configuration.
MIGRATION_MODULES = {app: None for app in ['accounts', 'common', 'institutions', 'programmes']}
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework.authentication.BasicAuthentication'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}
