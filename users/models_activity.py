from django.db import models
from django.contrib.auth.models import User


class ActivityLog(models.Model):
    """Records user actions for their activity feed."""

    ACTION_TYPES = (
        ('post_created', 'Created a post'),
        ('post_liked', 'Liked a post'),
        ('comment_added', 'Commented on a post'),
        ('follow', 'Followed a user'),
        ('friend_request', 'Sent a friend request'),
        ('friend_accept', 'Accepted a friend request'),
        ('reel_created', 'Created a reel'),
        ('story_created', 'Created a story'),
        ('event_created', 'Created an event'),
        ('event_rsvp', 'RSVPed to an event'),
        ('badge_earned', 'Earned a badge'),
        ('group_joined', 'Joined a group'),
        ('poll_voted', 'Voted on a poll'),
        ('profile_updated', 'Updated their profile'),
    )

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='activity_logs'
    )
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    description = models.TextField()
    target_type = models.CharField(
        max_length=50, blank=True,
        help_text='Model name of the target (e.g. Post, Reel, User)'
    )
    target_id = models.IntegerField(
        null=True, blank=True,
        help_text='PK of the target object'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username}: {self.get_action_type_display()} ({self.created_at})'

    @property
    def icon(self):
        icons = {
            'post_created': 'bi-pencil-square',
            'post_liked': 'bi-heart-fill',
            'comment_added': 'bi-chat-fill',
            'follow': 'bi-person-plus-fill',
            'friend_request': 'bi-person-add',
            'friend_accept': 'bi-people-fill',
            'reel_created': 'bi-camera-reels-fill',
            'story_created': 'bi-circle-fill',
            'event_created': 'bi-calendar-event-fill',
            'event_rsvp': 'bi-calendar-check-fill',
            'badge_earned': 'bi-award-fill',
            'group_joined': 'bi-collection-fill',
            'poll_voted': 'bi-bar-chart-fill',
            'profile_updated': 'bi-gear-fill',
        }
        return icons.get(self.action_type, 'bi-activity')

    @property
    def color(self):
        colors = {
            'post_created': '#6366f1',
            'post_liked': '#f43f5e',
            'comment_added': '#3b82f6',
            'follow': '#10b981',
            'friend_request': '#f59e0b',
            'friend_accept': '#10b981',
            'reel_created': '#ec4899',
            'story_created': '#f97316',
            'event_created': '#8b5cf6',
            'event_rsvp': '#14b8a6',
            'badge_earned': '#eab308',
            'group_joined': '#6366f1',
            'poll_voted': '#06b6d4',
            'profile_updated': '#64748b',
        }
        return colors.get(self.action_type, '#6366f1')
