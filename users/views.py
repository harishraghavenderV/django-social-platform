import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib import messages
from .forms import RegisterForm, UserForm, UserProfileForm
from .models import UserProfile
from .models_badges import UserBadge
from .models_activity import ActivityLog
from .models_instagram import InstagramAccount
from .badge_engine import check_badges
from . import instagram_service
from friends.models import FriendRequest, Follow
from posts.models import Post
from django.db.models import Q

logger = logging.getLogger(__name__)



def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect("home")
    else:
        form = RegisterForm()
    return render(request, "users/register.html", {"form": form})


@login_required
def profile_view(request, username):
    view_user = get_object_or_404(User, username=username)
    if hasattr(request, 'all_blocked_ids') and view_user.id in request.all_blocked_ids:
        from django.http import Http404
        raise Http404("Profile not found or blocked.")
        
    profile = get_object_or_404(UserProfile, user=view_user)
    posts = Post.objects.filter(
        Q(author=view_user) | Q(co_authors=view_user)
    ).distinct().order_by('-created_at')

    
    # Check friendship status
    friend_status = 'none'
    friend_request = None
    
    if request.user != view_user:
        # Check if they are friends
        is_friend = FriendRequest.objects.filter(
            (Q(sender=request.user, receiver=view_user) | Q(sender=view_user, receiver=request.user)),
            status='accepted'
        ).exists()
        
        if is_friend:
            friend_status = 'friends'
        else:
            # Check outgoing request
            outgoing = FriendRequest.objects.filter(sender=request.user, receiver=view_user, status='pending').first()
            if outgoing:
                friend_status = 'sent'
                friend_request = outgoing
            else:
                # Check incoming request
                incoming = FriendRequest.objects.filter(sender=view_user, receiver=request.user, status='pending').first()
                if incoming:
                    friend_status = 'received'
                    friend_request = incoming
                    
    # Check follow status
    is_following = Follow.objects.filter(follower=request.user, following=view_user).exists() if request.user.is_authenticated else False
    
    # Stats
    followers_count = Follow.objects.filter(following=view_user).count()
    following_count = Follow.objects.filter(follower=view_user).count()
    posts_count = posts.count()
    
    # Badges
    user_badges = UserBadge.objects.filter(user=view_user).select_related('badge')

    # Check for new badges (only for the profile owner viewing their own profile)
    if request.user == view_user:
        check_badges(view_user)

    # Activity tab
    tab = request.GET.get('tab', 'posts')
    activities = []
    if tab == 'activity':
        activities = ActivityLog.objects.filter(user=view_user)[:50]

    context = {
        'view_user': view_user,
        'profile': profile,
        'posts': posts,
        'friend_status': friend_status,
        'friend_request': friend_request,
        'is_following': is_following,
        'followers_count': followers_count,
        'following_count': following_count,
        'posts_count': posts_count,
        'user_badges': user_badges,
        'activities': activities,
        'active_tab': tab,
        'interest_tags_list': [t.strip() for t in profile.interest_tags.split(',') if t.strip()] if profile.interest_tags else [],
    }
    return render(request, 'users/profile.html', context)



@login_required
def profile_edit(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=request.user.userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()

            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action_type='profile_updated',
                description='Updated their profile',
                target_type='User',
                target_id=request.user.id,
            )

            return redirect('profile', username=request.user.username)
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=request.user.userprofile)
        
    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }
    return render(request, 'users/profile_edit.html', context)


@login_required
def toggle_theme(request):
    """AJAX endpoint to toggle dark/light theme."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    profile = request.user.userprofile
    new_theme = 'light' if profile.theme == 'dark' else 'dark'
    profile.theme = new_theme
    profile.save(update_fields=['theme'])

    return JsonResponse({'theme': new_theme})


@login_required
def notification_preferences(request):
    """View/update notification preferences."""
    profile = request.user.userprofile

    if request.method == 'POST':
        prefs = {}
        for key in UserProfile.DEFAULT_NOTIFICATION_PREFS:
            prefs[key] = request.POST.get(f'pref_{key}') == 'on'
        profile.notification_prefs = prefs
        profile.save(update_fields=['notification_prefs'])
        return redirect('notification_prefs')

    # Ensure prefs dict has all keys
    current_prefs = profile.notification_prefs or {}
    for key, default in UserProfile.DEFAULT_NOTIFICATION_PREFS.items():
        current_prefs.setdefault(key, default)

    context = {
        'prefs': current_prefs,
    }
    return render(request, 'users/notification_prefs.html', context)


@login_required
def activity_log_view(request):
    """Paginated activity log for the current user."""
    logs = ActivityLog.objects.filter(user=request.user)
    paginator = Paginator(logs, 30)
    page = paginator.get_page(request.GET.get('page', 1))

    context = {
        'page_obj': page,
    }
    return render(request, 'users/activity_log.html', context)


# ---------------------------------------------------------------------------
# Instagram Integration via Instagrapi
# ---------------------------------------------------------------------------

@login_required
def instagram_connect(request):
    """
    Connect the platform's Instagram account (configured in .env).
    Uses Instagrapi to verify the credentials and fetch account info.
    No Meta Developer App or OAuth redirect needed.
    """
    from django.conf import settings

    username = getattr(settings, 'INSTAGRAM_USERNAME', '')
    password = getattr(settings, 'INSTAGRAM_PASSWORD', '')

    if not username or username.startswith('your_'):
        messages.error(
            request,
            '⚠️ Instagram credentials not configured. '
            'Add INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD to your .env file.'
        )
        return redirect('profile_edit')

    try:
        # Verify login and get account info
        info = instagram_service.get_connection_info()
        ig_username = info['username']

        # Save/update the InstagramAccount record
        account, created = InstagramAccount.objects.update_or_create(
            user=request.user,
            defaults={
                'ig_user_id': ig_username,   # use username as ID for Instagrapi
                'ig_username': ig_username,
                'access_token': 'instagrapi_session',  # session file handles auth
                'token_expires_at': None,               # no token expiry with sessions
                'is_active': True,
            }
        )

        action = 'connected' if created else 'reconnected'
        messages.success(
            request,
            f'✅ Instagram @{ig_username} {action}! '
            f'{info["follower_count"]:,} followers · {info["media_count"]:,} posts.'
        )

        # Trigger an initial sync immediately
        _sync_instagram_account(request.user, account)

    except instagram_service.InstagramAPIError as e:
        messages.error(request, f'Instagram connection failed: {e}')
    except Exception as e:
        messages.error(request, f'Unexpected error: {e}')

    return redirect('profile_edit')


@login_required
def instagram_callback(request):
    """
    Legacy callback endpoint (kept for URL compatibility).
    Instagrapi doesn't use OAuth callbacks — redirect to connect.
    """
    return redirect('instagram_connect')


@login_required
def instagram_disconnect(request):
    """Remove the connected Instagram account."""
    if request.method != 'POST':
        return redirect('profile_edit')

    try:
        account = request.user.instagram_account
        ig_username = account.ig_username
        account.delete()
        messages.success(request, f'Instagram @{ig_username} disconnected.')
    except InstagramAccount.DoesNotExist:
        messages.info(request, 'No Instagram account was connected.')

    return redirect('profile_edit')


@login_required
def instagram_sync_now(request):
    """Manual one-click sync of Instagram media into the ConnectSphere feed."""
    if request.method != 'POST':
        return redirect('profile_edit')

    try:
        account = request.user.instagram_account
        if not account.is_active or account.is_token_expired:
            messages.error(request, 'Your Instagram token has expired. Please reconnect your account.')
            return redirect('profile_edit')

        synced = _sync_instagram_account(request.user, account)
        messages.success(request, f'✅ Synced {synced} new post(s) from @{account.ig_username}.')
    except InstagramAccount.DoesNotExist:
        messages.error(request, 'No Instagram account connected. Please connect first.')

    return redirect('profile_edit')

def _sync_instagram_account(user, account):
    """
    Internal helper: fetch latest Instagram media via Instagrapi and create Post objects.
    Returns the count of newly created posts.
    """
    from django.utils import timezone as tz

    try:
        # Instagrapi: fetch by username (ig_username stored as ig_user_id too)
        media_items = instagram_service.fetch_user_media(account.ig_username)
    except instagram_service.InstagramAPIError as exc:
        account.is_active = False
        account.save(update_fields=['is_active'])
        raise exc

    created_count = 0

    for item in media_items:
        permalink = item.get('permalink', '')
        media_type = item.get('media_type', 'IMAGE')
        caption = item.get('caption', '') or ''
        # Instagrapi returns 'url' for the CDN media link
        media_url = item.get('url') or item.get('thumbnail_url', '')

        # Skip if we already imported this permalink
        if Post.objects.filter(instagram_url=permalink).exists():
            continue

        post = Post.objects.create(
            author=user,
            content=caption[:500],
            instagram_url=permalink,
        )

        # Download and store the media file locally
        if media_url:
            ext = 'jpg' if media_type != 'VIDEO' else 'mp4'
            filename = f'ig_{item["id"]}.{ext}'
            file_content = instagram_service.download_media_to_file(media_url, filename)
            if file_content:
                post.image.save(filename, file_content, save=True)

        # Extract hashtags from caption
        from posts.views import apply_hashtags
        apply_hashtags(post)

        # Log activity
        ActivityLog.objects.create(
            user=user,
            action_type='post_created',
            description=f'Synced from Instagram @{account.ig_username}',
            target_type='Post',
            target_id=post.id,
        )

        # Broadcast via WebSocket
        try:
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer
            from django.template.loader import render_to_string
            
            post_html = render_to_string('posts/_post_card_fragment.html', {
                'posts': [post],
                'user': user,
                'user_reactions': {},
                'bookmarked_ids': set(),
            })
            
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'posts_feed',
                {
                    'type': 'new_post',
                    'post_html': post_html,
                    'author_username': user.username
                }
            )
        except Exception:
            logger.exception('Failed to broadcast synced Instagram post %s', post.id)

        created_count += 1

    # Update last synced timestamp
    account.last_synced = tz.now()
    account.save(update_fields=['last_synced'])

    return created_count


@login_required
def instagram_toggle_autosync(request):
    """AJAX POST to toggle auto_sync parameter on the Instagram account connection."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        account = request.user.instagram_account
        account.auto_sync = not account.auto_sync
        account.save(update_fields=['auto_sync'])
        return JsonResponse({'success': True, 'auto_sync': account.auto_sync})
    except InstagramAccount.DoesNotExist:
        return JsonResponse({'error': 'No Instagram account connected'}, status=400)