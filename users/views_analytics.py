from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncDate
from datetime import timedelta


@login_required
def profile_analytics(request):
    """Dashboard with engagement analytics for the current user."""
    user = request.user
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)

    # Total stats
    from posts.models import Post, Reaction, Comment
    from friends.models import Follow

    total_posts = Post.objects.filter(author=user).count()
    total_reactions = Reaction.objects.filter(post__author=user).count()
    total_comments = Comment.objects.filter(post__author=user).exclude(author=user).count()
    total_followers = Follow.objects.filter(following=user).count()
    total_following = Follow.objects.filter(follower=user).count()

    # Engagement rate = (total_reactions + total_comments) / total_posts
    engagement_rate = 0
    if total_posts > 0:
        engagement_rate = round(((total_reactions + total_comments) / total_posts) * 100, 1)

    # Follower growth last 30 days (daily counts)
    follower_trend = (
        Follow.objects.filter(following=user, created_at__gte=thirty_days_ago)
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    follower_labels = [entry['day'].strftime('%b %d') for entry in follower_trend]
    follower_data = [entry['count'] for entry in follower_trend]

    # Post engagement (reactions per post, last 10 posts)
    top_posts = (
        Post.objects.filter(author=user)
        .annotate(
            react_count=Count('reactions'),
            comment_count=Count('comments'),
        )
        .order_by('-react_count')[:10]
    )
    post_labels = [f'Post #{p.id}' for p in top_posts]
    reaction_data = [p.react_count for p in top_posts]
    comment_data = [p.comment_count for p in top_posts]

    # Content mix (posts, reels, stories counts)
    reel_count = 0
    story_count = 0
    try:
        from reels.models import Reel
        reel_count = Reel.objects.filter(author=user).count()
    except Exception:
        pass
    try:
        from stories.models import Story
        story_count = Story.objects.filter(author=user).count()
    except Exception:
        pass

    content_mix = {
        'posts': total_posts,
        'reels': reel_count,
        'stories': story_count,
    }

    context = {
        'total_posts': total_posts,
        'total_reactions': total_reactions,
        'total_comments': total_comments,
        'total_followers': total_followers,
        'total_following': total_following,
        'engagement_rate': engagement_rate,
        'follower_labels': follower_labels,
        'follower_data': follower_data,
        'post_labels': post_labels,
        'reaction_data': reaction_data,
        'comment_data': comment_data,
        'content_mix': content_mix,
        'top_posts': top_posts,
    }
    return render(request, 'users/analytics.html', context)


@login_required
def media_gallery(request):
    """Grid of all user's media content."""
    user = request.user

    media_items = []

    # Post images
    from posts.models import Post
    posts_with_images = Post.objects.filter(author=user, image__isnull=False).exclude(image='').order_by('-created_at')
    for post in posts_with_images:
        media_items.append({
            'type': 'post',
            'url': post.image.url,
            'link': f'/post/{post.id}/',
            'date': post.created_at,
            'caption': post.content[:80],
        })

    # Reel thumbnails
    try:
        from reels.models import Reel
        reels = Reel.objects.filter(author=user).order_by('-created_at')
        for reel in reels:
            if reel.thumbnail:
                media_items.append({
                    'type': 'reel',
                    'url': reel.thumbnail.url,
                    'link': f'/reels/{reel.id}/',
                    'date': reel.created_at,
                    'caption': reel.caption[:80] if reel.caption else '',
                })
    except Exception:
        pass

    # Story images
    try:
        from stories.models import Story
        stories = Story.objects.filter(author=user).order_by('-created_at')
        for story in stories:
            if story.image:
                media_items.append({
                    'type': 'story',
                    'url': story.image.url,
                    'link': '#',
                    'date': story.created_at,
                    'caption': story.caption[:80] if hasattr(story, 'caption') and story.caption else '',
                })
    except Exception:
        pass

    # Sort by date
    media_items.sort(key=lambda x: x['date'], reverse=True)

    context = {
        'media_items': media_items,
        'total_count': len(media_items),
    }
    return render(request, 'users/media_gallery.html', context)
