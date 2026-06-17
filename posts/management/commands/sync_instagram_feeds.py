"""
Management command: sync_instagram_feeds
Syncs real Instagram media for all connected accounts + broadcasts via WebSocket.
Also syncs public celebrity handles via oEmbed for real iframe embeds.
"""
import logging
from django.core.management.base import BaseCommand
from django.test import RequestFactory
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.template.loader import render_to_string
from users.models_instagram import InstagramAccount
from users import instagram_service
from users.views import _sync_instagram_account
from posts.models import Post
from posts.views import apply_hashtags

logger = logging.getLogger(__name__)

# Public Instagram handles synced via oEmbed (no auth needed)
# These use real public post URLs and render as actual Instagram iframes.
PUBLIC_HANDLES_POOL = [
    {
        'username': 'thanthitv',
        'bio': 'Thanthi TV - Tamil News & Media Group',
        'url': 'https://www.instagram.com/p/C6Z7o24Sdf1/',
        'content': 'டி-சர்ட் வாசகத்தால் ரிஜேக்ட் ஆன வேலை... அமேசான் பிரைம் வீடியோ நிர்வாகி பவிஷா ஜெயின் விளக்கம். #thanthitv #tamilnews',
    },
    {
        'username': 'msdhoni',
        'bio': 'M S Dhoni - Legend',
        'url': 'https://www.instagram.com/p/CzYVnUqyR_G/',
        'content': 'Back to where it started. Special memories at the ranch. #dhoni #cricket #msd',
    },
    {
        'username': 'cristiano',
        'bio': 'Cristiano Ronaldo',
        'url': 'https://www.instagram.com/p/C7W29vKsc2S/',
        'content': 'Focus on the next challenge. Let\'s go! #ronaldo #football #cr7 #workout',
    },
    {
        'username': 'virat.kohli',
        'bio': 'Virat Kohli',
        'url': 'https://www.instagram.com/p/C8uG15Sxw3L/',
        'content': 'Special moments on the field with the boys. Proud of this team! #kohli #india #cricket',
    },
    {
        'username': 'leomessi',
        'bio': 'Leo Messi',
        'url': 'https://www.instagram.com/p/C8_jW4uIA1c/',
        'content': 'Another victory together. Vamos Argentina! #messi #football #copaamerica',
    },
]


class Command(BaseCommand):
    help = (
        'Syncs real Instagram media for all connected accounts via Graph API. '
        'Also refreshes public handle oEmbed posts.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--public-only',
            action='store_true',
            help='Only sync public handle oEmbed posts (no Graph API calls)',
        )
        parser.add_argument(
            '--connected-only',
            action='store_true',
            help='Only sync connected user accounts via Graph API',
        )

    def handle(self, *args, **options):
        public_only = options.get('public_only', False)
        connected_only = options.get('connected_only', False)

        total_synced = 0

        # ---------------------------------------------------------------
        # 1. Sync connected user accounts via Graph API
        # ---------------------------------------------------------------
        if not public_only:
            total_synced += self._sync_connected_accounts()

        # ---------------------------------------------------------------
        # 2. Sync public handles via oEmbed
        # ---------------------------------------------------------------
        if not connected_only:
            total_synced += self._sync_public_handles()

        self.stdout.write(
            self.style.SUCCESS(f'SUCCESS: Total posts synced this run: {total_synced}')
        )

    def _sync_connected_accounts(self):
        """Sync all active, non-expired connected Instagram accounts."""
        accounts = InstagramAccount.objects.filter(is_active=True)
        if not accounts.exists():
            self.stdout.write(self.style.WARNING(
                'No connected Instagram accounts found. '
                'Users can connect via Profile Edit → Instagram section.'
            ))
            return 0

        synced = 0
        for account in accounts:
            if account.is_token_expired:
                self.stdout.write(self.style.WARNING(
                    f'Skipping @{account.ig_username} — token expired. '
                    f'Run refresh_instagram_tokens or have the user reconnect.'
                ))
                continue

            self.stdout.write(f'Syncing @{account.ig_username} ({account.user.username})...')
            try:
                count = _sync_instagram_account(account.user, account)
                synced += count
                self.stdout.write(self.style.SUCCESS(
                    f'  -> {count} new post(s) from @{account.ig_username}'
                ))
                # Broadcast any new posts via WebSocket
                if count > 0:
                    self._broadcast_latest_posts(account.user, count)
            except instagram_service.InstagramAPIError as e:
                self.stdout.write(self.style.ERROR(
                    f'  [ERROR] API error for @{account.ig_username}: {e}'
                ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'  [ERROR] Unexpected error for @{account.ig_username}: {e}'
                ))

        return synced

    def _sync_public_handles(self):
        """
        Sync public handle posts using oEmbed for real iframe embeds.
        Falls back to storing the permalink as instagram_url if oEmbed is unavailable.
        """
        import random
        from django.contrib.auth.models import User

        synced = 0
        post_data = random.choice(PUBLIC_HANDLES_POOL)
        username = post_data['username']
        bio = post_data['bio']
        url = post_data['url']
        content = post_data['content']

        self.stdout.write(f'Syncing public handle @{username} (oEmbed)...')

        # Skip if already imported
        if Post.objects.filter(instagram_url=url).exists():
            self.stdout.write(f'  -> Already imported, skipping.')
            return 0

        # Try to get real oEmbed HTML
        oembed_data = instagram_service.fetch_oembed(url)
        embed_html = oembed_data.get('html') if oembed_data else None
        if embed_html:
            self.stdout.write(self.style.SUCCESS(f'  -> Got real oEmbed for @{username}'))
        else:
            self.stdout.write(self.style.WARNING(
                f'  -> oEmbed unavailable (App Token not set?) - using iframe fallback'
            ))

        # Create/retrieve the author
        author, _ = User.objects.get_or_create(
            username=username,
            defaults={'email': f'{username}@example.com'}
        )
        profile = author.userprofile
        profile.is_verified = True
        profile.bio = bio
        profile.save(update_fields=['is_verified', 'bio'])

        # Create the post with the real permalink as instagram_url
        post = Post.objects.create(
            author=author,
            content=content,
            instagram_url=url,
            # Store real oEmbed HTML if we have it (added to Post below)
        )

        # Store oEmbed HTML on the post if available
        if embed_html and hasattr(post, 'instagram_embed_html'):
            post.instagram_embed_html = embed_html
            post.save(update_fields=['instagram_embed_html'])

        apply_hashtags(post)
        post.save()

        # Broadcast via WebSocket
        self._broadcast_post(author, post)
        synced += 1

        self.stdout.write(self.style.SUCCESS(
            f'  -> Created post {post.id} from @{username} (real URL: {url})'
        ))
        return synced

    def _broadcast_latest_posts(self, user, count):
        """Broadcast the N most recently synced posts for this user via WebSocket."""
        try:
            recent_posts = Post.objects.filter(author=user).order_by('-created_at')[:count]
            rf = RequestFactory()
            dummy_request = rf.get('/')
            dummy_request.user = user
            dummy_request.all_blocked_ids = set()

            post_html = render_to_string('posts/_post_card_fragment.html', {
                'posts': list(recent_posts),
                'user': user,
                'user_reactions': {},
                'bookmarked_ids': set(),
            }, request=dummy_request)

            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    'posts_feed',
                    {
                        'type': 'new_post',
                        'post_html': post_html,
                        'author_username': user.username,
                    }
                )
        except Exception as e:
            logger.warning('WebSocket broadcast failed: %s', e)

    def _broadcast_post(self, author, post):
        """Broadcast a single post via WebSocket."""
        self._broadcast_latest_posts(author, 1)
