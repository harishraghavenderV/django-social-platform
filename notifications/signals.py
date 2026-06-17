from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notification


@receiver(post_save, sender=Notification)
def broadcast_notification(sender, instance, created, **kwargs):
    if not created:
        return

    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        channel_layer = get_channel_layer()
        if channel_layer is None:
            return

        group_name = f'notifications_{instance.recipient.id}'
        notification_data = {
            'id': instance.id,
            'sender': instance.sender.username,
            'sender_avatar': instance.sender.userprofile.profile_picture.url if instance.sender.userprofile.profile_picture else None,
            'type': instance.notification_type,
            'message': _get_notification_message(instance),
            'post_id': instance.post.id if instance.post else None,
            'is_read': instance.is_read,
            'created_at': instance.created_at.strftime('%b %d, %I:%M %p'),
        }

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'send_notification',
                'notification': notification_data,
            }
        )
    except Exception:
        pass


def _get_notification_message(notification):
    messages = {
        'like': f'{notification.sender.username} liked your post',
        'comment': f'{notification.sender.username} commented on your post',
        'friend_request': f'{notification.sender.username} sent you a friend request',
        'friend_accept': f'{notification.sender.username} accepted your friend request',
        'follow': f'{notification.sender.username} started following you',
    }
    return messages.get(notification.notification_type, 'New notification')
