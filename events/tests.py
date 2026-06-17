from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import Event, EventRSVP

class EventsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='user1', password='password123')
        self.user2 = User.objects.create_user(username='user2', password='password123')
        
        # Create an event
        self.event = Event.objects.create(
            creator=self.user1,
            title="Django Meetup",
            description="Talking about Django 6.0 features.",
            start_datetime=timezone.now() + timedelta(days=1),
            end_datetime=timezone.now() + timedelta(days=1, hours=2),
            location="Boston, MA"
        )

    def test_event_list_unauthenticated(self):
        """Test that unauthenticated users are redirected to login."""
        response = self.client.get(reverse('events:event_list'))
        self.assertEqual(response.status_code, 302)

    def test_event_list_authenticated(self):
        """Test retrieving the event list view."""
        self.client.login(username='user1', password='password123')
        response = self.client.get(reverse('events:event_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/event_list.html')
        self.assertIn('events', response.context)
        self.assertEqual(len(response.context['events']), 1)

    def test_create_event_get(self):
        """Test retrieving the create event page."""
        self.client.login(username='user1', password='password123')
        response = self.client.get(reverse('events:create_event'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/create_event.html')

    def test_create_event_post(self):
        """Test submitting the form to create a new event."""
        self.client.login(username='user1', password='password123')
        start = timezone.now() + timedelta(days=2)
        end = start + timedelta(hours=3)
        data = {
            'title': 'Hackathon 2026',
            'description': 'Building agentic AI tools.',
            'start_datetime': start.strftime('%Y-%m-%dT%H:%M'),
            'end_datetime': end.strftime('%Y-%m-%dT%H:%M'),
            'location': 'Virtual',
            'is_online': True,
            'online_link': 'https://zoom.us/j/123456789'
        }
        response = self.client.post(reverse('events:create_event'), data=data)
        self.assertEqual(response.status_code, 302)  # Redirects to detail view
        self.assertEqual(Event.objects.count(), 2)
        self.assertTrue(Event.objects.filter(title='Hackathon 2026').exists())
        
        # Verify creator is automatically RSVPed as going
        new_event = Event.objects.get(title='Hackathon 2026')
        self.assertTrue(EventRSVP.objects.filter(event=new_event, user=self.user1, status='going').exists())

    def test_event_detail(self):
        """Test retrieving the event detail view."""
        self.client.login(username='user1', password='password123')
        response = self.client.get(reverse('events:event_detail', kwargs={'pk': self.event.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/event_detail.html')
        self.assertEqual(response.context['event'], self.event)

    def test_event_rsvp_toggle(self):
        """Test performing and updating RSVP via AJAX."""
        self.client.login(username='user2', password='password123')
        
        # RSVP Going
        response = self.client.post(reverse('events:event_rsvp', kwargs={'pk': self.event.pk}), data={'status': 'going'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['success'], True)
        self.assertEqual(response.json()['current_status'], 'going')
        self.assertEqual(self.event.attendee_count(), 1)
        
        # Change to Interested
        response = self.client.post(reverse('events:event_rsvp', kwargs={'pk': self.event.pk}), data={'status': 'interested'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['current_status'], 'interested')
        self.assertEqual(self.event.attendee_count(), 0)
        
        # Remove RSVP
        response = self.client.post(reverse('events:event_rsvp', kwargs={'pk': self.event.pk}), data={'status': 'remove'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['current_status'], None)
        self.assertFalse(EventRSVP.objects.filter(event=self.event, user=self.user2).exists())
