from django.db import models
from django.contrib.auth.models import User


class Reel(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reels')
    video = models.FileField(upload_to='reel_videos/')
    thumbnail = models.ImageField(upload_to='reel_thumbnails/', blank=True, null=True)
    caption = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name='liked_reels', blank=True)
    view_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        from utils.image_optimizer import optimize_image
        if self.pk:
            try:
                orig = Reel.objects.get(pk=self.pk)
                if orig.thumbnail != self.thumbnail and self.thumbnail:
                    optimize_image(self.thumbnail)
            except Reel.DoesNotExist:
                if self.thumbnail:
                    optimize_image(self.thumbnail)
        else:
            if self.thumbnail:
                optimize_image(self.thumbnail)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Reel by {self.author.username} at {self.created_at}'

    def like_count(self):
        return self.likes.count()

    def comment_count(self):
        return self.reel_comments.count()


class ReelComment(models.Model):
    reel = models.ForeignKey(Reel, on_delete=models.CASCADE, related_name='reel_comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reel_comments')
    content = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Comment by {self.author.username} on reel {self.reel.id}'
