# ConnectSphere - New Features Roadmap

**Comprehensive feature expansion strategy to transform ConnectSphere into a comprehensive social ecosystem.**

---

## 📑 Feature Categories

| Category | Count | Priority | Section |
|----------|-------|----------|---------|
| Social Interactions | 12 features | 🔴 High | [F1](#f1-advanced-social-interactions) |
| Content Creation | 10 features | 🔴 High | [F2](#f2-advanced-content-creation) |
| Discovery & Recommendations | 8 features | 🟠 Medium | [F3](#f3-discovery--recommendations) |
| Creator Economy | 7 features | 🟡 Medium | [F4](#f4-creator-economy) |
| Community & Moderation | 6 features | 🔴 High | [F5](#f5-community--moderation) |
| AI & Smart Features | 8 features | 🟡 Medium | [F6](#f6-ai--smart-features) |
| Integrations & Connectivity | 9 features | 🟡 Medium | [F7](#f7-integrations--connectivity) |
| Mobile & Native Apps | 5 features | 🟠 Medium | [F8](#f8-mobile--native-features) |
| Monetization | 6 features | 🟡 Medium | [F9](#f9-monetization) |
| Accessibility & Inclusivity | 7 features | 🔴 High | [F10](#f10-accessibility--inclusivity) |

---

## 🔴 F1: Advanced Social Interactions

### 1.1 Live Streaming
**Description**: Real-time video broadcasts with chat  
**Impact**: 🔥 Very High | **Complexity**: ⭐⭐⭐⭐ Hard | **Effort**: 5-7 days

**Implementation:**
```python
# posts/models.py
class LiveStream(models.Model):
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('live', 'Live'),
        ('ended', 'Ended'),
    ]
    
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='live_streams')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    thumbnail = models.ImageField(upload_to='live_thumbnails/', null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    stream_key = models.CharField(max_length=100, unique=True)  # For RTMP
    viewer_count = models.PositiveIntegerField(default=0)
    total_viewers = models.PositiveIntegerField(default=0)
    recording = models.FileField(upload_to='live_recordings/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class LiveStreamViewer(models.Model):
    stream = models.ForeignKey(LiveStream, on_delete=models.CASCADE, related_name='viewers')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)

class LiveStreamComment(models.Model):
    stream = models.ForeignKey(LiveStream, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
```

**WebSocket Consumer:**
```python
# posts/consumers.py
class LiveStreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.stream_id = self.scope['url_route']['kwargs']['stream_id']
        self.stream_group = f'live_stream_{self.stream_id}'
        
        await self.channel_layer.group_add(self.stream_group, self.channel_name)
        await self.accept()
        
        # Notify viewer joined
        await self.channel_layer.group_send(
            self.stream_group,
            {
                'type': 'viewer_joined',
                'username': self.scope['user'].username,
            }
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        
        if data['type'] == 'comment':
            comment = await self.save_comment(data['content'])
            await self.channel_layer.group_send(
                self.stream_group,
                {
                    'type': 'stream_comment',
                    'comment': comment,
                }
            )
        elif data['type'] == 'reaction':
            # Handle emoji reactions
            await self.channel_layer.group_send(
                self.stream_group,
                {
                    'type': 'stream_reaction',
                    'user': self.scope['user'].username,
                    'emoji': data['emoji'],
                }
            )

    async def stream_comment(self, event):
        await self.send(text_data=json.dumps({
            'type': 'comment',
            'comment': event['comment'],
        }))

    async def viewer_joined(self, event):
        await self.send(text_data=json.dumps({
            'type': 'viewer_joined',
            'username': event['username'],
        }))
```

**Tech Stack**: RTMP (FFmpeg), HLS streaming, AWS MediaLive or Wowza

---

### 1.2 Commenting on Comments (Nested Threads)
**Description**: Reply to specific comments instead of just the post  
**Impact**: 📈 High | **Complexity**: ⭐⭐ Easy | **Effort**: 2-3 days

```python
# posts/models.py
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    parent_comment = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        related_name='replies',
        null=True, 
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_depth(self):
        """Get nesting level."""
        if self.parent_comment:
            return self.parent_comment.get_depth() + 1
        return 0

    def get_root_comment(self):
        """Get top-level comment."""
        if self.parent_comment:
            return self.parent_comment.get_root_comment()
        return self
```

---

### 1.3 Comment Reactions (Like Comments)
**Description**: React to individual comments with emoji  
**Impact**: 📈 Medium | **Complexity**: ⭐⭐ Easy | **Effort**: 1-2 days

```python
# posts/models.py
class CommentReaction(models.Model):
    REACTION_TYPES = (
        ('like', '👍'),
        ('love', '❤️'),
        ('haha', '😂'),
        ('wow', '😮'),
        ('sad', '😢'),
        ('fire', '🔥'),
    )
    
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=10, choices=REACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('comment', 'user')
```

---

### 1.4 @Mention Notifications with Special Symbols
**Description**: Different notification types for @mentions, #hashtags, polls  
**Impact**: 📈 Medium | **Complexity**: ⭐⭐ Easy | **Effort**: 1-2 days

```python
# notifications/models.py
class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('comment_reply', 'Comment Reply'),
        ('friend_request', 'Friend Request'),
        ('friend_accept', 'Friend Accept'),
        ('follow', 'Follow'),
        ('mention', 'Mention'),
        ('tag_in_post', 'Tagged in Post'),
        ('tag_in_comment', 'Tagged in Comment'),
        ('poll_vote', 'Poll Voted'),
        ('collab_invite', 'Collaboration Invite'),
    )
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='notifications', blank=True, null=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='notifications', blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
```

---

### 1.5 User Tags/Mentions in Posts
**Description**: Tag users in photos (like Instagram)  
**Impact**: 📈 High | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 3-4 days

```python
# posts/models.py
class PostTag(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='tags')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tagged_in_posts')
    x_position = models.FloatField()  # % from left
    y_position = models.FloatField()  # % from top
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')

# Notification when tagged
@receiver(post_save, sender=PostTag)
def notify_tagged_user(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            recipient=instance.user,
            sender=instance.post.author,
            notification_type='tag_in_post',
            post=instance.post,
        )
```

---

### 1.6 Quote Posts (Share with Comment)
**Description**: Share a post and add your own caption/commentary  
**Impact**: 📈 Medium | **Complexity**: ⭐⭐ Easy | **Effort**: 2 days

```python
# posts/models.py
class Post(models.Model):
    # ... existing fields ...
    quoted_post = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quotes'
    )

# Template display
# Show both original post and quote in feed
```

---

### 1.7 Polls with Real-Time Updates
**Current**: Basic polls  
**Enhancement**: Real-time vote counts, animated results, anonymous polls

```python
# posts/poll_models.py
class Poll(models.Model):
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='poll')
    question = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_anonymous = models.BooleanField(default=False)
    allow_multiple_votes = models.BooleanField(default=False)
    
    def get_winner(self):
        """Get the winning option."""
        return self.options.annotate(
            count=Count('votes')
        ).order_by('-count').first()
```

---

### 1.8 Saved Collections (Smart Lists)
**Description**: Smart collections based on hashtags, creators, topics  
**Impact**: 📈 Medium | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 3-4 days

```python
# posts/models.py
class Collection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collections')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_private = models.BooleanField(default=True)
    posts = models.ManyToManyField(Post, related_name='in_collections')
    hashtags = models.ManyToManyField(HashTag, blank=True)  # Auto-add posts with these tags
    authors = models.ManyToManyField(User, blank=True, related_name='collected_by')  # Follow these creators
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'name')
```

---

### 1.9 Mentions Count & Activity Summary
**Description**: "You were mentioned 5 times this week"  
**Impact**: 📈 Low | **Complexity**: ⭐ Very Easy | **Effort**: 1 day

```python
# users/views.py
def notification_summary(user):
    from datetime import timedelta
    from django.utils import timezone
    
    last_week = timezone.now() - timedelta(days=7)
    
    summary = {
        'mentions': user.notifications.filter(
            notification_type__in=['mention', 'tag_in_post'],
            created_at__gte=last_week
        ).count(),
        'likes': user.notifications.filter(
            notification_type='like',
            created_at__gte=last_week
        ).count(),
        'comments': user.notifications.filter(
            notification_type__in=['comment', 'comment_reply'],
            created_at__gte=last_week
        ).count(),
        'follows': user.notifications.filter(
            notification_type='follow',
            created_at__gte=last_week
        ).count(),
    }
    
    return summary
```

---

### 1.10 Mutual Follows Detection
**Description**: Show "You both follow each other" badges  
**Impact**: 📈 Low | **Complexity**: ⭐ Very Easy | **Effort**: 1 day

```python
# friends/models.py
class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    @property
    def is_mutual(self):
        """Check if both users follow each other."""
        return Follow.objects.filter(
            follower=self.following,
            following=self.follower
        ).exists()
```

---

### 1.11 User Mention Suggestions
**Description**: Autocomplete @mentions while typing  
**Impact**: 📈 Medium | **Complexity**: ⭐⭐ Easy | **Effort**: 1-2 days

```python
# api/views.py
class MentionSuggestionsViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['get'])
    def suggest(self, request):
        query = request.GET.get('q', '')
        if len(query) < 2:
            return Response([])
        
        suggestions = User.objects.filter(
            username__istartswith=query
        ).exclude(id=request.user.id)[:10].values(
            'id', 'username', 'userprofile__profile_picture'
        )
        
        return Response(suggestions)
```

---

### 1.12 Reaction Summary Panel
**Description**: See who reacted with what emoji  
**Impact**: 📈 Low | **Complexity**: ⭐ Very Easy | **Effort**: 1 day

```python
# posts/models.py
class Post(models.Model):
    # ... existing ...
    
    def get_reaction_stats(self):
        """Get detailed reaction breakdown."""
        from django.db.models import Count
        
        return self.reactions.values('reaction_type').annotate(
            count=Count('id')
        ).order_by('-count')
    
    def who_reacted_with(self, reaction_type):
        """Get users who reacted with specific emoji."""
        return self.reactions.filter(
            reaction_type=reaction_type
        ).select_related('user')
```

---

## 🔴 F2: Advanced Content Creation

### 2.1 Carousel Posts (Multi-Image Albums)
**Description**: Create posts with multiple images in a swipeable carousel  
**Impact**: 🔥 Very High | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 3-4 days

```python
# posts/models.py
class PostMedia(models.Model):
    TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('gif', 'GIF'),
    ]
    
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='media_items')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    file = models.FileField(upload_to='post_media/')
    thumbnail = models.ImageField(upload_to='post_thumbnails/', null=True, blank=True)
    order = models.PositiveSmallIntegerField()
    caption = models.TextField(blank=True)  # Per-image caption
    aspect_ratio = models.CharField(max_length=10, default='1:1')  # 1:1, 4:5, 16:9
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']
        unique_together = ('post', 'order')
```

---

### 2.2 Draft Posts
**Description**: Save posts as drafts before publishing  
**Impact**: 📈 Medium | **Complexity**: ⭐ Very Easy | **Effort**: 1 day

```python
# posts/models.py
class Post(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
        ('scheduled', 'Scheduled'),
    ]
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='published')
    scheduled_for = models.DateTimeField(null=True, blank=True)
    last_saved = models.DateTimeField(auto_now=True)
```

---

### 2.3 Post Scheduling
**Description**: Schedule posts to publish at specific times  
**Impact**: 📈 Medium | **Complexity**: ⭐⭐ Easy | **Effort**: 2-3 days

```bash
pip install celery celery-beat

# celery.py
from celery import shared_task
from celery.schedules import crontab
from django.utils import timezone
from posts.models import Post

@shared_task
def publish_scheduled_posts():
    """Run every minute to check and publish scheduled posts."""
    now = timezone.now()
    posts = Post.objects.filter(
        status='scheduled',
        scheduled_for__lte=now
    )
    
    for post in posts:
        post.status = 'published'
        post.save()
        # Trigger notifications
        notify_followers(post)

app.conf.beat_schedule = {
    'publish-scheduled-posts': {
        'task': 'posts.tasks.publish_scheduled_posts',
        'schedule': crontab(minute='*'),  # Every minute
    },
}
```

---

### 2.4 Video Captions & Subtitles
**Description**: Auto-generate captions for reels with CC support  
**Impact**: 📈 High | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 4-5 days

```bash
pip install google-cloud-speech openai-whisper

# reels/tasks.py
@shared_task
def generate_captions(reel_id):
    """Auto-generate captions using Whisper AI."""
    import whisper
    from reels.models import Reel, ReelCaption
    
    reel = Reel.objects.get(id=reel_id)
    
    # Load Whisper model
    model = whisper.load_model("base")
    
    # Generate captions
    result = model.transcribe(reel.video.path)
    
    # Save captions
    for segment in result['segments']:
        ReelCaption.objects.create(
            reel=reel,
            start_time=segment['start'],
            end_time=segment['end'],
            text=segment['text'],
            language='en'
        )

# reels/models.py
class ReelCaption(models.Model):
    reel = models.ForeignKey(Reel, on_delete=models.CASCADE, related_name='captions')
    start_time = models.FloatField()
    end_time = models.FloatField()
    text = models.TextField()
    language = models.CharField(max_length=10, default='en')
```

---

### 2.5 GIF Creation from Videos
**Description**: Create animated GIFs from reel segments  
**Impact**: 📈 Medium | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 3-4 days

```python
# reels/tasks.py
@shared_task
def create_gif_from_reel(reel_id, start_time=0, end_time=3):
    """Create GIF from reel segment."""
    import imageio
    from reels.models import Reel
    
    reel = Reel.objects.get(id=reel_id)
    
    # Extract frames
    reader = imageio.get_reader(reel.video.path)
    frames = []
    for i, frame in enumerate(reader):
        if start_time * 30 <= i <= end_time * 30:  # 30fps assumption
            frames.append(frame)
    
    # Create GIF
    gif_path = f'{reel.id}.gif'
    imageio.mimwrite(gif_path, frames, duration=0.1)
    
    # Save
    reel.gif_preview = gif_path
    reel.save()
```

---

### 2.6 Rich Text Editor (Markdown Support)
**Description**: Format posts with bold, italic, links, code blocks  
**Impact**: 📈 Low | **Complexity**: ⭐⭐ Easy | **Effort**: 2 days

```bash
pip install markdown bleach

# posts/models.py
from markdown import markdown
from bleach import clean

class Post(models.Model):
    content = models.TextField()
    content_html = models.TextField(blank=True)  # Rendered HTML
    
    def save(self, *args, **kwargs):
        # Convert markdown to HTML
        html = markdown(self.content)
        # Sanitize dangerous HTML
        self.content_html = clean(
            html,
            tags=['b', 'i', 'u', 'p', 'br', 'a', 'strong', 'em', 'code', 'pre', 'blockquote'],
            attributes={'a': ['href', 'title']}
        )
        super().save(*args, **kwargs)
```

---

### 2.7 Story Drawing Tools
**Description**: Draw, write, add stickers to stories  
**Impact**: 📈 Medium | **Complexity**: ⭐⭐⭐⭐ Hard | **Effort**: 5-7 days

```bash
pip install Pillow fabric.js-python

# stories/models.py
class StoryElement(models.Model):
    TYPE_CHOICES = [
        ('text', 'Text'),
        ('sticker', 'Sticker'),
        ('drawing', 'Drawing'),
        ('emoji', 'Emoji'),
    ]
    
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='elements')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    content = models.JSONField()  # {text, position, rotation, color, size, ...}
    order = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']

# Frontend would use Fabric.js for drawing
```

---

### 2.8 Audio Posts (Podcasts)
**Description**: Create text posts with embedded audio  
**Impact**: 📈 Low-Medium | **Complexity**: ⭐⭐ Easy | **Effort**: 2-3 days

```python
# posts/models.py
class AudioPost(models.Model):
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='audio')
    audio_file = models.FileField(upload_to='audio_posts/')
    duration = models.IntegerField()  # Seconds
    transcript = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

---

### 2.9 Collaborative Posts (Co-Creation)
**Enhancement**: Better collaboration workflow  
**Current**: Basic co-authors field  
**Enhancement**: Invite collaborators, edit permissions, version history

```python
# posts/models.py
class PostCollaborator(models.Model):
    ROLE_CHOICES = [
        ('editor', 'Can Edit'),
        ('viewer', 'Can View Only'),
        ('commenter', 'Can Comment'),
    ]
    
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='collaborators')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer')
    invited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='post_invites_sent')
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('declined', 'Declined')])
    created_at = models.DateTimeField(auto_now_add=True)

class PostVersion(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='versions')
    content = models.TextField()
    image = models.ImageField(null=True, blank=True)
    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    change_summary = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
```

---

### 2.10 Content Templates & Presets
**Description**: Save post templates for quick creation  
**Impact**: 📈 Low | **Complexity**: ⭐⭐ Easy | **Effort**: 2 days

```python
# posts/models.py
class PostTemplate(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_templates')
    name = models.CharField(max_length=100)
    content = models.TextField()
    hashtags = models.TextField()  # Comma-separated
    media_layout = models.CharField(max_length=20, choices=[('single', 'Single'), ('carousel', 'Carousel'), ('grid', 'Grid')])
    is_public = models.BooleanField(default=False)
    usage_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
```

---

## 🟠 F3: Discovery & Recommendations

### 3.1 Personalized Feed Algorithm
**Description**: ML-based feed ranking (likes interests, interactions)  
**Impact**: 🔥 Very High | **Complexity**: ⭐⭐⭐⭐ Hard | **Effort**: 5-7 days

```python
# recommendations/models.py
class FeedRankingModel(models.Model):
    """Store ML model weights and scoring logic."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='feed_model')
    content_weights = models.JSONField(default=dict)  # Category preferences
    recency_weight = models.FloatField(default=0.3)
    engagement_weight = models.FloatField(default=0.5)
    social_weight = models.FloatField(default=0.2)
    last_updated = models.DateTimeField(auto_now=True)

# recommendations/scoring.py
def calculate_feed_score(post, user):
    """Calculate relevance score for post in user's feed."""
    score = 0.0
    
    # Recency (newer = better)
    from django.utils import timezone
    age_hours = (timezone.now() - post.created_at).total_seconds() / 3600
    recency_score = max(0, 1 - (age_hours / 168))  # Decays over week
    
    # Engagement (likes, comments)
    engagement_score = min(1.0, (post.reaction_count() + post.comments.count()) / 100)
    
    # Social (from followers, mutuals)
    from friends.models import Follow
    is_follower = Follow.objects.filter(
        follower=user, following=post.author
    ).exists()
    is_mutual = is_follower and Follow.objects.filter(
        follower=post.author, following=user
    ).exists()
    social_score = 1.0 if is_mutual else (0.5 if is_follower else 0.1)
    
    # Content preference (based on user interests)
    user_interests = user.userprofile.interest_tags.split(',') if user.userprofile.interest_tags else []
    post_hashtags = [tag.name for tag in post.hashtags.all()]
    interest_overlap = len(set(user_interests) & set(post_hashtags)) / max(len(user_interests), 1)
    interest_score = interest_overlap
    
    # Final weighted score
    score = (
        recency_score * 0.3 +
        engagement_score * 0.5 +
        social_score * 0.1 +
        interest_score * 0.1
    )
    
    return score

# Use in views
def personalized_feed(request):
    from django.db.models import F
    all_posts = Post.objects.all()
    
    # Score and sort
    scored_posts = [
        (post, calculate_feed_score(post, request.user))
        for post in all_posts
    ]
    sorted_posts = sorted(scored_posts, key=lambda x: x[1], reverse=True)
    
    return render(request, 'posts/feed.html', {
        'posts': [p[0] for p in sorted_posts[:50]]
    })
```

---

### 3.2 "For You" Page (Explore Tab)
**Description**: Discover posts from non-followed creators  
**Impact**: 🔥 Very High | **Complexity**: ⭐⭐⭐⭐ Hard | **Effort**: 5-7 days

```python
# recommendations/views.py
from datetime import timedelta

def explore_page(request):
    """Generate personalized explore feed."""
    from django.utils import timezone
    from django.db.models import Q
    
    # Get posts from past 7 days that user hasn't interacted with
    last_week = timezone.now() - timedelta(days=7)
    user_interacted = Q(
        reactions__user=request.user
    ) | Q(
        comments__author=request.user
    ) | Q(
        bookmarks=request.user
    )
    
    candidates = Post.objects.filter(
        created_at__gte=last_week,
        group__isnull=True
    ).exclude(
        user_interacted
    ).exclude(
        author=request.user
    ).exclude(
        author__in=request.user.following.values_list('following')
    ).distinct()
    
    # Score by engagement and interest
    scored = [(p, calculate_feed_score(p, request.user)) for p in candidates]
    sorted_posts = sorted(scored, key=lambda x: x[1], reverse=True)
    
    return render(request, 'posts/explore.html', {
        'posts': [p[0] for p in sorted_posts[:50]]
    })
```

---

### 3.3 Smart Hashtag Recommendations
**Description**: Suggest relevant hashtags while composing  
**Impact**: 📈 Medium | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 3-4 days

```python
# posts/views.py
@login_required
def suggest_hashtags(request):
    """Suggest hashtags based on post content."""
    content = request.GET.get('content', '')
    
    if not content or len(content) < 10:
        return JsonResponse({'suggestions': []})
    
    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np
    
    # Get all hashtags and their posts
    all_tags = HashTag.objects.all()
    
    # Find hashtags used in similar content
    similar_tags = []
    for tag in all_tags:
        tag_posts = tag.posts.values_list('content', flat=True)[:10]
        
        # Simple TF-IDF similarity
        vectorizer = TfidfVectorizer()
        try:
            vectors = vectorizer.fit_transform([content] + list(tag_posts))
            similarity = (vectors[0] * vectors[1:].T).max()
            if similarity > 0.1:
                similar_tags.append((tag.name, float(similarity)))
        except:
            pass
    
    # Sort by similarity and limit
    similar_tags.sort(key=lambda x: x[1], reverse=True)
    
    return JsonResponse({
        'suggestions': [tag[0] for tag in similar_tags[:10]]
    })
```

---

### 3.4 Trending Hashtags & Topics by Region
**Description**: Regional trending topics (worldwide, country, city)  
**Impact**: 📈 High | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 3-4 days

```python
# posts/models.py
class TrendingHashTag(models.Model):
    hashtag = models.OneToOneField(HashTag, on_delete=models.CASCADE)
    region = models.CharField(max_length=100, default='worldwide')  # Country code or 'worldwide'
    position = models.PositiveIntegerField()
    volume = models.PositiveIntegerField()  # Number of posts
    growth_rate = models.FloatField()  # % change from previous period
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('hashtag', 'region')

# tasks.py - Run hourly
@shared_task
def update_trending_hashtags():
    """Calculate trending hashtags by region."""
    from datetime import timedelta
    from django.utils import timezone
    from django.db.models import Count
    
    last_24h = timezone.now() - timedelta(hours=24)
    
    # Worldwide trends
    top_tags = HashTag.objects.filter(
        posts__created_at__gte=last_24h
    ).annotate(
        count=Count('posts')
    ).order_by('-count')[:50]
    
    for pos, tag in enumerate(top_tags, 1):
        TrendingHashTag.objects.update_or_create(
            hashtag=tag,
            region='worldwide',
            defaults={
                'position': pos,
                'volume': tag.count,
            }
        )
```

---

### 3.5 Creator Recommendations
**Description**: Suggest creators to follow based on interests  
**Impact**: 📈 High | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 4-5 days

```python
# friends/views.py
def recommend_creators(request):
    """Recommend creators based on user's interests and followers."""
    from django.db.models import Count
    from friends.models import Follow
    
    # Get users followed by people user follows
    user_followers = Follow.objects.filter(
        follower=request.user
    ).values_list('following', flat=True)
    
    recommendations = User.objects.filter(
        following__follower_id__in=user_followers
    ).exclude(
        followers__follower=request.user
    ).exclude(
        id=request.user.id
    ).annotate(
        mutual_followers=Count('followers', distinct=True)
    ).order_by('-mutual_followers')[:20]
    
    return render(request, 'friends/recommendations.html', {
        'recommendations': recommendations
    })
```

---

### 3.6 Interest-Based Collections (Auto-Curated)
**Description**: Automatically organize posts by topic  
**Impact**: 📈 Medium | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 3-4 days

```python
# posts/models.py
class InterestCategory(models.Model):
    CATEGORIES = [
        ('tech', 'Technology'),
        ('travel', 'Travel'),
        ('food', 'Food & Cooking'),
        ('fitness', 'Fitness'),
        ('art', 'Art & Design'),
        ('music', 'Music'),
        ('photography', 'Photography'),
        ('lifestyle', 'Lifestyle'),
    ]
    
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=50)
    description = models.TextField()
    icon = models.CharField(max_length=50)  # Bootstrap icon class
    color = models.CharField(max_length=7)  # Hex color

class PostInterest(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='interests')
    category = models.ForeignKey(InterestCategory, on_delete=models.CASCADE)
    confidence = models.FloatField()  # 0-1 score
    
    class Meta:
        unique_together = ('post', 'category')

# Auto-categorize using ML
@shared_task
def categorize_post(post_id):
    """Auto-categorize posts using NLP."""
    from posts.models import Post, PostInterest, InterestCategory
    import nltk
    from textblob import TextBlob
    
    post = Post.objects.get(id=post_id)
    
    # Simple keyword matching
    content = post.content.lower()
    hashtags = [tag.name for tag in post.hashtags.all()]
    
    category_keywords = {
        'tech': ['code', 'programming', 'software', 'app', 'tech', 'developer'],
        'travel': ['travel', 'trip', 'vacation', 'destination', 'explore'],
        'food': ['food', 'recipe', 'cooking', 'eat', 'restaurant'],
        'fitness': ['exercise', 'workout', 'gym', 'fitness', 'health'],
        'art': ['art', 'design', 'illustration', 'creative'],
        'music': ['music', 'song', 'artist', 'concert'],
        'photography': ['photo', 'photography', 'camera', 'picture'],
        'lifestyle': ['life', 'daily', 'routine', 'style'],
    }
    
    for category_slug, keywords in category_keywords.items():
        matches = sum(1 for keyword in keywords if keyword in content or keyword in ' '.join(hashtags))
        if matches > 0:
            confidence = min(1.0, matches / len(keywords))
            category = InterestCategory.objects.get(slug=category_slug)
            PostInterest.objects.create(
                post=post,
                category=category,
                confidence=confidence
            )
```

---

### 3.7 "You May Know" for Groups
**Description**: Suggest groups similar to ones user joined  
**Impact**: 📈 Low-Medium | **Complexity**: ⭐⭐ Easy | **Effort**: 2-3 days

```python
# groups/views.py
def recommend_groups(request):
    """Recommend groups based on user's memberships."""
    from django.db.models import Count
    
    user_groups = request.user.group_memberships.values_list('group', flat=True)
    
    # Find users in same groups
    similar_users = User.objects.filter(
        group_memberships__group_id__in=user_groups
    ).exclude(id=request.user.id).annotate(
        mutual_groups=Count('group_memberships', distinct=True)
    ).order_by('-mutual_groups')[:10].values_list('id', flat=True)
    
    # Find groups those users are in
    recommendations = Group.objects.filter(
        memberships__user_id__in=similar_users
    ).exclude(memberships__user=request.user).annotate(
        mutual_members=Count('memberships')
    ).order_by('-mutual_members')[:20]
    
    return render(request, 'groups/recommendations.html', {
        'recommendations': recommendations
    })
```

---

### 3.8 Smart Notifications (Digest)
**Description**: Group notifications instead of flooding  
**Impact**: 📈 Low-Medium | **Complexity**: ⭐⭐ Easy | **Effort**: 2 days

```python
# notifications/models.py
class NotificationDigest(models.Model):
    FREQUENCY_CHOICES = [
        ('instant', 'Instant'),
        ('daily', 'Daily Digest'),
        ('weekly', 'Weekly Digest'),
        ('never', 'Never'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_digest_settings')
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='instant')
    notification_types = models.JSONField(default=dict)  # Type -> enabled/disabled
    quiet_hours_start = models.TimeField(default='22:00')
    quiet_hours_end = models.TimeField(default='08:00')

# tasks.py
@shared_task
def send_daily_digest():
    """Send daily notification digest to users who opted in."""
    from notifications.models import Notification, NotificationDigest
    from datetime import timedelta
    from django.utils import timezone
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    
    yesterday = timezone.now() - timedelta(days=1)
    
    digests = NotificationDigest.objects.filter(frequency='daily')
    
    for digest in digests:
        notifications = Notification.objects.filter(
            recipient=digest.user,
            created_at__gte=yesterday
        ).order_by('-created_at')
        
        if notifications.exists():
            html_message = render_to_string(
                'notifications/digest_email.html',
                {'notifications': notifications}
            )
            
            send_mail(
                'Your Daily Digest',
                'Check out your daily digest',
                'noreply@connectsphere.com',
                [digest.user.email],
                html_message=html_message,
            )
```

---

## 🔴 F4: Community & Moderation

### 4.1 Community Guidelines & Reporting System
**Enhancement**: Detailed report categories and review workflow  
**Current**: Basic Report model  
**Enhancement**: Community voting on reports, moderator dashboard

```python
# moderation/models.py
class ReportCategory(models.Model):
    CATEGORY_TYPES = [
        ('spam', 'Spam'),
        ('harassment', 'Harassment'),
        ('hate_speech', 'Hate Speech'),
        ('misinformation', 'Misinformation'),
        ('adult_content', 'Adult Content'),
        ('violence', 'Violence'),
        ('copyright', 'Copyright'),
        ('other', 'Other'),
    ]
    
    category = models.CharField(max_length=50, unique=True, choices=CATEGORY_TYPES)
    description = models.TextField()
    icon = models.CharField(max_length=50)
    severity_level = models.IntegerField()  # 1-5

class Report(models.Model):
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('reviewing', 'Under Review'),
        ('in_violation', 'In Violation'),
        ('not_violation', 'Not a Violation'),
        ('appealed', 'Appealed'),
        ('resolved', 'Resolved'),
    ]
    
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_submitted')
    category = models.ForeignKey(ReportCategory, on_delete=models.CASCADE)
    content_type = models.CharField(max_length=20)  # post, comment, user, reel
    content_id = models.PositiveIntegerField()
    reason = models.TextField()
    evidence = models.JSONField(default=list)  # Screenshot URLs, links
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    moderator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='moderated_reports')
    resolution = models.TextField(blank=True)
    moderator_action = models.CharField(
        max_length=50,
        choices=[
            ('no_action', 'No Action'),
            ('warning', 'Warning'),
            ('content_removed', 'Content Removed'),
            ('account_suspended', 'Account Suspended'),
            ('account_banned', 'Account Banned'),
        ],
        blank=True
    )
    community_votes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

class ReportVote(models.Model):
    """Community voting on report validity."""
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='community_votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vote = models.BooleanField()  # Agree with report or not
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('report', 'user')
```

---

### 4.2 Moderation Dashboard
**Description**: Admin interface for reviewing reports  
**Impact**: 📈 High | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 4-5 days

```python
# moderation/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Report, ReportCategory

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'category_display',
        'status_badge',
        'reporter',
        'submitted_at',
        'moderator',
        'actions'
    ]
    list_filter = ['status', 'category', 'created_at']
    search_fields = ['reporter__username', 'reason']
    readonly_fields = ['submitted_at', 'reporter', 'content_type']
    
    fieldsets = (
        ('Report Details', {
            'fields': ('reporter', 'category', 'reason', 'submitted_at')
        }),
        ('Content', {
            'fields': ('content_type', 'content_id', 'evidence')
        }),
        ('Moderation', {
            'fields': ('status', 'moderator', 'moderator_action', 'resolution')
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'submitted': 'gray',
            'reviewing': 'blue',
            'in_violation': 'red',
            'not_violation': 'green',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    
    def category_display(self, obj):
        return obj.category.get_category_display()
    
    actions = ['mark_in_violation', 'mark_not_violation']
    
    def mark_in_violation(self, request, queryset):
        queryset.update(status='in_violation', moderator=request.user)
    mark_in_violation.short_description = "Mark as In Violation"
```

---

### 4.3 User Restrictions & Warnings
**Description**: Graduated enforcement (warning → shadow ban → full ban)  
**Impact**: 📈 High | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 3-4 days

```python
# moderation/models.py
class UserRestriction(models.Model):
    RESTRICTION_TYPES = [
        ('warning', 'Warning'),
        ('comment_restricted', 'Comments Restricted'),
        ('shadow_ban', 'Shadow Ban'),
        ('posting_restricted', 'Posting Restricted'),
        ('temporary_suspension', 'Temporary Suspension'),
        ('permanent_ban', 'Permanent Ban'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='restrictions')
    restriction_type = models.CharField(max_length=50, choices=RESTRICTION_TYPES)
    reason = models.TextField()
    imposed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='imposed_restrictions')
    duration_days = models.IntegerField(null=True, blank=True)  # NULL = permanent
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def is_expired(self):
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

# Middleware to enforce restrictions
class RestrictionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated:
            active_restrictions = request.user.restrictions.filter(
                is_active=True,
                restriction_type__in=['temporary_suspension', 'permanent_ban']
            )
            
            for restriction in active_restrictions:
                if restriction.is_expired():
                    restriction.is_active = False
                    restriction.save()
                else:
                    # Redirect to suspension page
                    from django.shortcuts import render
                    return render(request, 'moderation/account_restricted.html', {
                        'restriction': restriction
                    })
        
        return self.get_response(request)
```

---

### 4.4 Content Moderation Flags
**Description**: Soft delete with manual review  
**Impact**: 📈 Medium | **Complexity**: ⭐⭐ Easy | **Effort**: 2-3 days

```python
# moderation/models.py
class ContentFlag(models.Model):
    FLAG_REASONS = [
        ('auto_flagged', 'Auto-Flagged'),
        ('user_report', 'User Report'),
        ('moderator_action', 'Moderator Action'),
    ]
    
    content_type = models.CharField(max_length=50)  # post, comment, reel
    content_id = models.PositiveIntegerField()
    reason = models.CharField(max_length=100, choices=FLAG_REASONS)
    is_hidden = models.BooleanField(default=False)
    hidden_from = models.ManyToManyField(User, blank=True, related_name='hidden_content')
    flagged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

# In feeds, filter hidden content
def get_user_feed(request):
    flagged_content_ids = ContentFlag.objects.filter(
        hidden_from=request.user,
        is_hidden=True
    ).values_list('content_id')
    
    posts = Post.objects.exclude(id__in=flagged_content_ids)
    return posts
```

---

### 4.5 Spam Detection
**Description**: Auto-detect and flag spam content  
**Impact**: 📈 Medium | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 3-4 days

```bash
pip install textblob spam-filter

# moderation/tasks.py
@shared_task
def detect_spam(post_id):
    """Auto-detect spam posts."""
    from posts.models import Post
    from moderation.models import ContentFlag
    from textblob import TextBlob
    import re
    
    post = Post.objects.get(id=post_id)
    
    spam_score = 0.0
    
    # Check for excessive links
    links = re.findall(r'http[s]?://\S+', post.content)
    if len(links) > 3:
        spam_score += 0.3
    
    # Check for excessive mentions
    mentions = re.findall(r'@\w+', post.content)
    if len(mentions) > 10:
        spam_score += 0.3
    
    # Check for excessive hashtags
    hashtags = re.findall(r'#\w+', post.content)
    if len(hashtags) > 20:
        spam_score += 0.3
    
    # Check for keyboard mashing
    repeated = re.findall(r'(.)\1{4,}', post.content)
    if repeated:
        spam_score += 0.2
    
    # Check for all caps
    if post.content.isupper() and len(post.content) > 20:
        spam_score += 0.1
    
    if spam_score > 0.5:
        ContentFlag.objects.create(
            content_type='post',
            content_id=post.id,
            reason='auto_flagged',
            flagged_by=None,  # System flag
        )
        post.flagged = True
        post.save()
```

---

### 4.6 Appeal System
**Description**: Allow users to appeal account bans/restrictions  
**Impact**: 📈 Medium | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 3-4 days

```python
# moderation/models.py
class Appeal(models.Model):
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('reviewing', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appeals')
    restriction = models.ForeignKey(UserRestriction, on_delete=models.CASCADE, related_name='appeals')
    reason = models.TextField()
    evidence = models.JSONField(default=list)  # Evidence supporting appeal
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_appeals')
    reviewer_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

# When appeal is approved
@receiver(post_save, sender=Appeal)
def process_appeal(sender, instance, created, **kwargs):
    if instance.status == 'approved' and not created:
        # Remove restriction
        instance.restriction.is_active = False
        instance.restriction.save()
        
        # Notify user
        Notification.objects.create(
            recipient=instance.user,
            sender=User.objects.get(username='system'),
            notification_type='appeal_approved',
        )
```

---

## 🟡 F5: Creator Economy

### 5.1 Creator Fund / Monetization
**Description**: Pay creators based on engagement  
**Impact**: 🔥 Very High | **Complexity**: ⭐⭐⭐⭐ Hard | **Effort**: 6-8 days

```python
# monetization/models.py
class CreatorFund(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='creator_fund')
    account_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    lifetime_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    min_payout_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=100.0)
    payment_method = models.CharField(max_length=50, choices=[('bank', 'Bank Transfer'), ('paypal', 'PayPal'), ('crypto', 'Cryptocurrency')])
    payout_address = models.CharField(max_length=255)
    is_eligible = models.BooleanField(default=False)  # 10k followers, 100k views, 30 days old
    enrolled_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def can_withdraw(self):
        return self.account_balance >= self.min_payout_threshold

class CreatorEarning(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='earnings')
    post = models.ForeignKey(Post, on_delete=models.SET_NULL, null=True, blank=True, related_name='earnings')
    source = models.CharField(max_length=50)  # 'likes', 'views', 'engagement', 'premium'
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

class CreatorWithdrawal(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='withdrawals')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed')])
    transaction_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

# Celery task to calculate earnings
@shared_task
def calculate_daily_earnings():
    """Calculate creator earnings based on engagement."""
    from monetization.models import CreatorFund, CreatorEarning
    from datetime import timedelta
    from django.utils import timezone
    from django.db.models import Count
    
    yesterday = timezone.now() - timedelta(days=1)
    
    # Get all creators with new posts from yesterday
    creators = User.objects.filter(
        posts__created_at__gte=yesterday
    ).distinct()
    
    for creator in creators:
        if not hasattr(creator, 'creator_fund') or not creator.creator_fund.is_eligible:
            continue
        
        # Calculate earnings from posts
        posts = creator.posts.filter(created_at__gte=yesterday)
        
        for post in posts:
            # Simple: $0.01 per 100 likes
            likes = post.reaction_count()
            like_earnings = (likes / 100) * 0.01
            
            # $0.001 per comment
            comments = post.comments.count()
            comment_earnings = comments * 0.001
            
            # $0.002 per share
            shares = post.shares.count()
            share_earnings = shares * 0.002
            
            total = like_earnings + comment_earnings + share_earnings
            
            if total > 0:
                CreatorEarning.objects.create(
                    creator=creator,
                    post=post,
                    source='engagement',
                    amount=total,
                )
                
                creator.creator_fund.account_balance += total
                creator.creator_fund.lifetime_earnings += total
                creator.creator_fund.save()
```

---

### 5.2 Sponsorship & Brand Partnerships
**Description**: Connect brands with creators  
**Impact**: 📈 High | **Complexity**: ⭐⭐⭐⭐ Hard | **Effort**: 5-7 days

```python
# partnerships/models.py
class Brand(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    logo = models.ImageField(upload_to='brand_logos/')
    website = models.URLField()
    industry = models.CharField(max_length=100)
    verified = models.BooleanField(default=False)
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

class Sponsorship(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('open', 'Open for Proposals'),
        ('proposals', 'Reviewing Proposals'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='sponsorships')
    title = models.CharField(max_length=200)
    description = models.TextField()
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    requirements = models.JSONField()  # Deliverables, content specs, etc.
    target_audience = models.JSONField()  # Follower count, interests, location
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

class SponsorshipProposal(models.Model):
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('reviewing', 'Under Review'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('negotiating', 'Negotiating'),
    ]
    
    sponsorship = models.ForeignKey(Sponsorship, on_delete=models.CASCADE, related_name='proposals')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sponsorship_proposals')
    proposed_price = models.DecimalField(max_digits=10, decimal_places=2)
    portfolio_samples = models.JSONField()  # Links to previous sponsored posts
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    notes = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class SponsoredPost(models.Model):
    sponsorship = models.ForeignKey(Sponsorship, on_delete=models.CASCADE, related_name='posts')
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='sponsorship')
    creator_fee = models.DecimalField(max_digits=10, decimal_places=2)
    brand_fee = models.DecimalField(max_digits=10, decimal_places=2)
    requirements_met = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
```

---

### 5.3 Verified Creator Badge & Tier System
**Description**: Different tiers (verified, elite, mega)  
**Impact**: 📈 Medium | **Complexity**: ⭐⭐ Easy | **Effort**: 2-3 days

```python
# users/models.py
class UserProfile(models.Model):
    CREATOR_TIERS = [
        ('none', 'Not a Creator'),
        ('verified', 'Verified Creator'),
        ('elite', 'Elite Creator'),
        ('mega', 'Mega Creator'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # ... existing fields ...
    creator_tier = models.CharField(max_length=20, choices=CREATOR_TIERS, default='none')
    creator_verified_at = models.DateTimeField(null=True, blank=True)
    
    def auto_promote_tier(self):
        """Auto-promote creator tier based on follower count."""
        followers = self.user.followers.count()
        posts = self.user.posts.count()
        engagement_rate = sum(
            p.reaction_count() for p in self.user.posts.all()[:10]
        ) / max(posts, 1) / max(followers, 1)
        
        if followers >= 1000000 and engagement_rate > 0.05:
            self.creator_tier = 'mega'
        elif followers >= 100000 and engagement_rate > 0.03:
            self.creator_tier = 'elite'
        elif followers >= 10000 and engagement_rate > 0.02:
            self.creator_tier = 'verified'
        
        self.save()
```

---

### 5.4 Creator Analytics Dashboard
**Description**: Detailed stats on followers, engagement, reach  
**Impact**: 📈 High | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 4-5 days

```python
# analytics/views.py
@login_required
def creator_dashboard(request):
    user = request.user
    from datetime import timedelta
    from django.utils import timezone
    from django.db.models import Count, Avg, Sum
    
    # Time range
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Follower growth
    follower_count = user.followers.count()
    new_followers = user.followers.filter(created_at__gte=start_date).count()
    
    # Post performance
    posts = user.posts.filter(created_at__gte=start_date)
    total_engagement = sum(p.reaction_count() + p.comments.count() for p in posts)
    avg_engagement = total_engagement / max(posts.count(), 1)
    
    # Audience demographics
    audience = {
        'top_locations': [],  # Aggregate from user profiles
        'age_distribution': {},
        'gender_distribution': {},
    }
    
    # Top posts
    top_posts = posts.annotate(
        engagement=Count('reactions') + Count('comments')
    ).order_by('-engagement')[:5]
    
    context = {
        'follower_count': follower_count,
        'new_followers': new_followers,
        'total_engagement': total_engagement,
        'avg_engagement': avg_engagement,
        'top_posts': top_posts,
        'audience': audience,
    }
    
    return render(request, 'analytics/creator_dashboard.html', context)
```

---

### 5.5 Creator Directory / Marketplace
**Description**: Browse and discover creators to hire  
**Impact**: 📈 High | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 4-5 days

```python
# creators/models.py
class CreatorProfile(models.Model):
    CATEGORIES = [
        ('lifestyle', 'Lifestyle'),
        ('fashion', 'Fashion'),
        ('food', 'Food'),
        ('fitness', 'Fitness'),
        ('tech', 'Technology'),
        ('travel', 'Travel'),
        ('music', 'Music'),
        ('art', 'Art'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='creator_profile')
    bio = models.TextField()
    categories = models.ManyToManyField(CreatorCategory)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    portfolio_samples = models.JSONField(default=list)  # Post IDs
    available_for_collaboration = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    rating = models.FloatField(default=0.0)  # 0-5 stars
    verified_deliverables = models.PositiveIntegerField(default=0)
    
# creators/views.py
def creator_marketplace(request):
    category = request.GET.get('category')
    min_followers = request.GET.get('min_followers', 1000)
    
    creators = CreatorProfile.objects.filter(
        available_for_collaboration=True,
        user__followers__count__gte=min_followers,
    )
    
    if category:
        creators = creators.filter(categories__slug=category)
    
    creators = creators.order_by('-rating', '-verified_deliverables')
    
    return render(request, 'creators/marketplace.html', {
        'creators': creators,
    })
```

---

### 5.6 Subscription/Premium Tiers
**Description**: Patrons can subscribe to creators  
**Impact**: 📈 High | **Complexity**: ⭐⭐⭐⭐ Hard | **Effort**: 5-7 days

```python
# subscriptions/models.py
class CreatorSubscription(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='creator_subscriptions')
    tier_name = models.CharField(max_length=100)  # "Supporter", "VIP", "Exclusive"
    description = models.TextField()
    monthly_price = models.DecimalField(max_digits=8, decimal_places=2)
    benefits = models.JSONField()  # Early access, exclusive content, etc.
    max_subscribers = models.PositiveIntegerField(null=True, blank=True)  # Exclusive tier
    created_at = models.DateTimeField(auto_now_add=True)

class Subscription(models.Model):
    subscriber = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    tier = models.ForeignKey(CreatorSubscription, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[('active', 'Active'), ('cancelled', 'Cancelled'), ('expired', 'Expired')])
    start_date = models.DateTimeField(auto_now_add=True)
    renewal_date = models.DateTimeField()
    auto_renew = models.BooleanField(default=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

class ExclusiveContent(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    tier = models.ForeignKey(CreatorSubscription, on_delete=models.CASCADE)
    post = models.OneToOneField(Post, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
```

---

### 5.7 Tip/Donation System
**Description**: One-time tips from followers  
**Impact**: 📈 Medium | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 3-4 days

```python
# monetization/models.py
class Tip(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tips_received')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tips_sent')
    post = models.ForeignKey(Post, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    message = models.CharField(max_length=255, blank=True)
    is_anonymous = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

# Process payment via Stripe
@shared_task
def process_tip_payment(tip_id):
    """Process tip payment with Stripe."""
    import stripe
    from monetization.models import Tip
    
    tip = Tip.objects.get(id=tip_id)
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    try:
        charge = stripe.Charge.create(
            amount=int(tip.amount * 100),  # Cents
            currency='usd',
            source=tip.sender.payment_method,
            description=f'Tip for {tip.creator.username}',
        )
        
        tip.transaction_id = charge.id
        tip.save()
        
        # Add to creator's balance
        tip.creator.creator_fund.account_balance += tip.amount
        tip.creator.creator_fund.save()
        
    except stripe.error.CardError:
        tip.delete()  # Remove failed tip
```

---

## 🟡 F6: AI & Smart Features

### 6.1 AI-Powered Content Recommendations
**Description**: ML-based post recommendations using embeddings  
**Impact**: 🔥 Very High | **Complexity**: ⭐⭐⭐⭐ Hard | **Effort**: 6-8 days

```bash
pip install scikit-learn numpy sentence-transformers

# recommendations/ml_models.py
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class ContentRecommender:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def get_post_embedding(self, post):
        """Generate embedding for post content."""
        text = f"{post.content} {' '.join([tag.name for tag in post.hashtags.all()])}"
        return self.model.encode(text)
    
    def get_similar_posts(self, post, top_k=5):
        """Find similar posts."""
        from posts.models import Post
        
        post_embedding = self.get_post_embedding(post)
        all_posts = Post.objects.exclude(id=post.id)[:100]  # Sample for performance
        
        similarities = []
        for other in all_posts:
            other_embedding = self.get_post_embedding(other)
            similarity = cosine_similarity(
                [post_embedding],
                [other_embedding]
            )[0][0]
            similarities.append((other, similarity))
        
        return sorted(similarities, key=lambda x: x[1], reverse=True)[:top_k]

# views.py
@login_required
def recommended_posts(request):
    from recommendations.ml_models import ContentRecommender
    from posts.models import Post
    
    recommender = ContentRecommender()
    
    # Get user's recent posts they liked
    recent_likes = request.user.reactions.order_by('-created_at')[:10]
    
    recommendations = {}
    for reaction in recent_likes:
        similar = recommender.get_similar_posts(reaction.post, top_k=3)
        for post, score in similar:
            if post.id not in recommendations:
                recommendations[post.id] = (post, 0)
            _, existing_score = recommendations[post.id]
            recommendations[post.id] = (post, existing_score + score)
    
    # Sort and limit
    sorted_recs = sorted(
        recommendations.values(),
        key=lambda x: x[1],
        reverse=True
    )[:20]
    
    return render(request, 'recommendations/suggested.html', {
        'posts': [p[0] for p in sorted_recs]
    })
```

---

### 6.2 Auto-Caption Generation (AI)
**Description**: Generate post captions using GPT  
**Impact**: 📈 Medium | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 2-3 days

```bash
pip install openai

# posts/tasks.py
import openai

@shared_task
def generate_caption(post_id):
    """Generate caption using GPT for a post without caption."""
    from posts.models import Post
    
    post = Post.objects.get(id=post_id)
    
    if post.content:
        return  # Already has content
    
    openai.api_key = settings.OPENAI_API_KEY
    
    # Use image description if available
    image_description = "A nice photo"
    if post.image:
        # Could use image-to-text model here
        pass
    
    prompt = f"Write a creative and engaging social media caption for: {image_description}. Keep it under 150 characters. Include relevant hashtags."
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    
    post.content = response.choices[0].message.content
    post.save()
```

---

### 6.3 Hashtag Auto-Suggestion Based on Image Content
**Description**: Suggest hashtags by analyzing image  
**Impact**: 📈 Medium | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 3-4 days

```bash
pip install google-cloud-vision

# posts/tasks.py
from google.cloud import vision

@shared_task
def suggest_hashtags_from_image(post_id):
    """Analyze image and suggest hashtags."""
    from posts.models import Post, HashTag
    
    post = Post.objects.get(id=post_id)
    
    if not post.image:
        return
    
    client = vision.ImageAnnotatorClient()
    image = vision.Image(uri=post.image.url)
    
    # Detect labels
    response = client.label_detection(image=image)
    labels = [label.description for label in response.label_annotations]
    
    # Create/add hashtags
    for label in labels[:5]:
        tag, _ = HashTag.objects.get_or_create(name=label.lower())
        post.hashtags.add(tag)
```

---

### 6.4 Toxicity & NSFW Content Detection
**Description**: Auto-flag inappropriate content  
**Impact**: 📈 High | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 2-3 days

```bash
pip install perspective-api-client

# moderation/tasks.py
from googleapiclient import discovery

@shared_task
def check_content_toxicity(post_id):
    """Check post for toxic content using Google Perspective API."""
    from posts.models import Post
    from moderation.models import ContentFlag
    
    post = Post.objects.get(id=post_id)
    
    client = discovery.build(
        "commentanalyzer",
        "v1alpha1",
        developerKey=settings.GOOGLE_API_KEY
    )
    
    analyze_request = {
        "comment": {"text": post.content},
        "requestedAttributes": {
            "TOXICITY": {},
            "SEVERE_TOXICITY": {},
            "IDENTITY_ATTACK": {},
            "INSULT": {},
            "PROFANITY": {},
        }
    }
    
    response = client.comments().analyze(body=analyze_request).execute()
    
    for attr, score in response['attributeScores'].items():
        if score['summaryScore']['value'] > 0.7:
            ContentFlag.objects.create(
                content_type='post',
                content_id=post.id,
                reason='auto_flagged',
            )
            break
```

---

### 6.5 Smart Notification Timing
**Description**: Send notifications at optimal times  
**Impact**: 📈 Medium | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 3-4 days

```python
# notifications/tasks.py
@shared_task
def send_notification_at_optimal_time(notification_id):
    """Schedule notification for when user is most active."""
    from notifications.models import Notification
    from analytics.models import PageView
    from datetime import timedelta
    from django.utils import timezone
    import statistics
    
    notification = Notification.objects.get(id=notification_id)
    user = notification.recipient
    
    # Find user's most active hours
    last_30_days = timezone.now() - timedelta(days=30)
    page_views = PageView.objects.filter(
        user=user,
        created_at__gte=last_30_days
    )
    
    active_hours = [pv.created_at.hour for pv in page_views]
    
    if active_hours:
        most_active_hour = statistics.mode(active_hours)
        now = timezone.now()
        
        # Schedule for next occurrence of most active hour
        scheduled_time = now.replace(hour=most_active_hour, minute=0, second=0)
        if scheduled_time <= now:
            scheduled_time += timedelta(days=1)
        
        # Schedule task
        from celery import current_app
        current_app.send_task(
            'notifications.tasks.deliver_notification',
            args=[notification.id],
            eta=scheduled_time,
        )
```

---

### 6.6 Trend Prediction
**Description**: Predict which posts will go viral  
**Impact**: 📈 Medium | **Complexity**: ⭐⭐⭐⭐ Hard | **Effort**: 4-5 days

```python
# analytics/models.py
class PostViralityPrediction(models.Model):
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='virality_prediction')
    virality_score = models.FloatField()  # 0-100
    predicted_peak_time = models.DateTimeField()
    confidence = models.FloatField()  # 0-1
    created_at = models.DateTimeField(auto_now_add=True)

# tasks.py
@shared_task
def predict_post_virality(post_id, hours_since_creation=1):
    """Predict if post will go viral."""
    from posts.models import Post
    from analytics.models import PostViralityPrediction
    from datetime import timedelta
    from django.utils import timezone
    
    post = Post.objects.get(id=post_id)
    
    # Collect features
    features = {
        'initial_engagement': post.reaction_count() + post.comments.count(),
        'follower_count': post.author.followers.count(),
        'hashtag_count': post.hashtags.count(),
        'has_image': bool(post.image),
        'content_length': len(post.content),
    }
    
    # Simple prediction (in real world, use ML model)
    virality_score = (
        min(100, features['initial_engagement'] * 2) +
        min(100, features['follower_count'] / 100) +
        features['hashtag_count'] * 5 +
        (10 if features['has_image'] else 0) +
        (5 if 50 < features['content_length'] < 500 else 0)
    ) / 5
    
    # Predict peak time (typically 2-4 hours for viral posts)
    predicted_peak = post.created_at + timedelta(hours=3)
    
    PostViralityPrediction.objects.create(
        post=post,
        virality_score=min(100, virality_score),
        predicted_peak_time=predicted_peak,
        confidence=0.7,
    )
    
    if virality_score > 60:
        # Notify user their post might go viral
        Notification.objects.create(
            recipient=post.author,
            sender=User.objects.get(username='system'),
            notification_type='viral_prediction',
            post=post,
        )
```

---

### 6.7 Duplicate Content Detection
**Description**: Find reposted/copied content  
**Impact**: 📈 Medium | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 3-4 days

```python
# moderation/tasks.py
from difflib import SequenceMatcher

@shared_task
def detect_duplicate_content(post_id):
    """Detect duplicate/plagiarized content."""
    from posts.models import Post
    
    post = Post.objects.get(id=post_id)
    
    # Find similar posts
    all_posts = Post.objects.exclude(id=post.id, author=post.author)[:1000]
    
    for other_post in all_posts:
        similarity = SequenceMatcher(
            None,
            post.content,
            other_post.content
        ).ratio()
        
        if similarity > 0.8:  # Very similar
            # Flag as potential plagiarism
            Notification.objects.create(
                recipient=post.author,
                sender=User.objects.get(username='system'),
                notification_type='content_similarity',
                post=other_post,  # Link to original
            )
            break
```

---

### 6.8 Sentiment Analysis
**Description**: Analyze post sentiment (positive/negative)  
**Impact**: 📈 Low | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 2-3 days

```bash
pip install textblob vader-sentiment

# analytics/tasks.py
from textblob import TextBlob
from nltk.sentiment import SentimentIntensityAnalyzer

@shared_task
def analyze_post_sentiment(post_id):
    """Analyze post sentiment."""
    from posts.models import Post
    from analytics.models import PostAnalytics
    
    post = Post.objects.get(id=post_id)
    
    # Analyze sentiment
    analyzer = SentimentIntensityAnalyzer()
    scores = analyzer.polarity_scores(post.content)
    
    sentiment_label = 'neutral'
    if scores['compound'] > 0.05:
        sentiment_label = 'positive'
    elif scores['compound'] < -0.05:
        sentiment_label = 'negative'
    
    PostAnalytics.objects.create(
        post=post,
        sentiment=sentiment_label,
        sentiment_score=scores['compound'],
    )
```

---

## 🟡 F7: Integrations & Connectivity

### 7.1 Calendar Integration (Google Calendar, Outlook)
**Description**: Sync events with user calendars  
**Impact**: 📈 Low-Medium | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 3-4 days

```bash
pip install google-auth google-calendar-api

# events/integrations.py
from google.oauth2 import credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

def sync_event_to_google_calendar(event_id, user):
    """Sync ConnectSphere event to Google Calendar."""
    from events.models import Event
    
    event = Event.objects.get(id=event_id)
    creds = user.google_calendar_credentials
    
    service = build('calendar', 'v3', credentials=creds)
    
    event_body = {
        'summary': event.title,
        'description': event.description,
        'start': {'dateTime': event.start_datetime.isoformat()},
        'end': {'dateTime': event.end_datetime.isoformat()},
        'location': event.location,
    }
    
    if event.online_link:
        event_body['conferenceData'] = {
            'entryPoints': [{
                'uri': event.online_link,
                'entryPointType': 'more',
                'label': 'Join event',
            }]
        }
    
    service.events().insert(
        calendarId='primary',
        body=event_body,
        conferenceDataVersion=1,
    ).execute()
```

---

### 7.2 Spotify Integration (Share Songs/Playlists)
**Description**: Share Spotify tracks, create playlists  
**Impact**: 📈 Medium | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 3-4 days

```bash
pip install spotipy

# music/integrations.py
import spotipy
from spotipy.oauth2 import SpotifyOAuth

def share_spotify_track(user, track_id):
    """Create post with Spotify track embed."""
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=settings.SPOTIFY_CLIENT_ID,
            client_secret=settings.SPOTIFY_SECRET,
        )
    )
    
    track = sp.track(track_id)
    
    post = Post.objects.create(
        author=user,
        content=f"Currently vibing to {track['name']} by {track['artists'][0]['name']}",
        spotify_track_id=track_id,
        spotify_uri=track['uri'],
    )
    
    return post

# models.py
class Post(models.Model):
    # ... existing ...
    spotify_track_id = models.CharField(max_length=100, blank=True)
    spotify_uri = models.CharField(max_length=100, blank=True)
```

---

### 7.3 YouTube Integration (Share & Embed Videos)
**Description**: Embed YouTube videos in posts  
**Impact**: 📈 Medium | **Complexity**: ⭐⭐ Easy | **Effort**: 1-2 days

```python
# posts/models.py
class Post(models.Model):
    # ... existing ...
    youtube_video_id = models.CharField(max_length=50, blank=True)

# Template
{% if post.youtube_video_id %}
<iframe width="560" height="315"
  src="https://www.youtube.com/embed/{{ post.youtube_video_id }}"
  frameborder="0" allowfullscreen></iframe>
{% endif %}
```

---

### 7.4 Twitter/X Crossposting
**Description**: Auto-post to Twitter  
**Impact**: 📈 Medium | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 2-3 days

```bash
pip install tweepy

# posts/tasks.py
import tweepy

@shared_task
def crosspost_to_twitter(post_id):
    """Post ConnectSphere post to Twitter."""
    from posts.models import Post
    
    post = Post.objects.get(id=post_id)
    user = post.author
    
    # Get user's Twitter token
    if not hasattr(user, 'twitter_account'):
        return
    
    client = tweepy.Client(bearer_token=user.twitter_account.access_token)
    
    tweet_text = post.content[:280]
    if post.image:
        # Upload image to Twitter first
        pass
    
    response = client.create_tweet(text=tweet_text)
    
    # Store tweet ID
    post.twitter_tweet_id = response.data['id']
    post.save()
```

---

### 7.5 Discord Bot Integration
**Description**: Post updates to Discord servers  
**Impact**: 📈 Low | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 2-3 days

```bash
pip install discord.py

# integrations/discord_bot.py
import discord

class ConnectSphereBot(discord.Client):
    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
    
    async def on_message(self, message):
        if message.author == self.user:
            return
        
        # Listen for commands like !profile @username
        if message.content.startswith('!profile'):
            username = message.content.split()[1].replace('@', '')
            # Fetch user from ConnectSphere
            # Return profile info

intents = discord.Intents.default()
bot = ConnectSphereBot(intents=intents)
bot.run(settings.DISCORD_BOT_TOKEN)
```

---

### 7.6 Slack Integration (Team Sharing)
**Description**: Share posts to Slack channels  
**Impact**: 📈 Low | **Complexity**: ⭐⭐ Easy | **Effort**: 1-2 days

```bash
pip install slack-sdk

# integrations/slack.py
from slack_sdk import WebClient

def share_post_to_slack(post_id, slack_channel):
    """Share post to Slack channel."""
    from posts.models import Post
    
    post = Post.objects.get(id=post_id)
    
    client = WebClient(token=settings.SLACK_BOT_TOKEN)
    
    message = {
        'text': post.content,
        'blocks': [
            {
                'type': 'section',
                'text': {'type': 'mrkdwn', 'text': post.content},
            },
            {
                'type': 'context',
                'elements': [
                    {'type': 'mrkdwn', 'text': f"Posted by {post.author.username}"},
                ],
            },
        ],
    }
    
    if post.image:
        message['blocks'].insert(1, {
            'type': 'image',
            'image_url': post.image.url,
            'alt_text': 'Post image',
        })
    
    client.chat_postMessage(channel=slack_channel, **message)
```

---

### 7.7 Stripe Payments Integration
**Description**: Handle all payment processing  
**Impact**: 🔥 Very High | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 3-4 days

(Already mentioned in monetization sections)

---

### 7.8 Twilio SMS Notifications
**Description**: Send SMS for important notifications  
**Impact**: 📈 Low | **Complexity**: ⭐⭐ Easy | **Effort**: 1-2 days

```bash
pip install twilio

# notifications/sms.py
from twilio.rest import Client

def send_sms_notification(user, message):
    """Send SMS notification."""
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    client = Client(account_sid, auth_token)
    
    if not hasattr(user, 'phone_number'):
        return
    
    message = client.messages.create(
        body=message,
        from_=settings.TWILIO_PHONE_NUMBER,
        to=user.phone_number,
    )
```

---

### 7.9 QR Code Generation for Events
**Description**: Generate QR codes for event registration  
**Impact**: 📈 Low | **Complexity**: ⭐ Very Easy | **Effort**: 1 day

```python
# events/models.py
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile

class Event(models.Model):
    # ... existing ...
    qr_code = models.ImageField(upload_to='event_qr_codes/', null=True, blank=True)
    
    def generate_qr_code(self):
        """Generate QR code for event registration."""
        qr = qrcode.QRCode(version=1)
        qr.add_data(f"{settings.SITE_URL}/events/{self.id}/register/")
        qr.make(fit=True)
        
        img = qr.make_image()
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        self.qr_code.save(
            f'event_{self.id}.png',
            ContentFile(buffer.read()),
            save=False
        )
```

---

## 🟠 F8: Mobile & Native Features

### 8.1 Push Notifications (Firebase)
**Description**: Mobile push notifications  
**Impact**: 🔥 Very High | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 3-4 days

```bash
pip install firebase-admin

# notifications/tasks.py
import firebase_admin
from firebase_admin import messaging

@shared_task
def send_push_notification(notification_id):
    """Send push notification via Firebase."""
    from notifications.models import Notification
    
    notification = Notification.objects.get(id=notification_id)
    
    # Get user's FCM tokens
    tokens = notification.recipient.fcm_tokens.all()
    
    if not tokens:
        return
    
    for token_obj in tokens:
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=f"{notification.sender.username} sent a notification",
                body=notification.get_notification_message(),
            ),
            data={
                'notification_id': str(notification.id),
                'type': notification.notification_type,
            },
            tokens=[token_obj.token],
        )
        
        messaging.send_multicast(message)
```

---

### 8.2 App Deep Linking
**Description**: Open app to specific screens from URLs  
**Impact**: 📈 Medium | **Complexity**: ⭐⭐ Easy | **Effort**: 2 days

```bash
# configure app://connectsphere.com/* deep links

# urls.py
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET"])
def deep_link(request, content_type, content_id):
    """Handle deep links."""
    context = {
        'content_type': content_type,  # post, user, group, event
        'content_id': content_id,
        'app_schemes': {
            'ios': 'connectsphere://open',
            'android': 'connectsphere://',
        }
    }
    return render(request, 'deep_link.html', context)
```

---

### 8.3 Offline Mode (Background Sync)
**Description**: Sync posts when online after offline creation  
**Impact**: 📈 Medium | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 3-4 days

```python
# posts/models.py
class DraftPost(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='draft_posts')
    content = models.TextField()
    image = models.ImageField(null=True, blank=True)
    synced = models.BooleanField(default=False)
    created_locally_at = models.DateTimeField()
    synced_at = models.DateTimeField(null=True, blank=True)

# tasks.py - Sync when connection restored
@shared_task
def sync_draft_posts():
    """Upload draft posts created offline."""
    from posts.models import DraftPost, Post
    
    unsyn = DraftPost.objects.filter(synced=False)
    
    for draft in unsync:
        try:
            post = Post.objects.create(
                author=draft.author,
                content=draft.content,
                image=draft.image,
            )
            draft.synced = True
            draft.synced_at = timezone.now()
            draft.save()
        except Exception as e:
            logger.error(f"Failed to sync draft {draft.id}: {e}")
```

---

### 8.4 Widget Integration (iOS/Android)
**Description**: App home screen widgets  
**Impact**: 📈 Medium | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 4-5 days

(Requires native iOS/Android development)

---

### 8.5 Watch App (Apple Watch)
**Description**: Minimal app for smartwatch  
**Impact**: 📈 Low | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 3-4 days

(Requires watchOS development)

---

## 🔴 F9: Monetization

### 9.1 Advertising System
**Description**: Ad placements in feed  
**Impact**: 🔥 Very High | **Complexity**: ⭐⭐⭐⭐ Hard | **Effort**: 6-8 days

```python
# advertising/models.py
class Advertisement(models.Model):
    PLACEMENT_TYPES = [
        ('feed', 'Feed'),
        ('sidebar', 'Sidebar'),
        ('story', 'Story'),
        ('reel', 'Reel'),
    ]
    
    advertiser = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ads')
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='ads/')
    link = models.URLField()
    placement_type = models.CharField(max_length=50, choices=PLACEMENT_TYPES)
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    target_age_min = models.IntegerField(null=True)
    target_age_max = models.IntegerField(null=True)
    target_locations = models.JSONField(default=list)
    target_interests = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class AdImpression(models.Model):
    ad = models.ForeignKey(Advertisement, on_delete=models.CASCADE, related_name='impressions')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='ad_impressions')
    created_at = models.DateTimeField(auto_now_add=True)

class AdClick(models.Model):
    ad = models.ForeignKey(Advertisement, on_delete=models.CASCADE, related_name='clicks')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

# views.py - Inject ads in feed
def home_feed(request):
    posts = Post.objects.all()
    
    # Insert ads every 5 posts
    feed_items = []
    for i, post in enumerate(posts):
        feed_items.append(('post', post))
        if (i + 1) % 5 == 0:
            ad = select_targeted_ad(request.user)
            if ad:
                feed_items.append(('ad', ad))
    
    return render(request, 'posts/home.html', {'feed_items': feed_items})
```

---

### 9.2 Premium Subscription Tiers
**Description**: Advanced features behind paywall  
**Impact**: 🔥 Very High | **Complexity**: ⭐⭐⭐⭐ Hard | **Effort**: 5-7 days

```python
# subscriptions/models.py
class SubscriptionTier(models.Model):
    name = models.CharField(max_length=100)  # Free, Pro, Premium
    price_monthly = models.DecimalField(max_digits=8, decimal_places=2)
    features = models.JSONField()  # List of feature keys
    description = models.TextField()
    color = models.CharField(max_length=7)  # Badge color

class UserSubscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    tier = models.ForeignKey(SubscriptionTier, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=[('active', 'Active'), ('cancelled', 'Cancelled'), ('expired', 'Expired')])
    start_date = models.DateTimeField(auto_now_add=True)
    renewal_date = models.DateTimeField()
    stripe_subscription_id = models.CharField(max_length=100, unique=True)

# Check features
def has_feature(user, feature):
    if user.is_staff:
        return True
    
    subscription = getattr(user, 'subscription', None)
    if not subscription:
        return False
    
    return feature in subscription.tier.features

# Decorator
def require_feature(feature):
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            if not has_feature(request.user, feature):
                return render(request, 'subscriptions/upgrade_required.html', {
                    'feature': feature
                })
            return func(request, *args, **kwargs)
        return wrapper
    return decorator

# Usage
@require_feature('scheduled_posts')
def schedule_post(request):
    # ...
```

---

### 9.3 NFT/Blockchain Features
**Description**: Mint posts as NFTs  
**Impact**: 📈 Medium | **Complexity**: ⭐⭐⭐⭐ Hard | **Effort**: 6-8 days

```bash
pip install web3 eth-brownie

# blockchain/nft.py
from web3 import Web3

class PostNFT:
    def __init__(self, contract_address, abi):
        self.web3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/...'))
        self.contract = self.web3.eth.contract(address=contract_address, abi=abi)
    
    def mint_post_as_nft(self, post, creator_address):
        """Mint a post as NFT."""
        metadata = {
            'name': post.content[:50],
            'description': post.content,
            'image': post.image.url,
            'attributes': [
                {'trait_type': 'Likes', 'value': post.reaction_count()},
                {'trait_type': 'Creator', 'value': creator_address},
            ]
        }
        
        # Upload to IPFS
        ipfs_hash = ipfs_client.add(json.dumps(metadata))
        
        # Mint NFT
        tx_hash = self.contract.functions.mint(
            creator_address,
            f"ipfs://{ipfs_hash}"
        ).transact()
        
        return tx_hash
```

---

### 9.4 Referral Program
**Description**: Earn rewards for referrals  
**Impact**: 📈 High | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 3-4 days

```python
# referrals/models.py
class ReferralCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referral_codes')
    code = models.CharField(max_length=20, unique=True)
    reward_amount = models.DecimalField(max_digits=8, decimal_places=2, default=10.0)
    max_uses = models.IntegerField(null=True, blank=True)
    uses = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

class Referral(models.Model):
    code = models.ForeignKey(ReferralCode, on_delete=models.CASCADE)
    referred_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referrers')
    referrer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referrals')
    reward_given = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

# Signal when referred user completes action
@receiver(post_save, sender=UserSubscription)
def distribute_referral_reward(sender, instance, created, **kwargs):
    """Give referrer reward when referred user subscribes."""
    if created and instance.tier.name != 'Free':
        referral = Referral.objects.filter(
            referred_user=instance.user,
            reward_given=False
        ).first()
        
        if referral:
            referrer_fund = referral.referrer.creator_fund
            referrer_fund.account_balance += referral.code.reward_amount
            referrer_fund.save()
            
            referral.reward_given = True
            referral.save()
```

---

### 9.5 Affiliate Program
**Description**: Earn commission on product sales  
**Impact**: 📈 Medium | **Complexity**: ⭐⭐⭐⭐ Hard | **Effort**: 5-6 days

(Similar to referral + product catalog)

---

### 9.6 In-App Purchases (Virtual Gifts)
**Description**: Send virtual gifts to creators  
**Impact**: 📈 High | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 3-4 days

```python
# gifts/models.py
class Gift(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50)  # Emoji
    price = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField()

class GiftTransaction(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gifts_sent')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gifts_received')
    gift = models.ForeignKey(Gift, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField(default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

# Process gift transaction
@shared_task
def process_gift_purchase(transaction_id):
    """Process virtual gift purchase."""
    from gifts.models import GiftTransaction
    import stripe
    
    transaction = GiftTransaction.objects.get(transaction_id=transaction_id)
    
    # Charge sender
    stripe.Charge.create(
        amount=int(transaction.total_amount * 100),
        currency='usd',
        source=transaction.sender.stripe_payment_method,
    )
    
    # Give recipient 70% (ConnectSphere takes 30% cut)
    recipient_amount = transaction.total_amount * 0.7
    transaction.recipient.creator_fund.account_balance += recipient_amount
    transaction.recipient.creator_fund.save()
```

---

## 🔴 F10: Accessibility & Inclusivity

### 10.1 Multi-Language Support (i18n)
**Description**: Support 20+ languages  
**Impact**: 📈 Very High | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 4-5 days

```bash
pip install django-rosetta

# settings.py
USE_I18N = True
LANGUAGE_CODE = 'en-us'

LANGUAGES = [
    ('en', 'English'),
    ('es', 'Spanish'),
    ('fr', 'French'),
    ('de', 'German'),
    ('zh-hans', 'Chinese Simplified'),
    ('ja', 'Japanese'),
    ('pt-br', 'Portuguese'),
    ('ru', 'Russian'),
    # ... add more
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# templates
{% load i18n %}
<h1>{% trans "Welcome to ConnectSphere" %}</h1>

# Python
from django.utils.translation import gettext as _
message = _("Post created successfully")
```

---

### 10.2 Dark Mode Accessibility (WCAG Compliant)
**Description**: High contrast mode for visually impaired  
**Impact**: 📈 High | **Complexity**: ⭐⭐ Easy | **Effort**: 2 days

```html
<!-- Template with high contrast -->
<style media="(prefers-contrast: more)">
    body {
        --text-color: #000000;
        --bg-color: #ffffff;
        --border-color: #000000;
        --border-width: 2px;
    }
    
    button {
        border: var(--border-width) solid var(--border-color);
        color: var(--text-color);
    }
</style>

<!-- Respect reduced motion -->
<style media="(prefers-reduced-motion: reduce)">
    * {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
</style>
```

---

### 10.3 Screen Reader Optimization
**Description**: Full ARIA labels and semantic HTML  
**Impact**: 📈 High | **Complexity**: ⭐⭐ Easy | **Effort**: 2-3 days

```html
<!-- Semantic HTML -->
<article class="post">
    <header>
        <h2>{{ post.title }}</h2>
        <time datetime="{{ post.created_at }}">{{ post.created_at|date }}</time>
    </header>
    
    <div role="main">
        <p>{{ post.content }}</p>
    </div>
    
    <footer>
        <button aria-label="Like this post ({{ post.reaction_count }} likes)">
            ❤️
        </button>
    </footer>
</article>

<!-- ARIA navigation -->
<nav aria-label="Main navigation">
    <ul>
        <li><a href="#home">Home</a></li>
        <li><a href="#explore">Explore</a></li>
    </ul>
</nav>
```

---

### 10.4 Keyboard Navigation
**Description**: Full keyboard support for all features  
**Impact**: 📈 High | **Complexity**: ⭐⭐ Easy | **Effort**: 2 days

```html
<!-- Skip links -->
<a href="#main-content" class="skip-link">Skip to main content</a>

<!-- Logical tab order -->
<nav>
    <a href="/" tabindex="1">Home</a>
    <a href="/explore" tabindex="2">Explore</a>
    <a href="/profile" tabindex="3">Profile</a>
</nav>

<!-- Focus styles -->
<style>
    button:focus, a:focus {
        outline: 3px solid #0066cc;
        outline-offset: 2px;
    }
</style>

<!-- Keyboard shortcuts documentation -->
<details>
    <summary>Keyboard shortcuts</summary>
    <ul>
        <li><kbd>J</kbd> - Next post</li>
        <li><kbd>K</kbd> - Previous post</li>
        <li><kbd>L</kbd> - Like</li>
        <li><kbd>?</kbd> - Show help</li>
    </ul>
</details>
```

---

### 10.5 Captions & Transcripts
**Description**: Auto-captions for all videos  
**Impact**: 📈 High | **Complexity**: ⭐⭐⭐ Medium | **Effort**: 2-3 days

(Already covered in video captions section)

---

### 10.6 Color Blind Friendly Design
**Description**: Avoid relying on color alone  
**Impact**: 📈 Medium | **Complexity**: ⭐⭐ Easy | **Effort**: 1-2 days

```css
/* Use patterns + color -->
.sentiment-positive {
    background: linear-gradient(45deg, #28a745 25%, transparent 25%);
    color: #ffffff;
}

.sentiment-negative {
    background: linear-gradient(45deg, #dc3545 25%, transparent 25%);
    color: #ffffff;
}

/* Emoji in reactions are better than colors alone */
```

---

### 10.7 Sign Language Video Support
**Description**: Add sign language interpretation  
**Impact**: 📈 Low | **Complexity**: ⭐⭐⭐⭐ Hard | **Effort**: 5+ days

(Requires professional sign language interpreters)

---

## 📊 Feature Summary Table

| Feature | Category | Effort | Impact | Priority |
|---------|----------|--------|--------|----------|
| Live Streaming | Social | ⭐⭐⭐⭐ | 🔥 Very High | 🔴 High |
| Nested Comments | Social | ⭐⭐ | 📈 Medium | 🔴 High |
| Creator Fund | Monetization | ⭐⭐⭐⭐ | 🔥 Very High | 🔴 High |
| Personalized Feed | Discovery | ⭐⭐⭐⭐ | 🔥 Very High | 🔴 High |
| Dark Mode++ | Accessibility | ⭐⭐ | 📈 High | 🔴 High |
| Full-Text Search | Discovery | ⭐⭐⭐ | 📈 High | 🔴 High |
| Video Captions | Accessibility | ⭐⭐⭐ | 📈 High | 🟠 Medium |
| Sponsorship System | Creator Economy | ⭐⭐⭐⭐ | 📈 High | 🟠 Medium |
| AI Recommendations | AI Features | ⭐⭐⭐⭐ | 📈 High | 🟠 Medium |
| Multi-Language | Accessibility | ⭐⭐⭐ | 📈 Very High | 🟡 Medium |

---

## 🚀 Phase 1 Quick Wins (Next 30 Days)

- [ ] Nested comments (reply to comments)
- [ ] Comment reactions
- [ ] Carousel posts (multi-image)
- [ ] Draft posts
- [ ] Smart hashtag suggestions
- [ ] Trending topics by region
- [ ] User mention autocomplete
- [ ] Message typing indicators
- [ ] Read receipts in messages
- [ ] Basic verification badges

---

## 📈 Phase 2 Medium-Term (60-90 Days)

- [ ] Live streaming
- [ ] Creator fund/monetization
- [ ] Personalized feed algorithm
- [ ] Full-text search
- [ ] Sponsorship system
- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Post scheduling
- [ ] Video processing & transcoding
- [ ] Webhook system

---

## 🎯 Phase 3 Long-Term (4-6 Months)

- [ ] React/Vue frontend modernization
- [ ] AI-powered content recommendations
- [ ] Elasticsearch integration
- [ ] Creator marketplace
- [ ] Premium subscription tiers
- [ ] Advertising system
- [ ] Mobile native apps
- [ ] Video editing tools
- [ ] Community groups with moderation
- [ ] Blockchain/NFT features

---

*Last Updated: June 19, 2026*
