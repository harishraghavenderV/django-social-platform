from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import Reel, ReelComment

from friends.models import Follow

@login_required
def reels_feed(request):
    """Infinite scroll vertical reel viewer."""
    reels_list = Reel.objects.exclude(author_id__in=request.all_blocked_ids).order_by('-created_at')
    
    # Check for AJAX request
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == 'true'
    
    paginator = Paginator(reels_list, 5)  # 5 reels per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    following_ids = set(Follow.objects.filter(follower=request.user).values_list('following_id', flat=True))
    
    for reel in page_obj:
        reel.is_liked = reel.likes.filter(id=request.user.id).exists()
        reel.is_following = reel.author.id in following_ids or reel.author == request.user
        
    if is_ajax:
        data = []
        for reel in page_obj:
            avatar_url = reel.author.userprofile.profile_picture.url if (
                hasattr(reel.author, 'userprofile') and reel.author.userprofile.profile_picture
            ) else '/static/images/default-avatar.png'
            
            data.append({
                'id': reel.id,
                'video_url': reel.video.url,
                'caption': reel.caption,
                'author_id': reel.author.id,
                'author_username': reel.author.username,
                'author_avatar': avatar_url,
                'like_count': reel.like_count(),
                'comment_count': reel.comment_count(),
                'is_liked': reel.is_liked,
                'is_following': reel.author.id in following_ids or reel.author == request.user,
                'created_at': reel.created_at.strftime('%b %d, %Y'),
            })
        return JsonResponse({
            'reels': data,
            'has_next': page_obj.has_next(),
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
        })
        
    return render(request, 'reels/feed.html', {
        'reels': page_obj,
    })

@login_required
def create_reel(request):
    """Upload vertical short-form video."""
    if request.method == 'POST':
        video = request.FILES.get('video')
        caption = request.POST.get('caption', '')
        if video:
            reel = Reel.objects.create(
                author=request.user,
                video=video,
                caption=caption
            )
            return redirect('reels:feed')
    return render(request, 'reels/create.html')

@login_required
def reel_detail(request, pk):
    """View a single reel with details and comments."""
    reel = get_object_or_404(Reel, pk=pk)
    # Increment views
    reel.view_count += 1
    reel.save(update_fields=['view_count'])
    
    reel.is_liked = reel.likes.filter(id=request.user.id).exists()
    
    following_ids = set(Follow.objects.filter(follower=request.user).values_list('following_id', flat=True))
    reel.is_following = reel.author.id in following_ids or reel.author == request.user
    
    comments = reel.reel_comments.all().select_related('author', 'author__userprofile')
    
    return render(request, 'reels/detail.html', {
        'reel': reel,
        'comments': comments,
    })

@login_required
def reel_like(request, pk):
    """AJAX like/unlike toggle for reels."""
    reel = get_object_or_404(Reel, pk=pk)
    if reel.likes.filter(id=request.user.id).exists():
        reel.likes.remove(request.user)
        liked = False
    else:
        reel.likes.add(request.user)
        liked = True
        
    return JsonResponse({
        'liked': liked,
        'like_count': reel.like_count(),
    })

@login_required
def reel_comment(request, pk):
    """AJAX comment creation for reels."""
    reel = get_object_or_404(Reel, pk=pk)
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            comment = ReelComment.objects.create(
                reel=reel,
                author=request.user,
                content=content
            )
            # If AJAX
            is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == 'true'
            if is_ajax:
                avatar_url = request.user.userprofile.profile_picture.url if (
                    hasattr(request.user, 'userprofile') and request.user.userprofile.profile_picture
                ) else '/static/images/default-avatar.png'
                
                return JsonResponse({
                    'success': True,
                    'comment_id': comment.id,
                    'author_username': comment.author.username,
                    'author_avatar': avatar_url,
                    'content': comment.content,
                    'created_at': comment.created_at.strftime('%b %d, %Y'),
                    'comment_count': reel.comment_count(),
                })
            return redirect('reels:detail', pk=reel.pk)
            
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)
