from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

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
