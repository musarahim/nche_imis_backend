from django.apps import AppConfig


class LicenseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'license'

    def ready(self):
        from . import status_tracking  # noqa: F401
