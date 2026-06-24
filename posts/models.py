from django.db import models
from django.contrib.auth.models import User


class HashTag(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'#{self.name}'


class Post(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
    )
    
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField()
    image = models.ImageField(upload_to='post_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='published')
    hashtags = models.ManyToManyField(HashTag, related_name='posts', blank=True)
    bookmarks = models.ManyToManyField(User, related_name='bookmarked_posts', blank=True)
    group = models.ForeignKey(
        'groups.Group', on_delete=models.CASCADE, related_name='posts',
        blank=True, null=True
    )

    co_authors = models.ManyToManyField(User, blank=True, related_name='collaborative_posts', help_text='Co-authors who co-publish this post')


    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        from utils.image_optimizer import optimize_image
        if self.pk:
            try:
                orig = Post.objects.get(pk=self.pk)
                if orig.image != self.image and self.image:
                    optimize_image(self.image)
            except Post.DoesNotExist:
                if self.image:
                    optimize_image(self.image)
        else:
            if self.image:
                optimize_image(self.image)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Post by {self.author.username} at {self.created_at}'

    def reaction_count(self):
        return self.reactions.count()

    def share_count(self):
        return self.shares.count()

    def reactions_summary(self):
        """Return dict of reaction_type -> count for this post."""
        from django.db.models import Count
        return dict(
            self.reactions.values_list('reaction_type')
            .annotate(c=Count('id'))
            .values_list('reaction_type', 'c')
        )


class Reaction(models.Model):
    REACTION_TYPES = (
        ('like', '👍'),
        ('love', '❤️'),
        ('haha', '😂'),
        ('wow', '😮'),
        ('sad', '😢'),
        ('fire', '🔥'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reactions')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reactions')
    reaction_type = models.CharField(max_length=10, choices=REACTION_TYPES, default='like')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} reacted {self.reaction_type} on {self.post}'


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name='replies', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Comment by {self.author.username} on {self.post}'

    def reaction_count(self):
        return self.comment_reactions.count()

    def reactions_summary(self):
        """Return dict of reaction_type -> count for this comment."""
        from django.db.models import Count
        return dict(
            self.comment_reactions.values_list('reaction_type')
            .annotate(c=Count('id'))
            .values_list('reaction_type', 'c')
        )


class CommentReaction(models.Model):
    REACTION_TYPES = (
        ('like', '👍'),
        ('love', '❤️'),
        ('haha', '😂'),
        ('wow', '😮'),
        ('sad', '😢'),
        ('fire', '🔥'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment_reactions')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='comment_reactions')
    reaction_type = models.CharField(max_length=10, choices=REACTION_TYPES, default='like')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'comment')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} reacted {self.reaction_type} on comment'


class Share(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shares')
    original_post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='shares')
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_quote = models.BooleanField(default=False)  # If True, this is a quote post (share with commentary)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        share_type = 'quoted' if self.is_quote else 'shared'
        return f'{self.user.username} {share_type} post by {self.original_post.author.username}'

# Import Poll models so they are loaded as part of the posts app models
from .poll_models import Poll, PollOption, PollVote  # noqa: E402


class PostMedia(models.Model):
    """Model to store multiple media files for carousel posts"""
    MEDIA_TYPES = (
        ('image', 'Image'),
        ('video', 'Video'),
    )
    
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='media_items')
    file = models.FileField(upload_to='post_media/')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES, default='image')
    order = models.PositiveIntegerField(default=0)  # For ordering carousel items
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'Media {self.order} for post by {self.post.author.username}'

