from django.db import models
from django.contrib.auth.models import User

class Event(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_events')
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=255, blank=True)
    cover_image = models.ImageField(upload_to='event_covers/', blank=True, null=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    is_online = models.BooleanField(default=False)
    online_link = models.URLField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_datetime']

    def __str__(self):
        return self.title

    def rsvp_count_by_status(self, status):
        return self.rsvps.filter(status=status).count()

    def attendee_count(self):
        return self.rsvps.filter(status='going').count()

class EventRSVP(models.Model):
    STATUS_CHOICES = (
        ('going', 'Going'),
        ('interested', 'Interested'),
        ('not_going', 'Not Going'),
    )
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='rsvps')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_rsvps')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('event', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.event.title} ({self.status})"
