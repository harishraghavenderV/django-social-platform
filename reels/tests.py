from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Reel, ReelComment

class ReelsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Create users
        self.user1 = User.objects.create_user(username='user1', password='password123')
        self.user2 = User.objects.create_user(username='user2', password='password123')
        
        # Mock video file
        self.video_content = b'fake video file content'
        self.video_file = SimpleUploadedFile(
            "test_reel.mp4", 
            self.video_content, 
            content_type="video/mp4"
        )
        
        # Create a reel
        self.reel = Reel.objects.create(
            author=self.user1,
            video=self.video_file,
            caption="Check out my first reel! #wow"
        )

    def test_reels_feed_unauthenticated(self):
        """Test that unauthenticated users are redirected to login."""
        response = self.client.get(reverse('reels:feed'))
        self.assertEqual(response.status_code, 302)

    def test_reels_feed_authenticated(self):
        """Test that authenticated users can view the reels feed."""
        self.client.login(username='user1', password='password123')
        response = self.client.get(reverse('reels:feed'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reels/feed.html')
        self.assertIn('reels', response.context)
        self.assertEqual(len(response.context['reels']), 1)

    def test_create_reel_get(self):
        """Test GET request to create reel view."""
        self.client.login(username='user1', password='password123')
        response = self.client.get(reverse('reels:create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reels/create.html')

    def test_create_reel_post(self):
        """Test POST request to upload a new reel."""
        self.client.login(username='user1', password='password123')
        new_video = SimpleUploadedFile("new_reel.mp4", b"new video data", content_type="video/mp4")
        data = {
            'video': new_video,
            'caption': 'Another amazing reel!'
        }
        response = self.client.post(reverse('reels:create'), data=data)
        self.assertEqual(response.status_code, 302)  # Redirects to feed
        self.assertEqual(Reel.objects.count(), 2)
        self.assertTrue(Reel.objects.filter(caption='Another amazing reel!').exists())

    def test_reel_detail(self):
        """Test viewing single reel detail view."""
        self.client.login(username='user1', password='password123')
        response = self.client.get(reverse('reels:detail', kwargs={'pk': self.reel.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reels/detail.html')
        self.assertEqual(response.context['reel'], self.reel)
        
        # Verify view count incremented
        self.reel.refresh_from_db()
        self.assertEqual(self.reel.view_count, 1)

    def test_reel_like_toggle(self):
        """Test AJAX liking and unliking of reels."""
        self.client.login(username='user2', password='password123')
        
        # Like the reel
        response = self.client.post(reverse('reels:like', kwargs={'pk': self.reel.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['liked'], True)
        self.assertEqual(self.reel.like_count(), 1)
        self.assertTrue(self.reel.likes.filter(id=self.user2.id).exists())

        # Unlike the reel
        response = self.client.post(reverse('reels:like', kwargs={'pk': self.reel.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['liked'], False)
        self.assertEqual(self.reel.like_count(), 0)

    def test_reel_comment(self):
        """Test adding comments to a reel via AJAX."""
        self.client.login(username='user2', password='password123')
        data = {
            'content': 'This is an awesome reel!',
            'ajax': 'true'
        }
        response = self.client.post(reverse('reels:comment', kwargs={'pk': self.reel.pk}), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['success'], True)
        self.assertEqual(ReelComment.objects.count(), 1)
        
        comment = ReelComment.objects.first()
        self.assertEqual(comment.content, 'This is an awesome reel!')
        self.assertEqual(comment.author, self.user2)
        self.assertEqual(comment.reel, self.reel)
