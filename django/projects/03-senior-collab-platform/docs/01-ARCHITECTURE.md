# 🏗️ Step 1: Architecture & Setup

**Waktu:** 4-6 jam  
**Prerequisite:** Project 01 & 02 selesai

---

## 🎯 Tujuan

- System design untuk scalability
- Docker development environment
- Multi-service architecture
- Base models & project structure

---

## 📐 System Architecture

```
                    ┌─────────────────┐
                    │   Nginx/LB      │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
    ┌───────┴───────┐ ┌──────┴──────┐ ┌───────┴───────┐
    │  Django API   │ │  WebSocket  │ │   Celery      │
    │   (Gunicorn)  │ │  (Daphne)   │ │   Worker      │
    └───────┬───────┘ └──────┬──────┘ └───────┬───────┘
            │                │                │
            └────────────────┼────────────────┘
                             │
    ┌────────────────────────┼────────────────────────┐
    │                        │                        │
┌───┴───┐             ┌──────┴──────┐          ┌──────┴──────┐
│ PostgreSQL │        │    Redis    │          │ Elasticsearch│
│ (Primary DB)│       │ (Cache/PubSub)│        │   (Search)   │
└─────────────┘       └─────────────┘          └─────────────┘
                             │
                      ┌──────┴──────┐
                      │    AWS S3   │
                      │   (Files)   │
                      └─────────────┘
```

---

## 📋 Tasks

### 1.1 Docker Compose Setup

**Buat `docker-compose.yml`:**

```yaml
version: '3.8'

services:
  # Django API
  api:
    build: .
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
      - redis

  # WebSocket Server
  websocket:
    build: .
    command: daphne -b 0.0.0.0 -p 8001 config.asgi:application
    volumes:
      - .:/app
    ports:
      - "8001:8001"
    env_file:
      - .env
    depends_on:
      - db
      - redis

  # Celery Worker
  celery:
    build: .
    command: celery -A config worker -l info -c 4
    volumes:
      - .:/app
    env_file:
      - .env
    depends_on:
      - db
      - redis

  # Celery Beat (Scheduler)
  celery-beat:
    build: .
    command: celery -A config beat -l info
    volumes:
      - .:/app
    env_file:
      - .env
    depends_on:
      - redis

  # PostgreSQL
  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: collab_platform
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"

  # Redis
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # Elasticsearch
  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

volumes:
  postgres_data:
  redis_data:
  elasticsearch_data:
```

**Buat `Dockerfile`:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Default command
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### 1.2 Requirements

```txt
# Django
django>=4.2
djangorestframework>=3.14
djangorestframework-simplejwt>=5.3

# Channels (WebSocket)
channels>=4.0
channels-redis>=4.1
daphne>=4.0

# Database
psycopg2-binary>=2.9

# Celery
celery>=5.3
redis>=5.0
django-redis>=5.4

# Elasticsearch
elasticsearch>=8.11
elasticsearch-dsl>=8.11

# File Storage
boto3>=1.28
django-storages>=1.14
Pillow>=10.0

# Utils
python-dotenv>=1.0
django-filter>=23.0
django-cors-headers>=4.0

# Production
gunicorn>=21.0

# Testing
pytest>=7.4
pytest-django>=4.5
pytest-asyncio>=0.21
factory-boy>=3.3
```

### 1.3 ASGI Configuration

**Buat `config/asgi.py`:**

```python
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# Initialize Django ASGI application early
django_asgi_app = get_asgi_application()

# Import routing after Django is initialized
from config.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
```

**Buat `config/routing.py`:**

```python
from django.urls import path

websocket_urlpatterns = [
    # Will add WebSocket routes here
    # path('ws/documents/<int:document_id>/', DocumentConsumer.as_asgi()),
    # path('ws/channels/<int:channel_id>/', ChannelConsumer.as_asgi()),
    # path('ws/notifications/', NotificationConsumer.as_asgi()),
]
```

### 1.4 Settings Configuration

**Di `settings/base.py`:**

```python
# Channels
INSTALLED_APPS += [
    'channels',
    'apps.workspaces',
    'apps.documents',
    'apps.channels',  # Chat channels
    'apps.notifications',
    'apps.files',
    'apps.search',
    'apps.activity',
]

ASGI_APPLICATION = 'config.asgi.application'

# Channel layers (Redis)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(env('REDIS_HOST', default='localhost'), 6379)],
        },
    },
}

# Elasticsearch
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': env('ELASTICSEARCH_URL', default='localhost:9200')
    },
}
```

### 1.5 Base Models

**Buat `apps/core/models.py`:**

```python
from django.db import models
import uuid

class BaseModel(models.Model):
    """Base model with common fields"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class SoftDeleteModel(BaseModel):
    """Base model with soft delete"""
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    objects = SoftDeleteManager()
    all_objects = models.Manager()
    
    class Meta:
        abstract = True
    
    def soft_delete(self):
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
    
    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save()
```

### 1.6 Workspace Models

**Buat `apps/workspaces/models.py`:**

```python
from django.db import models
from apps.core.models import BaseModel
from django.conf import settings

class Workspace(BaseModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_workspaces'
    )
    logo = models.ImageField(upload_to='workspaces/logos/', blank=True)
    settings = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Member(BaseModel):
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
        ('guest', 'Guest'),
    ]
    
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['workspace', 'user']
    
    def __str__(self):
        return f"{self.user.email} - {self.workspace.name} ({self.role})"


class Invite(BaseModel):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='invites')
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=Member.ROLE_CHOICES, default='member')
    token = models.CharField(max_length=100, unique=True)
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['workspace', 'email']
```

---

## 🚀 Running

```bash
# Start all services
docker-compose up -d

# Apply migrations
docker-compose exec api python manage.py migrate

# Create superuser
docker-compose exec api python manage.py createsuperuser

# Check logs
docker-compose logs -f api
docker-compose logs -f websocket
docker-compose logs -f celery
```

---

## ✅ Checklist

- [ ] Docker Compose dengan semua services
- [ ] Dockerfile untuk Django
- [ ] ASGI configuration untuk Channels
- [ ] Channel layers dengan Redis
- [ ] Elasticsearch configuration
- [ ] Base models (UUID, soft delete)
- [ ] Workspace & Member models
- [ ] Invite model
- [ ] All services running

---

## 🔗 Referensi

- [ARCHITECTURE.md](../../../docs/01-fundamentals/ARCHITECTURE.md) - Project structure
- [WEBSOCKET.md](../../../docs/04-advanced/WEBSOCKET.md) - Django Channels
- [DEPLOYMENT.md](../../../docs/06-operations/DEPLOYMENT.md) - Docker

---

## ➡️ Next Step

Lanjut ke [02-REALTIME_WEBSOCKET.md](02-REALTIME_WEBSOCKET.md) - WebSocket Implementation
