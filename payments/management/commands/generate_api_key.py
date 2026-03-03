from django.core.management.base import BaseCommand
from rest_framework_api_key.models import APIKey


class Command(BaseCommand):
    help = 'Generate API key for external system integration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            type=str,
            required=True,
            help='Name/identifier for the API key (e.g., "External_System_1")'
        )

    def handle(self, *args, **options):
        name = options['name']
        
        # Generate API key
        api_key, key = APIKey.objects.create_key(name=name)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'API key generated successfully!\n'
                f'Name: {name}\n'
                f'ID: {api_key.id}\n'
                f'Key: {key}\n'
                f'Created: {api_key.created}\n\n'
                f'IMPORTANT: Store this key securely. It cannot be retrieved again.\n'
                f'Use this key in the X-Api-Key header for API requests.'
            )
        )