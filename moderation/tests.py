from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Block, Report
from friends.models import Follow, FriendRequest
from posts.models import Post

class ModerationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='user1', password='password123')
        self.user2 = User.objects.create_user(username='user2', password='password123')
        self.user3 = User.objects.create_user(username='user3', password='password123')
        
    def test_block_user_toggle(self):
        """Test blocking and unblocking a user, and connection cleanup."""
        self.client.login(username='user1', password='password123')
        
        # Setup followers and friend requests to check cleanup
        Follow.objects.create(follower=self.user1, following=self.user2)
        Follow.objects.create(follower=self.user2, following=self.user1)
        FriendRequest.objects.create(sender=self.user1, receiver=self.user2, status='pending')
        
        # Block user2
        response = self.client.post(reverse('moderation:toggle_block', kwargs={'username': 'user2'}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['blocked'], True)
        
        # Verify Block object exists
        self.assertTrue(Block.objects.filter(blocker=self.user1, blocked=self.user2).exists())
        
        # Verify cleanups happened
        self.assertFalse(Follow.objects.filter(follower=self.user1, following=self.user2).exists())
        self.assertFalse(Follow.objects.filter(follower=self.user2, following=self.user1).exists())
        self.assertFalse(FriendRequest.objects.filter(sender=self.user1, receiver=self.user2).exists())
        
        # Unblock user2
        response = self.client.post(reverse('moderation:toggle_block', kwargs={'username': 'user2'}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['blocked'], False)
        
        # Verify Block object deleted
        self.assertFalse(Block.objects.filter(blocker=self.user1, blocked=self.user2).exists())

    def test_cannot_block_self(self):
        """Test that a user cannot block themselves."""
        self.client.login(username='user1', password='password123')
        response = self.client.post(reverse('moderation:toggle_block', kwargs={'username': 'user1'}))
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])

    def test_blocked_list_view(self):
        """Test viewing blocked users list."""
        self.client.login(username='user1', password='password123')
        Block.objects.create(blocker=self.user1, blocked=self.user2)
        
        response = self.client.get(reverse('moderation:blocked_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moderation/blocked_list.html')
        self.assertIn(self.user2, response.context['blocked_users'])

    def test_blocked_profile_returns_404(self):
        """Test that blocked/blocker profile detail pages return 404."""
        Block.objects.create(blocker=self.user1, blocked=self.user2)
        
        # Blocker user1 logged in, trying to view blocked user2 profile -> 404
        self.client.login(username='user1', password='password123')
        response = self.client.get(reverse('profile', kwargs={'username': 'user2'}))
        self.assertEqual(response.status_code, 404)
        
        # Blocked user2 logged in, trying to view blocker user1 profile -> 404
        self.client.login(username='user2', password='password123')
        response = self.client.get(reverse('profile', kwargs={'username': 'user1'}))
        self.assertEqual(response.status_code, 404)

    def test_feed_exclusion(self):
        """Test that blocked users' posts are excluded from the feed."""
        # user1 follows user2 so user2's posts can appear in the feed
        Follow.objects.create(follower=self.user1, following=self.user2)
        
        # Create a post for user2
        post = Post.objects.create(author=self.user2, content="Hello from user2")
        
        self.client.login(username='user1', password='password123')
        
        # Before blocking
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello from user2")
        
        # Block user2 via AJAX view
        response = self.client.post(reverse('moderation:toggle_block', kwargs={'username': 'user2'}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['blocked'], True)
        
        # After blocking
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Hello from user2")

    def test_report_content(self):
        """Test submitting a report for a post."""
        post = Post.objects.create(author=self.user2, content="Bad content")
        self.client.login(username='user1', password='password123')
        
        data = {
            'report_type': 'post',
            'content_id': post.id,
            'reason': 'This post is offensive'
        }
        response = self.client.post(reverse('moderation:report_content'), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        
        # Verify Report object exists
        self.assertTrue(Report.objects.filter(
            reporter=self.user1,
            report_type='post',
            content_id=post.id,
            reason='This post is offensive'
        ).exists())

    def test_report_content_invalid(self):
        """Test submitting invalid report data."""
        self.client.login(username='user1', password='password123')
        
        # Invalid report type
        data = {
            'report_type': 'invalid_type',
            'content_id': 1,
            'reason': 'Some reason'
        }
        response = self.client.post(reverse('moderation:report_content'), data=data)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])
        
        # Empty reason
        data = {
            'report_type': 'post',
            'content_id': 1,
            'reason': ''
        }
        response = self.client.post(reverse('moderation:report_content'), data=data)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])
