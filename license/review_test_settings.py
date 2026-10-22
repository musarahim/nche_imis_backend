"""Isolated database for licensing assignment schema and regression tests."""
from .test_settings import *  # noqa: F403

DATABASES['default']['TEST']['NAME'] = 'test_licensing_reviewer_assignment'  # noqa: F405
