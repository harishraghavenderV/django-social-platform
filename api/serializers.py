from rest_framework import serializers
from django.contrib.auth.models import User
from users.models import UserProfile
from posts.models import Post, Comment, Reaction, CommentReaction, Share, PostMedia
from notifications.models import Notification
from friends.models import FriendRequest, Follow
from messaging.models import Message, Conversation


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    is_following = serializers.SerializerMethodField()
    is_follower = serializers.SerializerMethodField()
    is_mutual = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'bio', 'profile_picture', 'cover_photo', 'location', 'website', 'joined_date', 'is_following', 'is_follower', 'is_mutual']

    def get_is_following(self, obj):
        """Check if the current user is following this profile's user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Follow.objects.filter(follower=request.user, following=obj.user).exists()
        return False

    def get_is_follower(self, obj):
        """Check if this profile's user is following the current user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Follow.objects.filter(follower=obj.user, following=request.user).exists()
        return False

    def get_is_mutual(self, obj):
        """Check if it's a mutual follow (both follow each other)"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            follows_user = Follow.objects.filter(follower=request.user, following=obj.user).exists()
            user_follows = Follow.objects.filter(follower=obj.user, following=request.user).exists()
            return follows_user and user_follows
        return False

class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    reaction_count = serializers.SerializerMethodField()
    reactions_summary = serializers.SerializerMethodField()
    user_reaction = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'content', 'created_at', 'parent', 'replies', 'reaction_count', 'reactions_summary', 'user_reaction']
        read_only_fields = ['post']

    def get_replies(self, obj):
        """Return nested replies for this comment"""
        replies = obj.replies.all()
        return CommentSerializer(replies, many=True, context=self.context).data

    def get_reaction_count(self, obj):
        return obj.reaction_count()

    def get_reactions_summary(self, obj):
        return obj.reactions_summary()

    def get_user_reaction(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            reaction = obj.comment_reactions.filter(user=request.user).first()
            return reaction.reaction_type if reaction else None
        return None


class CommentReactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = CommentReaction
        fields = ['id', 'user', 'comment', 'reaction_type', 'created_at']
        read_only_fields = ['comment']

class ReactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Reaction
        fields = ['id', 'user', 'post', 'reaction_type', 'created_at']
        read_only_fields = ['post']

class PostMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostMedia
        fields = ['id', 'file', 'media_type', 'order', 'created_at']

class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    media_items = PostMediaSerializer(many=True, read_only=True)
    reaction_count = serializers.IntegerField(read_only=True)
    reactions_summary = serializers.SerializerMethodField()
    user_reaction = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'author', 'content', 'image', 'created_at', 'updated_at',
            'reaction_count', 'reactions_summary', 'user_reaction',
            'is_bookmarked', 'comments', 'status', 'media_items',
        ]

    def get_reactions_summary(self, obj):
        return obj.reactions_summary()

    def get_user_reaction(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            reaction = obj.reactions.filter(user=request.user).first()
            return reaction.reaction_type if reaction else None
        return None

    def get_is_bookmarked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.bookmarks.filter(id=request.user.id).exists()
        return False

class NotificationSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    post = PostSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'recipient', 'sender', 'notification_type', 'post', 'is_read', 'created_at']

class FriendRequestSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)

    class Meta:
        model = FriendRequest
        fields = ['id', 'sender', 'receiver', 'status', 'created_at']
        read_only_fields = ['sender', 'status']

class FollowSerializer(serializers.ModelSerializer):
    follower = UserSerializer(read_only=True)
    following = UserSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = ['id', 'follower', 'following', 'created_at']

class ShareSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    original_post = PostSerializer(read_only=True)

    class Meta:
        model = Share
        fields = ['id', 'user', 'original_post', 'content', 'created_at', 'is_quote']

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    read_by = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'content', 'image', 'is_read', 'read_by', 'created_at', 'read_at']
        read_only_fields = ['conversation']

class ConversationSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'participants', 'pinned_by', 'theme', 'created_at', 'updated_at', 'messages']


