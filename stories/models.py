from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class StoryManager(models.Manager):
    def active(self):
        return self.filter(expires_at__gt=timezone.now())


class Story(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories')
    image = models.ImageField(upload_to='story_images/')
    caption = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    objects = StoryManager()

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'stories'

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        from utils.image_optimizer import optimize_image
        if self.pk:
            try:
                orig = Story.objects.get(pk=self.pk)
                if orig.image != self.image and self.image:
                    optimize_image(self.image)
            except Story.DoesNotExist:
                if self.image:
                    optimize_image(self.image)
        else:
            if self.image:
                optimize_image(self.image)
        super().save(*args, **kwargs)

    def is_active(self):
        return self.expires_at > timezone.now()

    def __str__(self):
        return f'Story by {self.author.username} at {self.created_at}'


class StoryView(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='views')
    viewer = models.ForeignKey(User, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('story', 'viewer')
        ordering = ['-viewed_at']

    def __str__(self):
        return f'{self.viewer.username} viewed {self.story}'
