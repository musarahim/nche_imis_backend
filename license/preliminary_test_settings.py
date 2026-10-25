"""Isolated test schema for saved dynamic preliminary review records."""
from .review_test_settings import *  # noqa: F403

DATABASES['default']['TEST']['NAME'] = 'test_licensing_dynamic_review'  # noqa: F405
