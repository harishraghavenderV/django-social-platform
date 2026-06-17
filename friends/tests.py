from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from friends.models import FriendRequest, Follow
from notifications.models import Notification

class FriendsViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='user1', password='password123')
        self.user2 = User.objects.create_user(username='user2', password='password123')
        self.client.login(username='user1', password='password123')

    def test_send_friend_request(self):
        """Test sending a friend request creates relationship and notification."""
        response = self.client.post(reverse('send_friend_request', kwargs={'user_id': self.user2.id}))
        self.assertEqual(response.status_code, 302) # Redirects to profile
        self.assertEqual(FriendRequest.objects.count(), 1)
        req = FriendRequest.objects.first()
        self.assertEqual(req.sender, self.user1)
        self.assertEqual(req.receiver, self.user2)
        self.assertEqual(req.status, 'pending')
        # Check notification
        self.assertTrue(Notification.objects.filter(
            recipient=self.user2,
            sender=self.user1,
            notification_type='friend_request'
        ).exists())

    def test_accept_friend_request(self):
        """Test accepting friend request status change, auto-following, and notification."""
        req = FriendRequest.objects.create(sender=self.user2, receiver=self.user1, status='pending')
        response = self.client.post(reverse('accept_friend_request', kwargs={'request_id': req.id}))
        self.assertEqual(response.status_code, 302) # Redirects to friends list
        req.refresh_from_db()
        self.assertEqual(req.status, 'accepted')
        # Check auto follows
        self.assertTrue(Follow.objects.filter(follower=self.user1, following=self.user2).exists())
        self.assertTrue(Follow.objects.filter(follower=self.user2, following=self.user1).exists())
        # Check notification
        self.assertTrue(Notification.objects.filter(
            recipient=self.user2,
            sender=self.user1,
            notification_type='friend_accept'
        ).exists())

    def test_decline_friend_request(self):
        """Test declining friend request deletes the request."""
        req = FriendRequest.objects.create(sender=self.user2, receiver=self.user1, status='pending')
        response = self.client.post(reverse('decline_friend_request', kwargs={'request_id': req.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(FriendRequest.objects.count(), 0)

    def test_cancel_friend_request(self):
        """Test cancelling friend request from sender's side deletes the request."""
        req = FriendRequest.objects.create(sender=self.user1, receiver=self.user2, status='pending')
        response = self.client.post(reverse('cancel_friend_request', kwargs={'request_id': req.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(FriendRequest.objects.count(), 0)

    def test_remove_friend(self):
        """Test removing a friend deletes request and follow relationships."""
        req = FriendRequest.objects.create(sender=self.user1, receiver=self.user2, status='accepted')
        Follow.objects.create(follower=self.user1, following=self.user2)
        Follow.objects.create(follower=self.user2, following=self.user1)

        response = self.client.post(reverse('remove_friend', kwargs={'user_id': self.user2.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(FriendRequest.objects.count(), 0)
        self.assertEqual(Follow.objects.count(), 0)

    def test_follow_user(self):
        """Test following/unfollowing toggles Follow model and triggers notifications."""
        # Follow user2
        response = self.client.post(reverse('follow_user', kwargs={'user_id': self.user2.id}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Follow.objects.filter(follower=self.user1, following=self.user2).exists())
        self.assertTrue(Notification.objects.filter(
            recipient=self.user2,
            sender=self.user1,
            notification_type='follow'
        ).exists())

        # Unfollow user2
        response = self.client.post(reverse('follow_user', kwargs={'user_id': self.user2.id}))
        self.assertFalse(Follow.objects.filter(follower=self.user1, following=self.user2).exists())

    def test_friends_list_view(self):
        """Test friends list page contains pending requests and friends."""
        FriendRequest.objects.create(sender=self.user2, receiver=self.user1, status='pending')
        response = self.client.get(reverse('friends_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'friends/friends.html')
        self.assertEqual(response.context['received_requests'].count(), 1)
