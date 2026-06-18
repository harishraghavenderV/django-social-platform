from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

class UsersViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword123',
            email='testuser@example.com'
        )
        # Verify userprofile is auto-created by signals
        self.profile = self.user.userprofile

    def test_register_view_get(self):
        """Test GET request to register page returns a 200 and uses correct template."""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')

    def test_register_view_post_valid(self):
        """Test POST request with valid registration data creates a user and redirects."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'newpassword123',
            'password2': 'newpassword123',
        }
        response = self.client.post(reverse('register'), data=data)
        # Should redirect to home
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_profile_view_authenticated(self):
        """Test profile page for a user is accessible when logged in."""
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.get(reverse('profile', kwargs={'username': 'testuser'}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile.html')
        self.assertEqual(response.context['view_user'], self.user)
        self.assertEqual(response.context['profile'], self.profile)

    def test_profile_edit_get(self):
        """Test profile edit page is accessible for authenticated users."""
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.get(reverse('profile_edit'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile_edit.html')

    def test_profile_edit_post(self):
        """Test updating profile details via POST request."""
        self.client.login(username='testuser', password='testpassword123')
        data = {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'testuser@example.com',
            'bio': 'New bio text',
            'location': 'New York',
            'website': 'https://example.com'
        }
        response = self.client.post(reverse('profile_edit'), data=data)
        # Should redirect to profile page
        self.assertRedirects(response, reverse('profile', kwargs={'username': 'testuser'}))
        # Refresh from database
        self.user.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Test')
        self.assertEqual(self.profile.bio, 'New bio text')
        self.assertEqual(self.profile.location, 'New York')

    def test_password_reset_flow(self):
        """Test the password reset flow end-to-end."""
        # 1. Trigger reset request
        response = self.client.post(reverse('password_reset'), {'email': 'testuser@example.com'})
        # Should redirect to password reset done
        self.assertRedirects(response, reverse('password_reset_done'))
        
        # Check that one email was "sent" (to console/locmem backend)
        from django.core import mail
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('testuser@example.com', mail.outbox[0].to)
        
        # 2. Verify confirmation page loading
        body = mail.outbox[0].body
        import re
        match = re.search(r'/password-reset-confirm/([^/]+)/([^/]+)/', body)
        self.assertIsNotNone(match)
        uidb64 = match.group(1)
        token = match.group(2)
        
        # Access password reset confirm page and follow the redirect to set-password
        response = self.client.get(reverse('password_reset_confirm', kwargs={'uidb64': uidb64, 'token': token}), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/password_reset_confirm.html')
        
        # 3. Submit new password to the tokenless set-password URL
        response = self.client.post(reverse('password_reset_confirm', kwargs={'uidb64': uidb64, 'token': 'set-password'}), {
            'new_password1': 'newsecurepass123',
            'new_password2': 'newsecurepass123',
        })
        self.assertRedirects(response, reverse('password_reset_complete'))
        
        # Try to log in with new password
        login_success = self.client.login(username='testuser', password='newsecurepass123')
        self.assertTrue(login_success)

    def test_2fa_setup_and_verify_flow(self):
        """Test enabling 2FA, verification challenge, and disabling 2FA."""
        # 1. Access setup 2FA (requires login)
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.get(reverse('setup_2fa'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/2fa_setup.html')
        self.assertIn('qr_uri', response.context)
        
        # 2. Verify unconfirmed TOTP device exists
        from django_otp.plugins.otp_totp.models import TOTPDevice
        device = TOTPDevice.objects.get(user=self.user, confirmed=False)
        
        # 3. Simulate invalid code submission
        response = self.client.post(reverse('setup_2fa'), {'token': '000000'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['success'])
        
        # 4. Simulate valid code submission
        import unittest.mock as mock
        with mock.patch('django_otp.plugins.otp_totp.models.TOTPDevice.verify_token', return_value=True):
            response = self.client.post(reverse('setup_2fa'), {'token': '123456'})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()['success'])
            
        # Verify device is now confirmed
        device.refresh_from_db()
        self.assertTrue(device.confirmed)
        
        # 5. Test 2FA middleware restriction
        # Log out, then log in using standard login (which is model-authenticated but not 2FA-verified)
        self.client.logout()
        self.client.login(username='testuser', password='testpassword123')
        
        # Access profile settings (should be redirected to verify_2fa by middleware)
        response = self.client.get(reverse('profile_edit'))
        self.assertRedirects(response, reverse('verify_2fa'))
        
        # 6. Verify 2FA challenge page
        response = self.client.get(reverse('verify_2fa'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/2fa_verify.html')
        
        # 7. Submit valid 2FA code to verify challenge page
        with mock.patch('django_otp.plugins.otp_totp.models.TOTPDevice.verify_token', return_value=True):
            response = self.client.post(reverse('verify_2fa'), {'token': '123456'})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()['success'])
            
        # Now accessing profile settings should be allowed (no redirect)
        response = self.client.get(reverse('profile_edit'))
        self.assertEqual(response.status_code, 200)
        
        # 8. Disable 2FA
        response = self.client.post(reverse('disable_2fa'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        
        # Verify device deleted
        self.assertFalse(TOTPDevice.objects.filter(user=self.user).exists())

    def test_profile_edit_interest_tags_valid(self):
        """Test updating profile with valid interest tags (<= 5)."""
        self.client.login(username='testuser', password='testpassword123')
        data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'interest_tags': 'Python, Django, WebDev, Design, Testing'
        }
        response = self.client.post(reverse('profile_edit'), data=data)
        self.assertRedirects(response, reverse('profile', kwargs={'username': 'testuser'}))
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.interest_tags, 'Python, Django, WebDev, Design, Testing')

    def test_profile_edit_interest_tags_invalid(self):
        """Test that updating profile with > 5 interest tags fails validation."""
        self.client.login(username='testuser', password='testpassword123')
        data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'interest_tags': 'Python, Django, WebDev, Design, Testing, Overflow'
        }
        response = self.client.post(reverse('profile_edit'), data=data)
        self.assertEqual(response.status_code, 200)
        form = response.context['profile_form']
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['interest_tags'], ['You can add up to 5 interest tags only.'])
        self.profile.refresh_from_db()
        self.assertNotEqual(self.profile.interest_tags, 'Python, Django, WebDev, Design, Testing, Overflow')




