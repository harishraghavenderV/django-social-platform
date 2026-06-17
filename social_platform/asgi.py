"""
ASGI config for social_platform project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'social_platform.settings')

# Import Django ASGI application early to ensure AppRegistry is populated
# before importing consumers and routing.
import django
django.setup()

