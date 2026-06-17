import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Count
from django.contrib.auth.models import User
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from datetime import timedelta
from .models import Post, Comment, Share, HashTag, Reaction
from .poll_models import Poll, PollOption, PollVote
from friends.models import Follow
from notifications.models import Notification


def extract_hashtags(text):
    """Extract hashtags from text and return list of tag names (lowercase)."""
    return list(set(re.findall(r'#(\w+)', text.lower())))


def apply_hashtags(post):
    """Parse hashtags from post content and associate them."""
    tag_names = extract_hashtags(post.content)
    post.hashtags.clear()
    for name in tag_names:
        tag, _ = HashTag.objects.get_or_create(name=name)
        post.hashtags.add(tag)


def home(request):
    if request.user.is_authenticated:
        following_ids = Follow.objects.filter(
            follower=request.user
        ).values_list('following_id', flat=True)

        posts = Post.objects.filter(
            (Q(author=request.user) | Q(author_id__in=following_ids)),
            group__isnull=True,
        ).exclude(author_id__in=request.all_blocked_ids).select_related('poll').prefetch_related('poll__options').distinct().order_by('-created_at')

        # Get shares from self and followed users
        shares = Share.objects.filter(
            Q(user=request.user) | Q(user_id__in=following_ids)
        ).exclude(user_id__in=request.all_blocked_ids).exclude(original_post__author_id__in=request.all_blocked_ids).select_related('user', 'original_post', 'original_post__author').order_by('-created_at')

        suggestions = User.objects.exclude(
            id=request.user.id
        ).exclude(id__in=following_ids).exclude(id__in=request.all_blocked_ids)[:5]

        unread_notifications_count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()

        # Build a dict of user reactions for each post: {post_id: 'reaction_type'}
        user_reactions = {}
        if posts:
            post_ids = [p.id for p in posts]
            for r in Reaction.objects.filter(user=request.user, post_id__in=post_ids):
                user_reactions[r.post_id] = r.reaction_type

        # Bookmarked post IDs
        bookmarked_ids = set(
            request.user.bookmarked_posts.values_list('id', flat=True)
        )

        # Build a dict of user poll votes: {poll_id: option_id}
        user_votes = {}
        if posts:
            poll_ids = [p.poll.id for p in posts if hasattr(p, 'poll')]
            if poll_ids:
                for v in PollVote.objects.filter(user=request.user, poll_id__in=poll_ids):
                    user_votes[v.poll_id] = v.option_id

        context = {
            'posts': posts,
            'shares': shares,
            'suggestions': suggestions,
            'unread_notifications_count': unread_notifications_count,
            'user_reactions': user_reactions,
            'bookmarked_ids': bookmarked_ids,
            'user_votes': user_votes,
        }
        return render(request, 'posts/home.html', context)
    else:
        return render(request, 'posts/home.html')


@login_required
def post_create(request):
    if request.method == 'POST':
        content = request.POST.get('content')
        image = request.FILES.get('image')
        if content or image:
            post = Post.objects.create(
                author=request.user,
                content=content or '',
                image=image,
            )
            apply_hashtags(post)
            
            # Broadcast the new post to channels
            try:
                from asgiref.sync import async_to_sync
                from channels.layers import get_channel_layer
                from django.template.loader import render_to_string
                
                post_html = render_to_string('posts/_post_card_fragment.html', {
                    'posts': [post],
                    'user': request.user,
                    'user_reactions': {},
                    'bookmarked_ids': set(),
                }, request=request)
                
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    'posts_feed',
                    {
                        'type': 'new_post',
                        'post_html': post_html,
                        'author_username': request.user.username
                    }
                )
            except:
                pass
    return redirect('home')


@login_required
def post_detail(request, pk):
    post = get_object_or_404(Post.objects.select_related('poll').prefetch_related('poll__options'), pk=pk)
    comments = post.comments.all()
    user_reaction = None
    is_bookmarked = False
    user_vote_option_id = None
    if request.user.is_authenticated:
        reaction = Reaction.objects.filter(user=request.user, post=post).first()
        user_reaction = reaction.reaction_type if reaction else None
        is_bookmarked = post.bookmarks.filter(id=request.user.id).exists()
        if hasattr(post, 'poll'):
            vote = PollVote.objects.filter(user=request.user, poll=post.poll).first()
            user_vote_option_id = vote.option_id if vote else None
            
    return render(request, 'posts/post_detail.html', {
        'post': post,
        'comments': comments,
        'user_reaction': user_reaction,
        'is_bookmarked': is_bookmarked,
        'user_vote_option_id': user_vote_option_id,
    })


@login_required
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user:
        return redirect('post_detail', pk=pk)

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            post.content = content
            post.is_edited = True
            post.save()
            apply_hashtags(post)
        return redirect('post_detail', pk=pk)

    return render(request, 'posts/post_edit.html', {'post': post})


@login_required
def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author == request.user:
        post.delete()
    return redirect('home')


@login_required
def post_react(request, pk):
    """Toggle a reaction on a post. Accepts reaction_type via POST."""
    post = get_object_or_404(Post, pk=pk)
    reaction_type = request.POST.get('reaction_type', 'like')

    existing = Reaction.objects.filter(user=request.user, post=post).first()

    if existing:
        if existing.reaction_type == reaction_type:
            # Same reaction → remove it (un-react)
            existing.delete()
            # Broadcast update
            try:
                from asgiref.sync import async_to_sync
                from channels.layers import get_channel_layer
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    'posts_feed',
                    {
                        'type': 'post_like_update',
                        'post_id': post.id,
                        'like_count': post.reaction_count()
                    }
                )
            except:
                pass
            return JsonResponse({
                'reacted': False,
                'reaction_type': None,
                'reaction_count': post.reaction_count(),
                'reactions_summary': post.reactions_summary(),
            })
        else:
            # Different reaction → update
            existing.reaction_type = reaction_type
            existing.save()
    else:
        # New reaction
        Reaction.objects.create(user=request.user, post=post, reaction_type=reaction_type)
        # Notification
        if post.author != request.user:
            Notification.objects.create(
                recipient=post.author,
                sender=request.user,
                notification_type='like',
                post=post,
            )

    # Broadcast update
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'posts_feed',
            {
                'type': 'post_like_update',
                'post_id': post.id,
                'like_count': post.reaction_count()
            }
        )
    except:
        pass

    return JsonResponse({
        'reacted': True,
        'reaction_type': reaction_type,
        'reaction_count': post.reaction_count(),
        'reactions_summary': post.reactions_summary(),
    })


@login_required
def toggle_bookmark(request, pk):
    """Toggle bookmark on a post."""
    post = get_object_or_404(Post, pk=pk)
    if post.bookmarks.filter(id=request.user.id).exists():
        post.bookmarks.remove(request.user)
        bookmarked = False
    else:
        post.bookmarks.add(request.user)
        bookmarked = True
    return JsonResponse({'bookmarked': bookmarked})


@login_required
def bookmarks_list(request):
    """Show all bookmarked posts."""
    posts = request.user.bookmarked_posts.all().order_by('-created_at')
    return render(request, 'posts/bookmarks.html', {'posts': posts})


@login_required
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            comment = Comment.objects.create(
                post=post,
                author=request.user,
                content=content,
            )
            if post.author != request.user:
                Notification.objects.create(
                    recipient=post.author,
                    sender=request.user,
                    notification_type='comment',
                    post=post,
                )
            # Broadcast the comment to channels
            try:
                from asgiref.sync import async_to_sync
                from channels.layers import get_channel_layer
                from django.template.loader import render_to_string
                
                comment_html = render_to_string('posts/_comment_fragment.html', {'comment': comment}, request=request)
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    'posts_feed',
                    {
                        'type': 'post_comment_update',
                        'post_id': post.id,
                        'comment_count': post.comments.count(),
                        'comment_html': comment_html
                    }
                )
            except:
                pass
    return redirect('post_detail', pk=pk)


@login_required
def post_share(request, pk):
    original_post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        commentary = request.POST.get('content', '')
        Share.objects.create(
            user=request.user,
            original_post=original_post,
            content=commentary,
        )
    return redirect('home')


@login_required
def search(request):
    query = request.GET.get('q', '')
    tab = request.GET.get('tab', 'people')
    sort = request.GET.get('sort', 'recent')
    date_range = request.GET.get('date_range', '')

    users_results = []
    posts_results = []
    hashtag_results = []

    if query:
        # People search
        users_results = User.objects.filter(
            Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)
        ).exclude(id=request.user.id).exclude(
            id__in=request.all_blocked_ids
        ).annotate(follower_count=Count('followers'))

        if sort == 'popular':
            users_results = users_results.order_by('-follower_count')
        else:
            users_results = users_results.order_by('-date_joined')

        # Posts search
        posts_qs = Post.objects.filter(
            Q(content__icontains=query)
        ).exclude(author_id__in=request.all_blocked_ids)

        # Date range filter
        if date_range == 'today':
            posts_qs = posts_qs.filter(created_at__date=timezone.now().date())
        elif date_range == 'week':
            posts_qs = posts_qs.filter(created_at__gte=timezone.now() - timedelta(days=7))
        elif date_range == 'month':
            posts_qs = posts_qs.filter(created_at__gte=timezone.now() - timedelta(days=30))

        if sort == 'popular':
            posts_qs = posts_qs.annotate(
                engagement=Count('reactions') + Count('comments')
            ).order_by('-engagement')
        else:
            posts_qs = posts_qs.order_by('-created_at')

        posts_results = posts_qs[:30]

        # Hashtags search
        hashtag_results = HashTag.objects.filter(
            name__icontains=query.lstrip('#')
        ).annotate(post_count=Count('posts')).order_by('-post_count')[:20]

    context = {
        'query': query,
        'tab': tab,
        'sort': sort,
        'date_range': date_range,
        'users_results': users_results,
        'posts_results': posts_results,
        'hashtag_results': hashtag_results,
        'users_count': len(users_results) if isinstance(users_results, list) else users_results.count(),
        'posts_count': len(posts_results) if isinstance(posts_results, list) else posts_results.count(),
        'hashtags_count': len(hashtag_results) if isinstance(hashtag_results, list) else hashtag_results.count(),
    }
    return render(request, 'posts/search.html', context)


@login_required
def explore(request):
    """Trending posts — most engagement in the last 7 days."""
    week_ago = timezone.now() - timedelta(days=7)

    trending_posts = Post.objects.filter(
        created_at__gte=week_ago,
        group__isnull=True,
    ).annotate(
        engagement=Count('reactions') + Count('comments'),
    ).order_by('-engagement', '-created_at')[:30]

    trending_tags = HashTag.objects.annotate(
        post_count=Count('posts')
    ).order_by('-post_count')[:10]

    # Discover people (users not followed)
    if request.user.is_authenticated:
        following_ids = Follow.objects.filter(
            follower=request.user
        ).values_list('following_id', flat=True)
        discover_users = User.objects.exclude(
            id=request.user.id
        ).exclude(id__in=following_ids).exclude(id__in=request.all_blocked_ids).annotate(
            follower_count=Count('followers')
        ).order_by('-follower_count')[:8]
    else:
        discover_users = []

    return render(request, 'posts/explore.html', {
        'trending_posts': trending_posts,
        'trending_tags': trending_tags,
        'discover_users': discover_users,
    })


@login_required
def hashtag_feed(request, tag):
    hashtag = get_object_or_404(HashTag, name=tag.lower())
    posts = hashtag.posts.all().order_by('-created_at')
    return render(request, 'posts/hashtag_feed.html', {
        'hashtag': hashtag,
        'posts': posts,
    })


@login_required
def create_poll(request):
    """Create a post with an attached poll."""
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        question = request.POST.get('question', '').strip()
        options = request.POST.getlist('options')
        
        # Filter empty options
        options = [opt.strip() for opt in options if opt.strip()]
        
        if question and len(options) >= 2:
            # Create post
            post = Post.objects.create(
                author=request.user,
                content=content or question
            )
            apply_hashtags(post)
            
            # Create poll
            poll = Poll.objects.create(
                post=post,
                question=question
            )
            
            # Create options
            for opt_text in options:
                PollOption.objects.create(poll=poll, text=opt_text)
                
    return redirect('home')


@login_required
def vote_poll(request, pk):
    """AJAX vote on a poll option."""
    poll = get_object_or_404(Poll, pk=pk)
    option_id = request.POST.get('option_id')
    option = get_object_or_404(PollOption, id=option_id, poll=poll)
    
    if poll.expires_at and poll.expires_at < timezone.now():
        return JsonResponse({'success': False, 'error': 'This poll has expired.'}, status=400)
        
    vote, created = PollVote.objects.get_or_create(
        poll=poll,
        user=request.user,
        defaults={'option': option}
    )
    
    if not created:
        return JsonResponse({'success': False, 'error': 'You have already voted in this poll.'}, status=400)
        
    # Recalculate vote counts / update cache
    option.vote_count = option.votes.count()
    option.save(update_fields=['vote_count'])
    
    options_data = []
    total_votes = poll.total_votes()
    for opt in poll.options.all():
        opt.vote_count = opt.votes.count()
        opt.save(update_fields=['vote_count'])
        
        percentage = round((opt.vote_count / total_votes * 100), 1) if total_votes > 0 else 0
        options_data.append({
            'id': opt.id,
            'text': opt.text,
            'votes': opt.vote_count,
            'percentage': percentage
        })
        
    return JsonResponse({
        'success': True,
        'total_votes': total_votes,
        'options': options_data
    })


@login_required
def home_feed_api(request):
    """AJAX endpoint returning paginated post HTML fragments for infinite scroll."""
    page_num = request.GET.get('page', 1)

    following_ids = Follow.objects.filter(
        follower=request.user
    ).values_list('following_id', flat=True)

    posts = Post.objects.filter(
        (Q(author=request.user) | Q(author_id__in=following_ids)),
        group__isnull=True,
    ).exclude(
        author_id__in=request.all_blocked_ids
    ).select_related('poll').prefetch_related('poll__options').distinct().order_by('-created_at')

    paginator = Paginator(posts, 10)
    page = paginator.get_page(page_num)

    # Build user reactions and bookmarks for this page
    user_reactions = {}
    bookmarked_ids = set()
    if page.object_list:
        post_ids = [p.id for p in page.object_list]
        for r in Reaction.objects.filter(user=request.user, post_id__in=post_ids):
            user_reactions[r.post_id] = r.reaction_type
        bookmarked_ids = set(
            request.user.bookmarked_posts.filter(id__in=post_ids).values_list('id', flat=True)
        )

    html = render_to_string('posts/_post_card_fragment.html', {
        'posts': page.object_list,
        'user': request.user,
        'user_reactions': user_reactions,
        'bookmarked_ids': bookmarked_ids,
    }, request=request)

    return JsonResponse({
        'html': html,
        'has_next': page.has_next(),
        'next_page': page.next_page_number() if page.has_next() else None,
    })


@login_required
def import_instagram(request):
    """
    Import an Instagram post by URL.
    Uses the real Instagram oEmbed API for public posts (no user auth needed).
    Falls back to iframe embed if oEmbed is unavailable.
    Broadcasts the new post in real-time via WebSocket.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=400)

    url = request.POST.get('url', '').strip()
    if not url:
        return JsonResponse({'error': 'URL is required'}, status=400)

    import re
    from django.conf import settings
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer
    from users import instagram_service

    # Validate it's an Instagram URL
    match = re.search(r'instagram\.com/(?:p|reel|tv)/([a-zA-Z0-9_-]+)', url)
    if not match:
        return JsonResponse({'error': 'Invalid Instagram URL. Use a post, reel, or TV URL.'}, status=400)

    post_id = match.group(1)
    if '/reel/' in url:
        instagram_url = f'https://www.instagram.com/reel/{post_id}/'
    elif '/tv/' in url:
        instagram_url = f'https://www.instagram.com/tv/{post_id}/'
    else:
        instagram_url = f'https://www.instagram.com/p/{post_id}/'

    # Skip if already imported
    if Post.objects.filter(instagram_url=instagram_url).exists():
        existing = Post.objects.filter(instagram_url=instagram_url).first()
        return JsonResponse({
            'success': True,
            'post_id': existing.id,
            'author': existing.author.username,
            'content': existing.content,
            'instagram_url': existing.instagram_url,
            'already_exists': True,
        })

    # Determine author username from URL keywords
    url_lower = url.lower()
    author_username = 'instagram_creator'
    author_bio = 'Instagram Creator'
    if 'thanthitv' in url_lower:
        author_username, author_bio = 'thanthitv', 'Thanthi TV - Tamil News & Media Group'
    elif 'dhoni' in url_lower or 'msdhoni' in url_lower:
        author_username, author_bio = 'msdhoni', 'M S Dhoni'
    elif 'cristiano' in url_lower or 'ronaldo' in url_lower:
        author_username, author_bio = 'cristiano', 'Cristiano Ronaldo'
    elif 'leomessi' in url_lower or 'messi' in url_lower:
        author_username, author_bio = 'leomessi', 'Leo Messi'
    elif 'virat' in url_lower or 'kohli' in url_lower:
        author_username, author_bio = 'virat.kohli', 'Virat Kohli'

    # Get or create the author
    from django.contrib.auth.models import User
    author, _ = User.objects.get_or_create(
        username=author_username,
        defaults={'email': f'{author_username}@example.com'}
    )
    profile = author.userprofile
    profile.is_verified = True
    profile.bio = author_bio
    profile.save(update_fields=['is_verified', 'bio'])

    # Try real oEmbed API first
    oembed_data = instagram_service.fetch_oembed(instagram_url)
    embed_html = oembed_data.get('html') if oembed_data else None

    # If oEmbed returned an author name, use it as content
    content_text = f'Imported post from @{author_username}.'
    if oembed_data and oembed_data.get('author_name'):
        content_text = f'Post by @{oembed_data["author_name"]} on Instagram.'

    # Create the post — instagram_url drives the embed rendering
    post = Post.objects.create(
        author=author,
        content=content_text,
        instagram_url=instagram_url,
    )
    apply_hashtags(post)
    post.save()

    # Broadcast via WebSocket
    try:
        post_html = render_to_string('posts/_post_card_fragment.html', {
            'posts': [post],
            'user': request.user,
            'user_reactions': {},
            'bookmarked_ids': set(),
        }, request=request)

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'posts_feed',
            {
                'type': 'new_post',
                'post_html': post_html,
                'author_username': author.username,
            }
        )
    except Exception:
        pass

    return JsonResponse({
        'success': True,
        'post_id': post.id,
        'author': author.username,
        'content': post.content,
        'instagram_url': post.instagram_url,
        'oembed_available': embed_html is not None,
        'image_url': post.image.url if post.image else None,
    })