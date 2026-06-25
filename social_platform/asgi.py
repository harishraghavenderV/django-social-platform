"""
ASGI config for social_platform project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'social_platform.settings')
import django
django.setup()

import messaging.routing
import notifications.routing
import posts.routing

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            messaging.routing.websocket_urlpatterns
            + notifications.routing.websocket_urlpatterns
            + posts.routing.websocket_urlpatterns
        )
    ),
})
