"""
Management command: refresh_instagram_tokens
Verifies and refreshes the Instagrapi login session.
Schedule this to run daily to keep the session alive.
"""
import logging
from django.core.management.base import BaseCommand
from users import instagram_service

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Verifies and refreshes the Instagrapi login session.'

    def handle(self, *args, **options):
        self.stdout.write('Testing and refreshing Instagrapi session...')
        try:
            info = instagram_service.get_connection_info()
            self.stdout.write(self.style.SUCCESS(
                f"SUCCESS: Instagrapi session is active for @{info['username']}.\n"
                f"Account info: {info['follower_count']:,} followers | {info['media_count']:,} posts."
            ))
        except instagram_service.InstagramAPIError as e:
            self.stdout.write(self.style.ERROR(f'  [ERROR] Session verification/refresh failed: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  [ERROR] Unexpected error: {e}'))
