"""Isolated PostgreSQL license API tests; no external payment calls."""
from common.test_settings import *  # noqa: F403

INSTALLED_APPS = [*INSTALLED_APPS, 'payments']  # noqa: F405
MIGRATION_MODULES = {**MIGRATION_MODULES, 'payments': None}  # noqa: F405
DATABASES['default']['TEST']['NAME'] = 'test_license_api'  # noqa: F405
URA_BASE_URL = 'https://payments.example.test'
URA_TOKEN_ENDPOINT = 'https://payments.example.test/token'
URA_CONSUMER_KEY = 'test-only'
URA_CONSUMER_SECRET = 'test-only'
MEDIA_URL = '/media/'
