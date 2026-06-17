from django import template
from django.db import models
from moderation.models import Block

register = template.Library()

@register.simple_tag
def is_blocked(user1, user2):
    """Return True if user1 has blocked user2 or user2 has blocked user1."""
    if not user1 or not user2 or user1.is_anonymous or user2.is_anonymous:
        return False
    return Block.objects.filter(
        (models.Q(blocker=user1) & models.Q(blocked=user2)) |
        (models.Q(blocker=user2) & models.Q(blocked=user1))
    ).exists()
