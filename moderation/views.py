from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth.models import User
from .models import Block, Report

@login_required
def toggle_block_user(request, username):
    """AJAX view to block/unblock a user."""
    target_user = get_object_or_404(User, username=username)
    if target_user == request.user:
        return JsonResponse({'success': False, 'error': 'You cannot block yourself.'}, status=400)
        
    block_rel = Block.objects.filter(blocker=request.user, blocked=target_user)
    if block_rel.exists():
        block_rel.delete()
        blocked = False
    else:
        Block.objects.create(blocker=request.user, blocked=target_user)
        
        # Clean up social relationships upon blocking
        from friends.models import Follow, FriendRequest
        Follow.objects.filter(follower=request.user, following=target_user).delete()
        Follow.objects.filter(follower=target_user, following=request.user).delete()
        FriendRequest.objects.filter(
            (Q(sender=request.user) & Q(receiver=target_user)) | 
            (Q(sender=target_user) & Q(receiver=request.user))
        ).delete()
        
        blocked = True
        
    return JsonResponse({'success': True, 'blocked': blocked})

@login_required
def blocked_list(request):
    """List of users blocked by the current user."""
    blocks = Block.objects.filter(blocker=request.user).select_related('blocked', 'blocked__userprofile')
    blocked_users = [b.blocked for b in blocks]
    return render(request, 'moderation/blocked_list.html', {'blocked_users': blocked_users})

@login_required
def report_content(request):
    """AJAX view to submit a moderation report for a post, comment, user, or reel."""
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        content_id = request.POST.get('content_id')
        reason = request.POST.get('reason', '').strip()
        
        if report_type not in ['post', 'comment', 'user', 'reel']:
            return JsonResponse({'success': False, 'error': 'Invalid report type.'}, status=400)
        if not content_id:
            return JsonResponse({'success': False, 'error': 'Content ID is required.'}, status=400)
        if not reason:
            return JsonResponse({'success': False, 'error': 'Please provide a reason for the report.'}, status=400)
            
        report = Report.objects.create(
            reporter=request.user,
            report_type=report_type,
            content_id=content_id,
            reason=reason
        )
        
        return JsonResponse({
            'success': True, 
            'message': 'Report submitted successfully. Our team will review this content shortly.'
        })
        
    return JsonResponse({'success': False, 'error': 'Method not allowed.'}, status=405)
