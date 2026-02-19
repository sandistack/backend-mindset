"""
WebSocket URL routing configuration.
"""

from django.urls import path
from apps.documents.consumers import DocumentConsumer
from apps.channels.consumers import ChatConsumer
from apps.notifications.consumers import NotificationConsumer

websocket_urlpatterns = [
    path('ws/documents/<uuid:document_id>/', DocumentConsumer.as_asgi()),
    path('ws/channels/<uuid:channel_id>/', ChatConsumer.as_asgi()),
    path('ws/notifications/', NotificationConsumer.as_asgi()),
]
