from django.db import models
from django.contrib.auth.models import User


class Badge(models.Model):
    """Achievements that users can earn through platform activity."""

    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(
        max_length=50,
        help_text='Bootstrap icon class (e.g. bi-star-fill)'
    )
    description = models.TextField()
    criteria = models.CharField(
        max_length=200,
        help_text='Short machine-readable criteria key (e.g. posts_10, followers_100)'
    )
    color = models.CharField(
        max_length=7,
        default='#6366f1',
        help_text='Hex color for badge display'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    """Tracks which badges a user has earned."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='badges'
    )
    badge = models.ForeignKey(
        Badge, on_delete=models.CASCADE, related_name='awards'
    )
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'badge')
        ordering = ['-earned_at']

    def __str__(self):
        return f'{self.user.username} earned {self.badge.name}'
