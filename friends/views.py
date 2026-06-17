from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.models import User
from .models import FriendRequest, Follow
from notifications.models import Notification
from django.db.models import Q

@login_required
def send_friend_request(request, user_id):
    receiver = get_object_or_404(User, id=user_id)
    if receiver != request.user:
        # Check if already exists
        existing = FriendRequest.objects.filter(
            (Q(sender=request.user, receiver=receiver) | Q(sender=receiver, receiver=request.user))
        ).first()
        
        if not existing:
            friend_req = FriendRequest.objects.create(sender=request.user, receiver=receiver, status='pending')
            # Create notification
            Notification.objects.create(
                recipient=receiver,
                sender=request.user,
                notification_type='friend_request'
            )
    return redirect('profile', username=receiver.username)

@login_required
def accept_friend_request(request, request_id):
    friend_req = get_object_or_404(FriendRequest, id=request_id, receiver=request.user)
    friend_req.status = 'accepted'
    friend_req.save()
    
    # Auto follow each other upon accepting a friend request
    Follow.objects.get_or_create(follower=request.user, following=friend_req.sender)
    Follow.objects.get_or_create(follower=friend_req.sender, following=request.user)
    
    # Create notification
    Notification.objects.create(
        recipient=friend_req.sender,
        sender=request.user,
        notification_type='friend_accept'
    )
    return redirect('friends_list')

@login_required
def decline_friend_request(request, request_id):
    friend_req = get_object_or_404(FriendRequest, id=request_id, receiver=request.user)
    friend_req.status = 'declined'
    friend_req.delete() # Or just delete it to allow re-requesting
    return redirect('friends_list')

@login_required
def cancel_friend_request(request, request_id):
    friend_req = get_object_or_404(FriendRequest, id=request_id, sender=request.user)
    friend_req.delete()
    return redirect('profile', username=friend_req.receiver.username)

@login_required
def remove_friend(request, user_id):
    friend = get_object_or_404(User, id=user_id)
    FriendRequest.objects.filter(
        (Q(sender=request.user, receiver=friend) | Q(sender=friend, receiver=request.user)),
        status='accepted'
    ).delete()
    # Optionally unfollow
    Follow.objects.filter(follower=request.user, following=friend).delete()
    Follow.objects.filter(follower=friend, following=request.user).delete()
    return redirect('profile', username=friend.username)

@login_required
def follow_user(request, user_id):
    user_to_follow = get_object_or_404(User, id=user_id)
    if user_to_follow != request.user:
        follow_rel = Follow.objects.filter(follower=request.user, following=user_to_follow)
        followed = False
        if follow_rel.exists():
            follow_rel.delete()
        else:
            Follow.objects.create(follower=request.user, following=user_to_follow)
            followed = True
            # Create notification
            Notification.objects.create(
                recipient=user_to_follow,
                sender=request.user,
                notification_type='follow'
            )
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
            return JsonResponse({'followed': followed})
            
    return redirect('profile', username=user_to_follow.username)

@login_required
def friends_list(request):
    # Received pending requests
    received_requests = FriendRequest.objects.filter(receiver=request.user, status='pending')
    # Sent pending requests
    sent_requests = FriendRequest.objects.filter(sender=request.user, status='pending')
    
    # Friends list (both ways accepted)
    friends_relations = FriendRequest.objects.filter(
        (Q(sender=request.user) | Q(receiver=request.user)),
        status='accepted'
    )
    
    friends = []
    for rel in friends_relations:
        if rel.sender == request.user:
            friends.append(rel.receiver)
        else:
            friends.append(rel.sender)
            
    context = {
        'received_requests': received_requests,
        'sent_requests': sent_requests,
        'friends': friends,
    }
    return render(request, 'friends/friends.html', context)
