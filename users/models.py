from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):

    THEME_CHOICES = (
        ('dark', 'Dark'),
        ('light', 'Light'),
    )

    DEFAULT_NOTIFICATION_PREFS = {
        'likes': True,
        'comments': True,
        'follows': True,
        'messages': True,
        'mentions': True,
        'events': True,
        'friend_requests': True,
    }

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    bio = models.TextField(
        max_length=500,
        blank=True
    )

    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True
    )

    cover_photo = models.ImageField(
        upload_to='cover_photos/',
        blank=True,
        null=True
    )

    location = models.CharField(
        max_length=100,
        blank=True
    )

    website = models.URLField(
        blank=True
    )

    joined_date = models.DateTimeField(
        auto_now_add=True
    )

    is_verified = models.BooleanField(
        default=False,
        help_text='Verified badge status'
    )

    theme = models.CharField(
        max_length=10,
        choices=THEME_CHOICES,
        default='dark'
    )

    notification_prefs = models.JSONField(
        default=dict,
        blank=True,
        help_text='Per-type notification preferences'
    )

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def save(self, *args, **kwargs):
        if not self.notification_prefs:
            self.notification_prefs = self.DEFAULT_NOTIFICATION_PREFS.copy()
        
        from utils.image_optimizer import optimize_image
        if self.pk:
            try:
                orig = UserProfile.objects.get(pk=self.pk)
                if orig.profile_picture != self.profile_picture and self.profile_picture:
                    optimize_image(self.profile_picture)
                if orig.cover_photo != self.cover_photo and self.cover_photo:
                    optimize_image(self.cover_photo)
            except UserProfile.DoesNotExist:
                if self.profile_picture:
                    optimize_image(self.profile_picture)
                if self.cover_photo:
                    optimize_image(self.cover_photo)
        else:
            if self.profile_picture:
                optimize_image(self.profile_picture)
            if self.cover_photo:
                optimize_image(self.cover_photo)

        super().save(*args, **kwargs)
