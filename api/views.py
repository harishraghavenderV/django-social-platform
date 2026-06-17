from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from posts.models import Post, Reaction
from users.models import UserProfile
from notifications.models import Notification
from friends.models import Follow, FriendRequest
from .serializers import (
    PostSerializer, CommentSerializer, UserProfileSerializer,
    NotificationSerializer, FriendRequestSerializer,
)


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        following_ids = Follow.objects.filter(follower=self.request.user).values_list('following_id', flat=True)
        return Post.objects.filter(
            Q(author=self.request.user) | Q(author_id__in=following_ids)
        ).distinct().order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'])
    def react(self, request, pk=None):
        post = self.get_object()
        user = request.user
        reaction_type = request.data.get('reaction_type', 'like')

        existing = Reaction.objects.filter(user=user, post=post).first()
        if existing:
            if existing.reaction_type == reaction_type:
                existing.delete()
                return Response({
                    'reacted': False,
                    'reaction_count': post.reaction_count(),
                    'reactions_summary': post.reactions_summary(),
                })
            else:
                existing.reaction_type = reaction_type
                existing.save()
        else:
            Reaction.objects.create(user=user, post=post, reaction_type=reaction_type)
            if post.author != user:
                Notification.objects.create(
                    recipient=post.author,
                    sender=user,
                    notification_type='like',
                    post=post,
                )

        return Response({
            'reacted': True,
            'reaction_type': reaction_type,
            'reaction_count': post.reaction_count(),
            'reactions_summary': post.reactions_summary(),
        })

    @action(detail=True, methods=['post'])
    def bookmark(self, request, pk=None):
        post = self.get_object()
        if post.bookmarks.filter(id=request.user.id).exists():
            post.bookmarks.remove(request.user)
            return Response({'bookmarked': False})
        else:
            post.bookmarks.add(request.user)
            return Response({'bookmarked': True})

    @action(detail=True, methods=['post'])
    def comment(self, request, pk=None):
        post = self.get_object()
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user, post=post)
            if post.author != request.user:
                Notification.objects.create(
                    recipient=post.author,
                    sender=request.user,
                    notification_type='comment',
                    post=post,
                )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'user__username'

    @action(detail=True, methods=['post'], url_path='follow')
    def follow(self, request, user__username=None):
        profile = self.get_object()
        user_to_follow = profile.user
        if user_to_follow == request.user:
            return Response({'detail': 'You cannot follow yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        follow_rel = Follow.objects.filter(follower=request.user, following=user_to_follow)
        if follow_rel.exists():
            follow_rel.delete()
            followed = False
        else:
            Follow.objects.create(follower=request.user, following=user_to_follow)
            followed = True
            Notification.objects.create(
                recipient=user_to_follow,
                sender=request.user,
                notification_type='follow',
            )
        return Response({'followed': followed}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='send-friend-request')
    def send_friend_request(self, request, user__username=None):
        profile = self.get_object()
        receiver = profile.user
        if receiver == request.user:
            return Response({'detail': 'You cannot send a friend request to yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        existing = FriendRequest.objects.filter(
            (Q(sender=request.user, receiver=receiver) | Q(sender=receiver, receiver=request.user))
        ).first()

        if existing:
            return Response({'detail': 'Friend request relationship already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        friend_req = FriendRequest.objects.create(sender=request.user, receiver=receiver, status='pending')
        Notification.objects.create(
            recipient=receiver,
            sender=request.user,
            notification_type='friend_request',
        )
        serializer = FriendRequestSerializer(friend_req)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return Response({'status': 'all notifications marked as read'})

    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'notification marked as read'})


class FriendRequestViewSet(viewsets.ModelViewSet):
    serializer_class = FriendRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FriendRequest.objects.filter(
            Q(sender=self.request.user) | Q(receiver=self.request.user)
        ).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        friend_req = get_object_or_404(FriendRequest, id=pk, receiver=request.user)
        if friend_req.status != 'pending':
            return Response({'detail': 'Friend request is not pending.'}, status=status.HTTP_400_BAD_REQUEST)
        friend_req.status = 'accepted'
        friend_req.save()

        Follow.objects.get_or_create(follower=request.user, following=friend_req.sender)
        Follow.objects.get_or_create(follower=friend_req.sender, following=request.user)

        Notification.objects.create(
            recipient=friend_req.sender,
            sender=request.user,
            notification_type='friend_accept',
        )
        return Response({'status': 'friend request accepted'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        friend_req = get_object_or_404(FriendRequest, id=pk, receiver=request.user)
        friend_req.delete()
        return Response({'status': 'friend request declined'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        friend_req = get_object_or_404(FriendRequest, id=pk, sender=request.user)
        friend_req.delete()
        return Response({'status': 'friend request cancelled'}, status=status.HTTP_200_OK)
