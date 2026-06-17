from django.db import models
from django.contrib.auth.models import User

class Block(models.Model):
    blocker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocking')
    blocked = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('blocker', 'blocked')

    def __str__(self):
        return f"{self.blocker.username} blocked {self.blocked.username}"

class Report(models.Model):
    REPORT_TYPES = (
        ('post', 'Post'),
        ('comment', 'Comment'),
        ('user', 'User'),
        ('reel', 'Reel'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('resolved', 'Resolved'),
    )
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_submitted')
    report_type = models.CharField(max_length=15, choices=REPORT_TYPES)
    content_id = models.PositiveIntegerField()  # ID of post, comment, user, or reel
    reason = models.TextField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Report #{self.id} by {self.reporter.username} ({self.report_type})"
