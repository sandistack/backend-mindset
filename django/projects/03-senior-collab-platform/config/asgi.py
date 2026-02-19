"""
ASGI config for Senior Collaboration Platform.

Handles both HTTP and WebSocket connections.
"""

import os
from django.core.asgi import get_asgi_application

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django_asgi_app = get_asgi_application()

# Import routing after Django is initialized
from channels.routing import ProtocolTypeRouter, URLRouter
from apps.core.middleware.websocket_auth import JWTAuthMiddleware
from config.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddleware(
        URLRouter(websocket_urlpatterns)
    ),
})
