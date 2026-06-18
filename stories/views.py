from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from .models import Story, StoryView
from friends.models import Follow


@login_required
def create_story(request):
    if request.method == 'POST':
        image = request.FILES.get('image')
        caption = request.POST.get('caption', '')
        if image:
            Story.objects.create(
                author=request.user,
                image=image,
                caption=caption,
            )
        return redirect('home')
    return render(request, 'stories/create_story.html')


@login_required
def view_stories(request, user_id):
    story_user = get_object_or_404(User, id=user_id)
    stories = Story.objects.active().filter(author=story_user).order_by('created_at')

    if not stories.exists():
        return redirect('home')

    # Record views for these active stories
    for story in stories:
        StoryView.objects.get_or_create(story=story, viewer=request.user)

    return render(request, 'stories/story_viewer.html', {
        'story_user': story_user,
        'stories': stories,
    })


@login_required
def story_data(request):
    """Return story bar data for the home feed: users with active stories."""
    following_ids = Follow.objects.filter(
        follower=request.user
    ).values_list('following_id', flat=True)

    # Get users with active stories (self + following)
    from django.db.models import Q
    story_users_ids = Story.objects.active().filter(
        Q(author=request.user) | Q(author_id__in=following_ids)
    ).exclude(author_id__in=request.all_blocked_ids).values_list('author_id', flat=True).distinct()

    story_users = User.objects.filter(id__in=story_users_ids)

    data = []
    for u in story_users:
        # Check if user u has any active stories not yet viewed by request.user
        active_stories = Story.objects.active().filter(author=u)
        has_unviewed = active_stories.exclude(views__viewer=request.user).exists()

        data.append({
            'user_id': u.id,
            'username': u.username,
            'avatar_url': u.userprofile.profile_picture.url if u.userprofile.profile_picture else None,
            'has_unviewed': has_unviewed,
        })

    return JsonResponse({'story_users': data})
