from .models_badges import Badge, UserBadge
from .models_activity import ActivityLog


# Badge criteria definitions
# format: { criteria_key: { check_fn, auto_create_badge_kwargs } }

BADGE_DEFINITIONS = {
    'first_post': {
        'name': 'First Post',
        'icon': 'bi-pencil-square',
        'description': 'Published your first post!',
        'color': '#6366f1',
        'check': lambda user: user.posts.exists(),
    },
    'posts_10': {
        'name': 'Prolific Writer',
        'icon': 'bi-journal-richtext',
        'description': 'Published 10 posts',
        'color': '#3b82f6',
        'check': lambda user: user.posts.count() >= 10,
    },
    'posts_50': {
        'name': 'Content Machine',
        'icon': 'bi-file-earmark-text-fill',
        'description': 'Published 50 posts',
        'color': '#8b5cf6',
        'check': lambda user: user.posts.count() >= 50,
    },
    'followers_10': {
        'name': 'Rising Star',
        'icon': 'bi-star-fill',
        'description': 'Gained 10 followers',
        'color': '#f59e0b',
        'check': lambda user: user.followers.count() >= 10,
    },
    'followers_100': {
        'name': 'Influencer',
        'icon': 'bi-trophy-fill',
        'description': 'Gained 100 followers',
        'color': '#eab308',
        'check': lambda user: user.followers.count() >= 100,
    },
    'followers_1000': {
        'name': 'Celebrity',
        'icon': 'bi-gem',
        'description': 'Gained 1000 followers',
        'color': '#ec4899',
        'check': lambda user: user.followers.count() >= 1000,
    },
    'first_reel': {
        'name': 'Reel Creator',
        'icon': 'bi-camera-reels-fill',
        'description': 'Published your first reel!',
        'color': '#ec4899',
        'check': lambda user: hasattr(user, 'reels') and user.reels.exists(),
    },
    'first_story': {
        'name': 'Storyteller',
        'icon': 'bi-circle-fill',
        'description': 'Published your first story!',
        'color': '#f97316',
        'check': lambda user: hasattr(user, 'stories') and user.stories.exists(),
    },
    'social_butterfly': {
        'name': 'Social Butterfly',
        'icon': 'bi-people-fill',
        'description': 'Made 5 friends',
        'color': '#10b981',
        'check': lambda user: _friend_count(user) >= 5,
    },
    'early_adopter': {
        'name': 'Early Adopter',
        'icon': 'bi-lightning-charge-fill',
        'description': 'One of the first 100 users!',
        'color': '#14b8a6',
        'check': lambda user: user.id <= 100,
    },
}


def _friend_count(user):
    """Count accepted friendships for a user."""
    from friends.models import FriendRequest
    from django.db.models import Q
    return FriendRequest.objects.filter(
        (Q(sender=user) | Q(receiver=user)),
        status='accepted'
    ).count()


def check_badges(user):
    """Evaluate all badge criteria for a user and award any newly earned badges.
    Returns a list of newly awarded Badge instances.
    """
    newly_earned = []

    for criteria_key, definition in BADGE_DEFINITIONS.items():
        # Skip if already earned
        if UserBadge.objects.filter(
            user=user,
            badge__criteria=criteria_key
        ).exists():
            continue

        # Evaluate the check
        try:
            if definition['check'](user):
                badge, _ = Badge.objects.get_or_create(
                    criteria=criteria_key,
                    defaults={
                        'name': definition['name'],
                        'icon': definition['icon'],
                        'description': definition['description'],
                        'color': definition['color'],
                    }
                )
                UserBadge.objects.create(user=user, badge=badge)
                newly_earned.append(badge)

                # Log the achievement
                ActivityLog.objects.create(
                    user=user,
                    action_type='badge_earned',
                    description=f'Earned the "{badge.name}" badge',
                    target_type='Badge',
                    target_id=badge.id,
                )
        except Exception:
            continue

    return newly_earned
