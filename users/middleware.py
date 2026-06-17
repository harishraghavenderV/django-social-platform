from django.shortcuts import redirect
from django.urls import reverse
from django_otp import user_has_device

class TwoFactorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Check if user has a confirmed 2FA device but is not verified in this session
            if not request.user.is_verified() and user_has_device(request.user):
                allowed_paths = [
                    reverse('verify_2fa'),
                    reverse('logout'),
                ]
                # Allow static/media assets and admin requests, but restrict standard routes
                if request.path not in allowed_paths and not request.path.startswith('/static/') and not request.path.startswith('/media/') and not request.path.startswith('/admin/'):
                    return redirect('verify_2fa')

        return self.get_response(request)
