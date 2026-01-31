# 🔌 Step 2: Real-time WebSocket

**Waktu:** 8-10 jam  
**Prerequisite:** Step 1 selesai

---

## 🎯 Tujuan

- Django Channels setup
- WebSocket authentication
- Document collaboration consumer
- Chat channel consumer
- Notification consumer

---

## 📋 Tasks

### 2.1 JWT Authentication untuk WebSocket

**Buat `apps/core/middleware/websocket_auth.py`:**

```python
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model

User = get_user_model()

@database_sync_to_async
def get_user_from_token(token_string):
    try:
        token = AccessToken(token_string)
        user_id = token['user_id']
        return User.objects.get(id=user_id)
    except Exception:
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    JWT authentication for WebSocket connections.
    Token passed via query string: ws://host/ws/path/?token=xxx
    """
    
    async def __call__(self, scope, receive, send):
        # Get token from query string
        query_string = scope.get('query_string', b'').decode()
        query_params = dict(x.split('=') for x in query_string.split('&') if '=' in x)
        token = query_params.get('token', None)
        
        if token:
            scope['user'] = await get_user_from_token(token)
        else:
            scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)
```

**Update `config/asgi.py`:**

```python
from apps.core.middleware.websocket_auth import JWTAuthMiddleware

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddleware(
        URLRouter(websocket_urlpatterns)
    ),
})
```

### 2.2 Base Consumer

**Buat `apps/core/consumers.py`:**

```python
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

class BaseConsumer(AsyncJsonWebsocketConsumer):
    """Base consumer with common functionality"""
    
    async def connect(self):
        # Check authentication
        if self.scope['user'].is_anonymous:
            await self.close(code=4001)
            return
        
        self.user = self.scope['user']
        await self.on_connect()
    
    async def on_connect(self):
        """Override in subclass"""
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.on_disconnect(close_code)
    
    async def on_disconnect(self, close_code):
        """Override in subclass"""
        pass
    
    async def receive_json(self, content):
        """Route message to handler based on type"""
        message_type = content.get('type', '')
        handler = getattr(self, f'handle_{message_type}', None)
        
        if handler:
            await handler(content.get('data', {}))
        else:
            await self.send_error(f'Unknown message type: {message_type}')
    
    async def send_message(self, message_type, data):
        await self.send_json({
            'type': message_type,
            'data': data
        })
    
    async def send_error(self, message):
        await self.send_json({
            'type': 'error',
            'message': message
        })
```

### 2.3 Document Collaboration Consumer

**Buat `apps/documents/consumers.py`:**

```python
from channels.db import database_sync_to_async
from apps.core.consumers import BaseConsumer
from .models import Document
from .services import DocumentService

class DocumentConsumer(BaseConsumer):
    """
    WebSocket consumer untuk collaborative document editing.
    
    Messages:
    - join: Join document session
    - leave: Leave document session
    - update: Send document update
    - cursor: Send cursor position
    """
    
    async def on_connect(self):
        self.document_id = self.scope['url_route']['kwargs']['document_id']
        self.room_group_name = f'document_{self.document_id}'
        
        # Verify access
        has_access = await self.check_access()
        if not has_access:
            await self.close(code=4003)
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send current document state
        document = await self.get_document()
        await self.send_message('document_state', {
            'content': document.content,
            'version': document.version
        })
        
        # Notify others
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user_id': str(self.user.id),
                'user_name': self.user.name
            }
        )
    
    async def on_disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Notify others
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'user_id': str(self.user.id)
            }
        )
    
    # Message handlers
    async def handle_update(self, data):
        """Handle document update"""
        content = data.get('content')
        version = data.get('version')
        
        # Save to database
        new_version = await self.save_document(content, version)
        
        # Broadcast to all clients
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'document_updated',
                'content': content,
                'version': new_version,
                'user_id': str(self.user.id)
            }
        )
    
    async def handle_cursor(self, data):
        """Handle cursor position update"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'cursor_moved',
                'user_id': str(self.user.id),
                'user_name': self.user.name,
                'position': data.get('position')
            }
        )
    
    # Group message handlers (from channel_layer.group_send)
    async def user_joined(self, event):
        await self.send_message('user_joined', {
            'user_id': event['user_id'],
            'user_name': event['user_name']
        })
    
    async def user_left(self, event):
        await self.send_message('user_left', {
            'user_id': event['user_id']
        })
    
    async def document_updated(self, event):
        # Don't send to the user who made the change
        if event['user_id'] != str(self.user.id):
            await self.send_message('document_updated', {
                'content': event['content'],
                'version': event['version'],
                'user_id': event['user_id']
            })
    
    async def cursor_moved(self, event):
        if event['user_id'] != str(self.user.id):
            await self.send_message('cursor_moved', {
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'position': event['position']
            })
    
    # Database operations
    @database_sync_to_async
    def check_access(self):
        try:
            document = Document.objects.get(id=self.document_id)
            return document.workspace.members.filter(user=self.user).exists()
        except Document.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_document(self):
        return Document.objects.get(id=self.document_id)
    
    @database_sync_to_async
    def save_document(self, content, version):
        document = Document.objects.get(id=self.document_id)
        document.content = content
        document.version += 1
        document.save()
        
        # Create version history
        DocumentService.create_version(document, self.user)
        
        return document.version
```

**Referensi:** [WEBSOCKET.md](../../../docs/04-advanced/WEBSOCKET.md)

### 2.4 Chat Consumer

**Buat `apps/channels/consumers.py`:**

```python
from channels.db import database_sync_to_async
from apps.core.consumers import BaseConsumer
from .models import Channel, Message
from .serializers import MessageSerializer

class ChatConsumer(BaseConsumer):
    """
    WebSocket consumer untuk chat channel.
    
    Messages:
    - message: Send new message
    - typing: Typing indicator
    - read: Mark messages as read
    """
    
    async def on_connect(self):
        self.channel_id = self.scope['url_route']['kwargs']['channel_id']
        self.room_group_name = f'chat_{self.channel_id}'
        
        # Verify access
        has_access = await self.check_access()
        if not has_access:
            await self.close(code=4003)
            return
        
        # Join room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Update online status
        await self.set_online(True)
        await self.broadcast_presence()
    
    async def on_disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        await self.set_online(False)
        await self.broadcast_presence()
    
    async def handle_message(self, data):
        """Handle new message"""
        content = data.get('content')
        attachments = data.get('attachments', [])
        
        # Save message
        message = await self.save_message(content, attachments)
        message_data = await self.serialize_message(message)
        
        # Broadcast
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'new_message',
                'message': message_data
            }
        )
    
    async def handle_typing(self, data):
        """Handle typing indicator"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_typing',
                'user_id': str(self.user.id),
                'user_name': self.user.name,
                'is_typing': data.get('is_typing', False)
            }
        )
    
    # Group handlers
    async def new_message(self, event):
        await self.send_message('message', event['message'])
    
    async def user_typing(self, event):
        if event['user_id'] != str(self.user.id):
            await self.send_message('typing', {
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'is_typing': event['is_typing']
            })
    
    # Database operations
    @database_sync_to_async
    def check_access(self):
        try:
            channel = Channel.objects.get(id=self.channel_id)
            if channel.type == 'public':
                return channel.workspace.members.filter(user=self.user).exists()
            return channel.members.filter(user=self.user).exists()
        except Channel.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, content, attachments):
        channel = Channel.objects.get(id=self.channel_id)
        return Message.objects.create(
            channel=channel,
            user=self.user,
            content=content,
            attachments=attachments
        )
    
    @database_sync_to_async
    def serialize_message(self, message):
        return MessageSerializer(message).data
    
    @database_sync_to_async
    def set_online(self, is_online):
        from django.core.cache import cache
        cache_key = f'user_online_{self.user.id}'
        if is_online:
            cache.set(cache_key, True, 300)  # 5 minutes
        else:
            cache.delete(cache_key)
    
    async def broadcast_presence(self):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'presence_update',
                'user_id': str(self.user.id)
            }
        )
    
    async def presence_update(self, event):
        online_users = await self.get_online_users()
        await self.send_message('presence', {'online_users': online_users})
    
    @database_sync_to_async
    def get_online_users(self):
        from django.core.cache import cache
        channel = Channel.objects.get(id=self.channel_id)
        members = channel.workspace.members.values_list('user_id', flat=True)
        
        online = []
        for user_id in members:
            if cache.get(f'user_online_{user_id}'):
                online.append(str(user_id))
        return online
```

### 2.5 Notification Consumer

**Buat `apps/notifications/consumers.py`:**

```python
from apps.core.consumers import BaseConsumer

class NotificationConsumer(BaseConsumer):
    """
    User-specific notification channel.
    Each user joins their own notification room.
    """
    
    async def on_connect(self):
        self.room_group_name = f'notifications_{self.user.id}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send unread count
        count = await self.get_unread_count()
        await self.send_message('unread_count', {'count': count})
    
    async def on_disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    # Called when notification is sent to user
    async def notification(self, event):
        await self.send_message('notification', event['data'])
    
    @database_sync_to_async
    def get_unread_count(self):
        from .models import Notification
        return Notification.objects.filter(
            user=self.user,
            read_at__isnull=True
        ).count()
```

### 2.6 Update Routing

**Update `config/routing.py`:**

```python
from django.urls import path
from apps.documents.consumers import DocumentConsumer
from apps.channels.consumers import ChatConsumer
from apps.notifications.consumers import NotificationConsumer

websocket_urlpatterns = [
    path('ws/documents/<uuid:document_id>/', DocumentConsumer.as_asgi()),
    path('ws/channels/<uuid:channel_id>/', ChatConsumer.as_asgi()),
    path('ws/notifications/', NotificationConsumer.as_asgi()),
]
```

---

## 🧪 Testing WebSocket

```python
# tests/test_websocket.py
import pytest
from channels.testing import WebsocketCommunicator
from config.asgi import application

@pytest.mark.asyncio
async def test_document_consumer():
    # Create test user and document
    # ...
    
    communicator = WebsocketCommunicator(
        application,
        f'/ws/documents/{document.id}/?token={token}'
    )
    
    connected, _ = await communicator.connect()
    assert connected
    
    # Receive document state
    response = await communicator.receive_json_from()
    assert response['type'] == 'document_state'
    
    # Send update
    await communicator.send_json_to({
        'type': 'update',
        'data': {'content': 'New content', 'version': 1}
    })
    
    await communicator.disconnect()
```

---

## ✅ Checklist

- [ ] JWT WebSocket authentication
- [ ] Base consumer class
- [ ] Document consumer dengan collaboration
- [ ] Chat consumer dengan messaging
- [ ] Notification consumer
- [ ] WebSocket routing
- [ ] Presence/online status
- [ ] Typing indicators
- [ ] Cursor positions
- [ ] WebSocket tests

---

## 🔗 Referensi

- [WEBSOCKET.md](../../../docs/04-advanced/WEBSOCKET.md) - Complete guide

---

## ➡️ Next Step

Lanjut ke [03-CACHING_STRATEGY.md](03-CACHING_STRATEGY.md) - Multi-layer Caching
