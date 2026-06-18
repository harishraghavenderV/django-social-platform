from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from messaging.models import Conversation, Message

class MessagingViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Create users
        self.user1 = User.objects.create_user(username='user1', password='password123')
        self.user2 = User.objects.create_user(username='user2', password='password123')
        
        # Create a conversation
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user1, self.user2)

    def test_inbox_view(self):
        """Test inbox lists active conversations for authenticated user."""
        self.client.login(username='user1', password='password123')
        response = self.client.get(reverse('inbox'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'messaging/inbox.html')
        # Conversation is in list
        conversations_list = [item['conversation'] for item in response.context['conversations']]
        self.assertIn(self.conversation, conversations_list)

    def test_toggle_pin_conversation(self):
        """Test toggling pin status for a conversation."""
        self.client.login(username='user1', password='password123')
        
        # Pin it
        response = self.client.post(reverse('toggle_pin_conversation', kwargs={'conversation_id': self.conversation.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertTrue(response.json()['is_pinned'])
        self.assertTrue(self.conversation.pinned_by.filter(id=self.user1.id).exists())
        
        # Unpin it
        response = self.client.post(reverse('toggle_pin_conversation', kwargs={'conversation_id': self.conversation.id}))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['is_pinned'])
        self.assertFalse(self.conversation.pinned_by.filter(id=self.user1.id).exists())

    def test_change_chat_theme(self):
        """Test updating the conversation theme."""
        self.client.login(username='user1', password='password123')
        
        # Change to ocean
        response = self.client.post(
            reverse('change_chat_theme', kwargs={'conversation_id': self.conversation.id}),
            data={'theme': 'ocean'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(response.json()['theme'], 'ocean')
        
        self.conversation.refresh_from_db()
        self.assertEqual(self.conversation.theme, 'ocean')

        # Invalid theme should fail
        response = self.client.post(
            reverse('change_chat_theme', kwargs={'conversation_id': self.conversation.id}),
            data={'theme': 'invalid_theme'}
        )
        self.assertEqual(response.status_code, 400)
