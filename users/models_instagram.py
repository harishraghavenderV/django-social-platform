from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class InstagramAccount(models.Model):
    """Stores a connected Instagram account for a ConnectSphere user."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='instagram_account',
    )
    ig_user_id = models.CharField(
        max_length=100,
        help_text='Instagram user ID returned by Graph API',
    )
    ig_username = models.CharField(
        max_length=100,
        help_text='Instagram @handle',
    )
    access_token = models.TextField(
        help_text='Long-lived Instagram access token (60 days)',
    )
    token_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Expiry timestamp for the long-lived token',
    )
    last_synced = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Last time media was synced from Instagram',
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this connection is active',
    )
    auto_sync = models.BooleanField(
        default=True,
        help_text='Enable automatic background sync on feed load',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Instagram Account'
        verbose_name_plural = 'Instagram Accounts'

    def __str__(self):
        return f'{self.user.username} → @{self.ig_username}'

    @property
    def is_token_expiring_soon(self):
        """Returns True if the token expires within 7 days."""
        if not self.token_expires_at:
            return False
        return self.token_expires_at <= timezone.now() + timezone.timedelta(days=7)

    @property
    def is_token_expired(self):
        """Returns True if the token has already expired."""
        if not self.token_expires_at:
            return False
        return self.token_expires_at <= timezone.now()
