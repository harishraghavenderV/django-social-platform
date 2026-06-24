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
from .badge_engine import check_badges
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

