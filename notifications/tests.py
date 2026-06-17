from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from notifications.models import Notification

class NotificationsViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='user1', password='password123')
        self.user2 = User.objects.create_user(username='user2', password='password123')
        # Create notifications
        self.notif1 = Notification.objects.create(
            recipient=self.user1,
            sender=self.user2,
            notification_type='follow'
        )
        self.notif2 = Notification.objects.create(
            recipient=self.user1,
            sender=self.user2,
            notification_type='friend_request'
        )
        self.client.login(username='user1', password='password123')

    def test_notifications_list_view(self):
        """Test listing all notifications for user."""
        response = self.client.get(reverse('notifications_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notifications/notifications.html')
        self.assertEqual(response.context['notifications'].count(), 2)

    def test_mark_read_redirect(self):
        """Test marking a single notification as read redirects correctly."""
        response = self.client.post(reverse('mark_read', kwargs={'pk': self.notif1.pk}))
        self.assertEqual(response.status_code, 302) # Redirects to notifications list
        self.notif1.refresh_from_db()
        self.assertTrue(self.notif1.is_read)

    def test_mark_read_ajax(self):
        """Test marking a single notification as read returns JSON for AJAX requests."""
        response = self.client.post(
            reverse('mark_read', kwargs={'pk': self.notif1.pk}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.notif1.refresh_from_db()
        self.assertTrue(self.notif1.is_read)

    def test_mark_all_read(self):
        """Test marking all notifications as read."""
        response = self.client.post(reverse('mark_all_read'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Notification.objects.filter(recipient=self.user1, is_read=False).count(), 0)

    def test_unread_count(self):
        """Test fetching unread notification count via AJAX."""
        response = self.client.get(reverse('unread_count'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['unread_count'], 2)
