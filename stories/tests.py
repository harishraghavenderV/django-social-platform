from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import Story, StoryView
from friends.models import Follow


class StoryViewsTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='password123')
        self.user2 = User.objects.create_user(username='user2', password='password123')
        
        # user1 follows user2
        Follow.objects.create(follower=self.user1, following=self.user2)
        
        # Create profile verification/setup
        self.user1.userprofile.save()
        self.user2.userprofile.save()

        # Create active story for user2
        self.story2 = Story.objects.create(
            author=self.user2,
            image='dummy.jpg',
            caption='Story 2 content',
            expires_at=timezone.now() + timedelta(hours=24)
        )

    def test_story_data_shows_has_unviewed(self):
        """Test story_data view returns u.has_unviewed = True for active unviewed stories."""
        self.client.login(username='user1', password='password123')
        response = self.client.get(reverse('story_data'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify user2 is returned with has_unviewed=True
        story_users = data.get('story_users', [])
        user2_data = next((u for u in story_users if u['user_id'] == self.user2.id), None)
        self.assertIsNotNone(user2_data)
        self.assertTrue(user2_data['has_unviewed'])

    def test_viewing_story_creates_story_view_and_updates_story_data(self):
        """Test that viewing stories logs StoryView and sets has_unviewed to False."""
        self.client.login(username='user1', password='password123')
        
        # Initially unviewed
        self.assertFalse(StoryView.objects.filter(story=self.story2, viewer=self.user1).exists())
        
        # View stories
        view_url = reverse('view_stories', kwargs={'user_id': self.user2.id})
        response = self.client.get(view_url)
        self.assertEqual(response.status_code, 200)
        
        # Check StoryView record exists
        self.assertTrue(StoryView.objects.filter(story=self.story2, viewer=self.user1).exists())
        
        # story_data should now return has_unviewed = False for user2
        response = self.client.get(reverse('story_data'))
        data = response.json()
        story_users = data.get('story_users', [])
        user2_data = next((u for u in story_users if u['user_id'] == self.user2.id), None)
        self.assertIsNotNone(user2_data)
        self.assertFalse(user2_data['has_unviewed'])
