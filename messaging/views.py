from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Max
from .models import Conversation, Message


@login_required
def inbox(request):
    conversations = Conversation.objects.filter(
        participants=request.user
    ).annotate(
        last_msg_time=Max('messages__created_at')
    ).order_by('-last_msg_time')

    conversation_data = []
    for convo in conversations:
        other_user = convo.participants.exclude(id=request.user.id).first()
        if other_user and hasattr(request, 'all_blocked_ids') and other_user.id in request.all_blocked_ids:
            continue
        last_msg = convo.last_message()
        unread = convo.unread_count_for(request.user)
        conversation_data.append({
            'conversation': convo,
            'other_user': other_user,
            'last_message': last_msg,
            'unread_count': unread,
        })

    return render(request, 'messaging/inbox.html', {
        'conversations': conversation_data,
    })


@login_required
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)

    if not conversation.participants.filter(id=request.user.id).exists():
        return redirect('inbox')

    # Mark unread messages as read
    conversation.messages.filter(is_read=False).exclude(
        sender=request.user
    ).update(is_read=True)

    messages = conversation.messages.all()
    other_user = conversation.participants.exclude(id=request.user.id).first()
    if other_user and hasattr(request, 'all_blocked_ids') and other_user.id in request.all_blocked_ids:
        return redirect('inbox')

    return render(request, 'messaging/conversation.html', {
        'conversation': conversation,
        'messages': messages,
        'other_user': other_user,
    })


@login_required
def start_conversation(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    if other_user == request.user or (hasattr(request, 'all_blocked_ids') and other_user.id in request.all_blocked_ids):
        return redirect('inbox')

    # Check if a conversation already exists between these two users
    conversations = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=other_user
    )

    # Filter to only 1-on-1 conversations (exactly 2 participants)
    for convo in conversations:
        if convo.participants.count() == 2:
            return redirect('conversation_detail', conversation_id=convo.id)

    # Create new conversation
    conversation = Conversation.objects.create()
    conversation.participants.add(request.user, other_user)

    return redirect('conversation_detail', conversation_id=conversation.id)


@login_required
def send_message(request, conversation_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    conversation = get_object_or_404(Conversation, id=conversation_id)
    if not conversation.participants.filter(id=request.user.id).exists():
        return JsonResponse({'error': 'Forbidden'}, status=403)

    other_user = conversation.participants.exclude(id=request.user.id).first()
    if other_user and hasattr(request, 'all_blocked_ids') and other_user.id in request.all_blocked_ids:
        return JsonResponse({'error': 'You cannot send messages to a blocked user.'}, status=403)

    content = request.POST.get('content', '').strip()
    image = request.FILES.get('image')

    if not content and not image:
        return JsonResponse({'error': 'Empty message'}, status=400)

    message = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=content,
        image=image,
    )

    # Update conversation timestamp
    conversation.save()

    # Send via WebSocket if channel layer is available
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'chat_{conversation_id}',
                {
                    'type': 'chat_message',
                    'message': {
                        'id': message.id,
                        'sender': message.sender.username,
                        'sender_id': message.sender.id,
                        'content': message.content,
                        'image_url': message.image.url if message.image else None,
                        'created_at': message.created_at.strftime('%b %d, %I:%M %p'),
                    }
                }
            )
    except Exception:
        pass

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'id': message.id,
            'sender': message.sender.username,
            'sender_id': message.sender.id,
            'content': message.content,
            'image_url': message.image.url if message.image else None,
            'created_at': message.created_at.strftime('%b %d, %I:%M %p'),
        })

    return redirect('conversation_detail', conversation_id=conversation_id)


@login_required
def unread_messages_count(request):
    conversations = Conversation.objects.filter(participants=request.user)
    total = 0
    for convo in conversations:
        total += convo.unread_count_for(request.user)
    return JsonResponse({'unread_count': total})
