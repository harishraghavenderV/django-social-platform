from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from posts.models import Post, Comment
from friends.models import FriendRequest, Follow

class APITestSuite(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(username='user1', password='password123')
        self.user2 = User.objects.create_user(username='user2', password='password123')
        self.client.force_authenticate(user=self.user1)
        
        # Verify userprofiles exist
        self.profile1 = self.user1.userprofile
        self.profile2 = self.user2.userprofile

    def test_post_viewset_list(self):
        """Test fetching posts feed via api."""
        Post.objects.create(author=self.user1, content='My post')
        response = self.client.get('/api/posts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if isinstance(response.data, dict) and 'results' in response.data:
            self.assertEqual(len(response.data['results']), 1)
            self.assertEqual(response.data['results'][0]['content'], 'My post')
        else:
            self.assertEqual(len(response.data), 1)
            self.assertEqual(response.data[0]['content'], 'My post')

    def test_post_viewset_create(self):
        """Test creating post via api."""
        data = {'content': 'API post'}
        response = self.client.post('/api/posts/', data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(Post.objects.first().content, 'API post')

    def test_post_like_action(self):
        """Test reacting to a post via api action."""
        # Follow user2 so their posts are in user1's feed
        Follow.objects.create(follower=self.user1, following=self.user2)
        post = Post.objects.create(author=self.user2, content='User2 post')
        
        response = self.client.post(f'/api/posts/{post.id}/react/', data={'reaction_type': 'like'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['reacted'], True)
        self.assertEqual(response.data['reaction_type'], 'like')
        self.assertEqual(post.reaction_count(), 1)

    def test_post_comment_action(self):
        """Test commenting on a post via api action (post must be in user's feed/following)."""
        # Follow user2 so their posts are in user1's feed
        Follow.objects.create(follower=self.user1, following=self.user2)
        post = Post.objects.create(author=self.user2, content='User2 post')
        
        data = {'content': 'My API comment'}
        response = self.client.post(f'/api/posts/{post.id}/comment/', data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 1)

    def test_profile_follow_action(self):
        """Test following/unfollowing a profile via api action."""
        response = self.client.post(f'/api/profiles/{self.user2.username}/follow/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['followed'], True)
        self.assertTrue(Follow.objects.filter(follower=self.user1, following=self.user2).exists())

        # Unfollow
        response = self.client.post(f'/api/profiles/{self.user2.username}/follow/')
        self.assertEqual(response.data['followed'], False)

    def test_profile_send_friend_request_action(self):
        """Test sending friend request via profile api action."""
        response = self.client.post(f'/api/profiles/{self.user2.username}/send-friend-request/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FriendRequest.objects.count(), 1)
        self.assertEqual(FriendRequest.objects.first().status, 'pending')

    def test_accept_friend_request_api(self):
        """Test accepting a friend request via API viewset."""
        req = FriendRequest.objects.create(sender=self.user2, receiver=self.user1, status='pending')
        response = self.client.post(f'/api/friend-requests/{req.id}/accept/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        req.refresh_from_db()
        self.assertEqual(req.status, 'accepted')
        self.assertTrue(Follow.objects.filter(follower=self.user1, following=self.user2).exists())

    def test_decline_friend_request_api(self):
        """Test declining a friend request via API viewset."""
        req = FriendRequest.objects.create(sender=self.user2, receiver=self.user1, status='pending')
        response = self.client.post(f'/api/friend-requests/{req.id}/decline/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(FriendRequest.objects.filter(id=req.id).exists())

    def test_cancel_friend_request_api(self):
        """Test cancelling a friend request via API viewset."""
        req = FriendRequest.objects.create(sender=self.user1, receiver=self.user2, status='pending')
        response = self.client.post(f'/api/friend-requests/{req.id}/cancel/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(FriendRequest.objects.filter(id=req.id).exists())
