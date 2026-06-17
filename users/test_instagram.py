from unittest.mock import MagicMock, patch
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.management import call_command
from users.models_instagram import InstagramAccount
from users import instagram_service
from posts.models import Post

@override_settings(INSTAGRAM_USERNAME='test_user_ig_real', INSTAGRAM_PASSWORD='test_password')
class InstagramServiceTestCase(TestCase):
    @patch('instagrapi.Client')
    def test_get_connection_info(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock account_info
        mock_info = MagicMock()
        mock_info.username = 'test_user_ig'
        mock_info.full_name = 'Test User IG'
        mock_info.follower_count = 1500
        mock_info.following_count = 200
        mock_info.media_count = 45
        mock_info.profile_pic_url = 'http://example.com/pic.jpg'
        mock_info.is_private = False
        mock_client.account_info.return_value = mock_info
        
        info = instagram_service.get_connection_info()
        self.assertEqual(info['username'], 'test_user_ig')
        self.assertEqual(info['follower_count'], 1500)
        self.assertEqual(info['media_count'], 45)
        
    @patch('instagrapi.Client')
    def test_fetch_user_media(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.user_id_from_username.return_value = '12345'
        
        # Mock media item
        mock_media = MagicMock()
        mock_media.id = '99999'
        mock_media.media_type = MagicMock()
        mock_media.media_type.name = 'IMAGE'
        mock_media.thumbnail_url = 'http://example.com/thumb.jpg'
        mock_media.video_url = ''
        mock_media.caption_text = 'Test caption #cool'
        mock_media.code = 'C_abc123'
        mock_media.like_count = 100
        mock_media.comment_count = 5
        mock_client.user_medias.return_value = [mock_media]
        
        results = instagram_service.fetch_user_media('test_user_ig')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], '99999')
        self.assertEqual(results[0]['caption'], 'Test caption #cool')
        self.assertEqual(results[0]['permalink'], 'https://www.instagram.com/p/C_abc123/')


@override_settings(INSTAGRAM_USERNAME='test_user_ig_real', INSTAGRAM_PASSWORD='test_password')
class InstagramViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client.login(username='testuser', password='password123')

    @patch('users.instagram_service.get_connection_info')
    @patch('users.instagram_service.fetch_user_media')
    def test_instagram_connect_success(self, mock_fetch, mock_info):
        mock_info.return_value = {
            'username': 'test_user_ig',
            'follower_count': 1000,
            'media_count': 10,
        }
        mock_fetch.return_value = [] # no posts to sync
        
        response = self.client.get(reverse('instagram_connect'))
        self.assertRedirects(response, reverse('profile_edit'))
        
        # Verify account created
        account = InstagramAccount.objects.get(user=self.user)
        self.assertEqual(account.ig_username, 'test_user_ig')
        self.assertTrue(account.is_active)

    def test_instagram_disconnect(self):
        # Create an account first
        account = InstagramAccount.objects.create(
            user=self.user,
            ig_user_id='123',
            ig_username='test_user_ig',
            access_token='test_token',
            is_active=True
        )
        
        response = self.client.post(reverse('instagram_disconnect'))
        self.assertRedirects(response, reverse('profile_edit'))
        
        # Verify deleted
        self.assertFalse(InstagramAccount.objects.filter(user=self.user).exists())

    @patch('users.instagram_service.fetch_user_media')
    def test_instagram_sync_now(self, mock_fetch):
        account = InstagramAccount.objects.create(
            user=self.user,
            ig_user_id='123',
            ig_username='test_user_ig',
            access_token='test_token',
            is_active=True
        )
        
        mock_fetch.return_value = [
            {
                'id': 'ig_post_1',
                'permalink': 'https://instagram.com/p/1/',
                'media_type': 'IMAGE',
                'url': 'http://example.com/1.jpg',
                'caption': 'Cool sync post #awesome',
            }
        ]
        
        # Mock download_media_to_file to return None (avoiding network download in tests)
        with patch('users.instagram_service.download_media_to_file', return_value=None):
            response = self.client.post(reverse('instagram_sync'))
            self.assertRedirects(response, reverse('profile_edit'))
            
            # Check post is created
            self.assertEqual(Post.objects.count(), 1)
            post = Post.objects.first()
            self.assertEqual(post.instagram_url, 'https://instagram.com/p/1/')
            self.assertEqual(post.content, 'Cool sync post #awesome')


@override_settings(INSTAGRAM_USERNAME='test_user_ig_real', INSTAGRAM_PASSWORD='test_password')
class InstagramCommandsTestCase(TestCase):
    @patch('users.instagram_service.get_connection_info')
    def test_refresh_instagram_tokens_command(self, mock_info):
        mock_info.return_value = {
            'username': 'test_user_ig',
            'follower_count': 1000,
            'media_count': 10,
        }
        
        # Call command
        call_command('refresh_instagram_tokens')
        mock_info.assert_called_once()

    @patch('users.instagram_service.fetch_oembed')
    def test_sync_instagram_feeds_public_command(self, mock_oembed):
        mock_oembed.return_value = {
            'html': '<blockquote>Mock embed</blockquote>',
            'author_name': 'test_creator'
        }
        
        call_command('sync_instagram_feeds', '--public-only')
        # Check that at least one public post was created
        self.assertTrue(Post.objects.filter(instagram_url__isnull=False).exists())

