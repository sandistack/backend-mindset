# 🔌 WEBSOCKET - Django (Junior → Senior)

Dokumentasi lengkap tentang WebSocket dan real-time communication di Django menggunakan Django Channels.

---

## 🎯 HTTP vs WebSocket

### HTTP (Request-Response)

```
Client: "Hey server, give me data"
Server: "Here's your data"
[Connection closed]

Client: "Hey server, any updates?"
Server: "No updates"
[Connection closed]

Client: "Hey server, updates now?"
Server: "Yes, here's update"
[Connection closed]
```

**Problems:**
- ❌ Client must keep asking (polling)
- ❌ Inefficient (many requests)
- ❌ Not real-time
- ❌ High latency

### WebSocket (Persistent Connection)

```
Client: "Hey server, I want updates"
Server: "OK, connection open"
[Connection stays open]

Server: "New message for you!" (push)
Server: "Another update!" (push)
Server: "One more!" (push)
```

**Benefits:**
- ✅ Bidirectional communication
- ✅ Server can push data
- ✅ Real-time updates
- ✅ Low latency
- ✅ Efficient

---

## 1️⃣ JUNIOR LEVEL - Django Channels Setup

### Install Django Channels

```bash
pip install channels channels-redis daphne
```

### Basic Configuration

```python
# config/settings/base.py
INSTALLED_APPS = [
    'daphne',  # Must be first!
    'django.contrib.admin',
    'django.contrib.auth',
    # ... other apps
    'channels',
]

# ASGI application
ASGI_APPLICATION = 'config.asgi.application'

# Channel layers (Redis)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}
```

### ASGI Configuration

```python
# config/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django_asgi_app = get_asgi_application()

from apps.chat import routing  # Import after django setup

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns
        )
    ),
})
```

---

## 2️⃣ MID LEVEL - Basic WebSocket Consumer

### Create Consumer

```python
# apps/chat/consumers.py
from channels.generic.websocket import WebsocketConsumer
import json

class ChatConsumer(WebsocketConsumer):
    """
    Basic WebSocket consumer (synchronous)
    """
    
    def connect(self):
        """
        Called when WebSocket connection is opened
        """
        # Accept connection
        self.accept()
        
        print(f"WebSocket connected: {self.channel_name}")
    
    def disconnect(self, close_code):
        """
        Called when WebSocket connection is closed
        """
        print(f"WebSocket disconnected: {close_code}")
    
    def receive(self, text_data):
        """
        Called when message received from client
        """
        # Parse JSON
        data = json.loads(text_data)
        message = data.get('message', '')
        
        print(f"Received: {message}")
        
        # Send message back to client
        self.send(text_data=json.dumps({
            'message': f"Echo: {message}"
        }))
```

### URL Routing

```python
# apps/chat/routing.py
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/chat/', consumers.ChatConsumer.as_asgi()),
]
```

### Run Server

```bash
# Run with Daphne (ASGI server)
daphne -p 8000 config.asgi:application

# Or use runserver (supports ASGI in Django 3+)
python manage.py runserver
```

### Client-Side (JavaScript)

```javascript
// Connect to WebSocket
const socket = new WebSocket('ws://localhost:8000/ws/chat/');

// Connection opened
socket.onopen = function(e) {
    console.log('WebSocket connected!');
    
    // Send message
    socket.send(JSON.stringify({
        'message': 'Hello Server!'
    }));
};

// Message received
socket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    console.log('Received:', data.message);
};

// Connection closed
socket.onclose = function(e) {
    console.log('WebSocket disconnected');
};

// Error
socket.onerror = function(e) {
    console.error('WebSocket error:', e);
};
```

---

## 3️⃣ MID-SENIOR LEVEL - Async Consumer

### Async Consumer (Better Performance)

```python
# apps/chat/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class ChatConsumer(AsyncWebsocketConsumer):
    """
    Async WebSocket consumer (recommended)
    """
    
    async def connect(self):
        """
        Accept WebSocket connection
        """
        await self.accept()
        print(f"Connected: {self.channel_name}")
    
    async def disconnect(self, close_code):
        """
        Handle disconnection
        """
        print(f"Disconnected: {close_code}")
    
    async def receive(self, text_data):
        """
        Receive message from WebSocket
        """
        data = json.loads(text_data)
        message = data['message']
        
        # Send message back
        await self.send(text_data=json.dumps({
            'message': f"Server: {message}",
            'timestamp': str(datetime.now())
        }))
```

---

## 4️⃣ SENIOR LEVEL - Channel Layers (Broadcasting)

### Group Chat with Channel Layers

```python
# apps/chat/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class ChatRoomConsumer(AsyncWebsocketConsumer):
    """
    Chat room dengan broadcasting
    """
    
    async def connect(self):
        # Get room name from URL
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Notify room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': f'{self.scope["user"]} joined the room'
            }
        )
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Notify room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': f'{self.scope["user"]} left the room'
            }
        )
    
    async def receive(self, text_data):
        """
        Receive message from WebSocket
        """
        data = json.loads(text_data)
        message = data['message']
        username = self.scope['user'].username
        
        # Broadcast to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username
            }
        )
    
    async def chat_message(self, event):
        """
        Receive message from room group
        """
        message = event['message']
        username = event.get('username', 'System')
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'username': username
        }))
```

### URL with Parameters

```python
# apps/chat/routing.py
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/chat/<str:room_name>/', consumers.ChatRoomConsumer.as_asgi()),
]
```

### Client-Side

```javascript
// Connect to room
const roomName = 'general';
const socket = new WebSocket(`ws://localhost:8000/ws/chat/${roomName}/`);

// Send message
function sendMessage(message) {
    socket.send(JSON.stringify({
        'message': message
    }));
}

// Receive message
socket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    console.log(`${data.username}: ${data.message}`);
    
    // Display in UI
    displayMessage(data.username, data.message);
};
```

---

## 5️⃣ SENIOR LEVEL - Authentication

### JWT Authentication for WebSocket

```python
# apps/core/middleware.py
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model

User = get_user_model()

@database_sync_to_async
def get_user_from_token(token):
    """
    Get user from JWT token
    """
    try:
        access_token = AccessToken(token)
        user_id = access_token['user_id']
        return User.objects.get(id=user_id)
    except Exception:
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom middleware for JWT authentication
    """
    
    async def __call__(self, scope, receive, send):
        # Get token from query string
        query_string = scope['query_string'].decode()
        params = dict(param.split('=') for param in query_string.split('&') if '=' in param)
        token = params.get('token')
        
        # Authenticate user
        if token:
            scope['user'] = await get_user_from_token(token)
        else:
            scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)


# config/asgi.py
from apps.core.middleware import JWTAuthMiddleware

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddleware(  # Add JWT middleware
        URLRouter(
            routing.websocket_urlpatterns
        )
    ),
})
```

### Client with JWT

```javascript
// Get JWT token from login
const token = localStorage.getItem('access_token');

// Connect with token
const socket = new WebSocket(`ws://localhost:8000/ws/chat/room1/?token=${token}`);
```

### Protected Consumer

```python
class ChatConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        # Check authentication
        if self.scope['user'].is_anonymous:
            await self.close()
            return
        
        # User authenticated, accept connection
        await self.accept()
```

---

## 6️⃣ EXPERT LEVEL - Database Integration

### Save Messages to Database

```python
# apps/chat/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatRoom(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ChatMessage(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']


# apps/chat/consumers.py
from channels.db import database_sync_to_async
from .models import ChatRoom, ChatMessage

class ChatRoomConsumer(AsyncWebsocketConsumer):
    
    @database_sync_to_async
    def save_message(self, room_name, user, message):
        """
        Save message to database
        """
        room, _ = ChatRoom.objects.get_or_create(name=room_name)
        
        return ChatMessage.objects.create(
            room=room,
            user=user,
            message=message
        )
    
    @database_sync_to_async
    def get_room_history(self, room_name, limit=50):
        """
        Get chat history
        """
        room = ChatRoom.objects.get(name=room_name)
        messages = room.messages.all()[:limit]
        
        return [
            {
                'username': msg.user.username,
                'message': msg.message,
                'created_at': msg.created_at.isoformat()
            }
            for msg in messages
        ]
    
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        
        # Join room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send chat history
        history = await self.get_room_history(self.room_name)
        await self.send(text_data=json.dumps({
            'type': 'chat_history',
            'messages': history
        }))
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        
        # Save to database
        await self.save_message(
            self.room_name,
            self.scope['user'],
            message
        )
        
        # Broadcast to group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': self.scope['user'].username
            }
        )
```

---

## 7️⃣ EXPERT LEVEL - Real-time Notifications

### Notification Consumer

```python
# apps/notifications/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Real-time notifications for user
    """
    
    async def connect(self):
        if self.scope['user'].is_anonymous:
            await self.close()
            return
        
        # User-specific group
        self.user_group_name = f'notifications_{self.scope["user"].id}'
        
        # Join user's notification group
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave group
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )
    
    async def notification_message(self, event):
        """
        Send notification to WebSocket
        """
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'title': event['title'],
            'message': event['message'],
            'timestamp': event['timestamp']
        }))


# Routing
websocket_urlpatterns = [
    path('ws/notifications/', NotificationConsumer.as_asgi()),
]
```

### Send Notification from Views

```python
# apps/tasks/views.py
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class TaskCreateView(APIView):
    
    def post(self, request):
        # Create task
        task = TaskService.create_task(
            user=request.user,
            **request.data
        )
        
        # Send real-time notification
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'notifications_{request.user.id}',
            {
                'type': 'notification_message',
                'title': 'New Task Created',
                'message': f'Task "{task.title}" has been created',
                'timestamp': str(timezone.now())
            }
        )
        
        return Response({'data': TaskSerializer(task).data})
```

### Client-Side

```javascript
// Connect to notifications
const token = localStorage.getItem('access_token');
const socket = new WebSocket(`ws://localhost:8000/ws/notifications/?token=${token}`);

socket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    
    if (data.type === 'notification') {
        // Show notification
        showNotification(data.title, data.message);
    }
};

function showNotification(title, message) {
    // Browser notification
    if (Notification.permission === 'granted') {
        new Notification(title, {
            body: message,
            icon: '/static/icon.png'
        });
    }
    
    // Or in-app notification
    const notifDiv = document.getElementById('notifications');
    notifDiv.innerHTML += `<div class="alert">${title}: ${message}</div>`;
}
```

---

## 8️⃣ EXPERT LEVEL - Scaling WebSocket

### Redis Adapter for Multiple Servers

```python
# config/settings/production.py
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('redis-server.com', 6379)],
            "capacity": 1500,  # Max messages in channel
            "expiry": 10,      # Message expiry (seconds)
        },
    },
}
```

**How it works:**
```
User A → Server 1 → Redis → Server 2 → User B
User C → Server 2 → Redis → Server 1 → User D
```

### Load Balancer Configuration (Nginx)

```nginx
upstream websocket {
    ip_hash;  # Sticky sessions
    server 192.168.1.10:8000;
    server 192.168.1.11:8000;
    server 192.168.1.12:8000;
}

server {
    listen 80;
    
    location /ws/ {
        proxy_pass http://websocket;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📊 Use Cases

| Use Case | Implementation |
|----------|----------------|
| **Chat Application** | Channel layers + groups |
| **Real-time Notifications** | User-specific groups |
| **Live Dashboard** | Broadcast updates to all clients |
| **Collaborative Editing** | Operational Transformation + WebSocket |
| **Online Gaming** | Fast bidirectional communication |
| **Live Streaming** | WebRTC + WebSocket signaling |
| **IoT Monitoring** | Sensor data → WebSocket → Dashboard |

---

## 🎯 Best Practices

### 1. Use Async Consumers

```python
# ✅ Good: Async (better performance)
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

# ❌ Avoid: Sync (blocks)
class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
```

### 2. Handle Disconnections

```python
async def disconnect(self, close_code):
    # Always cleanup
    await self.channel_layer.group_discard(
        self.room_group_name,
        self.channel_name
    )
    
    # Notify others
    await self.channel_layer.group_send(
        self.room_group_name,
        {'type': 'user_left', 'user': self.scope['user'].username}
    )
```

### 3. Validate Messages

```python
async def receive(self, text_data):
    try:
        data = json.loads(text_data)
        
        # Validate
        if 'message' not in data:
            await self.send(text_data=json.dumps({
                'error': 'Missing message field'
            }))
            return
        
        # Process
        await self.process_message(data['message'])
    
    except json.JSONDecodeError:
        await self.send(text_data=json.dumps({
            'error': 'Invalid JSON'
        }))
```

### 4. Rate Limiting

```python
from time import time

class ChatConsumer(AsyncWebsocketConsumer):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message_count = 0
        self.window_start = time()
    
    async def receive(self, text_data):
        # Rate limit: 10 messages per 60 seconds
        current_time = time()
        
        if current_time - self.window_start > 60:
            self.message_count = 0
            self.window_start = current_time
        
        if self.message_count >= 10:
            await self.send(text_data=json.dumps({
                'error': 'Rate limit exceeded'
            }))
            return
        
        self.message_count += 1
        
        # Process message
        await self.process_message(text_data)
```

---

## 💡 Summary

| Level | Technique |
|-------|-----------|
| **Junior** | Basic WebSocket setup |
| **Mid** | Async consumers |
| **Mid-Senior** | Channel layers (broadcasting) |
| **Senior** | Authentication, database integration |
| **Expert** | Real-time notifications, scaling |

**Key Points:**
- ✅ Use Django Channels for WebSocket
- ✅ Always use async consumers
- ✅ Use channel layers for broadcasting
- ✅ Authenticate WebSocket connections
- ✅ Handle disconnections properly
- ✅ Use Redis for scaling

**Quick Start:**
```bash
# Install
pip install channels channels-redis daphne

# Run server
daphne -p 8000 config.asgi:application

# Or
python manage.py runserver
```

**Common Pattern:**
```python
# Consumer
class MyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        await self.send(text_data=json.dumps(data))
    
    async def disconnect(self, close_code):
        pass

# Client
const socket = new WebSocket('ws://localhost:8000/ws/path/');
socket.onmessage = (e) => console.log(JSON.parse(e.data));
socket.send(JSON.stringify({message: 'Hello'}));
```
