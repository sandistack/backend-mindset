# 🛠️ Step 1: Project Setup

**Waktu:** 3-4 jam  
**Prerequisite:** Project 01 selesai

---

## 🎯 Tujuan

- Setup multi-app Django project
- Konfigurasi PostgreSQL
- Setup Redis untuk caching
- Setup Celery untuk background tasks
- Docker development environment

---

## 📋 Tasks

### 1.1 Project Structure

```bash
mkdir ecommerce-api && cd ecommerce-api

# Virtual environment
python -m venv venv
source venv/bin/activate  # atau venv\Scripts\activate di Windows

# Create Django project
django-admin startproject config .

# Create apps
mkdir apps
cd apps
django-admin startapp authentication
django-admin startapp core
django-admin startapp products
django-admin startapp cart
django-admin startapp orders
django-admin startapp payments
django-admin startapp reports
cd ..
```

### 1.2 Requirements

**Buat `requirements.txt`:**

```
# Django
django>=4.2
djangorestframework>=3.14
djangorestframework-simplejwt>=5.3

# Database
psycopg2-binary>=2.9

# Filtering & Pagination
django-filter>=23.0

# CORS
django-cors-headers>=4.0

# Environment
python-dotenv>=1.0

# Celery & Redis
celery>=5.3
redis>=5.0
django-redis>=5.4

# File Upload
boto3>=1.28
django-storages>=1.14
Pillow>=10.0

# Email
django-anymail>=10.0

# Export
openpyxl>=3.1
weasyprint>=60.0
reportlab>=4.0

# API Documentation
drf-spectacular>=0.26

# Testing
pytest>=7.4
pytest-django>=4.5
pytest-cov>=4.1
factory-boy>=3.3
```

### 1.3 Docker Setup (Development)

**Buat `docker-compose.yml`:**

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: ecommerce
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  # Optional: Local S3 (MinIO)
  minio:
    image: minio/minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data

volumes:
  postgres_data:
  minio_data:
```

```bash
# Start services
docker-compose up -d
```

### 1.4 Settings Configuration

**`config/settings/base.py`:**

```python
# Apps
INSTALLED_APPS = [
    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'django_filters',
    'corsheaders',
    'storages',
    'drf_spectacular',
    
    # Local apps
    'apps.authentication',
    'apps.core',
    'apps.products',
    'apps.cart',
    'apps.orders',
    'apps.payments',
    'apps.reports',
]

# Custom User
AUTH_USER_MODEL = 'authentication.User'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'apps.core.pagination.CustomPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# Celery
CELERY_BROKER_URL = env('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# AWS S3 (akan dikonfigurasi di step File Upload)
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID', default='')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY', default='')
AWS_STORAGE_BUCKET_NAME = env('AWS_BUCKET', default='')
AWS_S3_REGION_NAME = env('AWS_REGION', default='ap-southeast-1')
```

### 1.5 Celery Configuration

**Buat `config/celery.py`:**

```python
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('ecommerce')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
```

**Update `config/__init__.py`:**

```python
from .celery import app as celery_app

__all__ = ('celery_app',)
```

### 1.6 Run Services

```bash
# Terminal 1: Django
python manage.py runserver

# Terminal 2: Celery Worker
celery -A config worker -l info

# Terminal 3: Celery Beat (untuk scheduled tasks)
celery -A config beat -l info
```

---

## ✅ Checklist

- [ ] Docker services running (PostgreSQL, Redis)
- [ ] Django project created
- [ ] All apps created
- [ ] Settings configured (base, development)
- [ ] Celery configured dan berjalan
- [ ] Redis cache configured
- [ ] `python manage.py check` no errors

---

## 🔗 Referensi

- [ARCHITECTURE.md](../../../docs/01-fundamentals/ARCHITECTURE.md) - Project structure
- [BACKGROUND_JOBS.md](../../../docs/04-advanced/BACKGROUND_JOBS.md) - Celery setup
- [CACHING.md](../../../docs/04-advanced/CACHING.md) - Redis configuration

---

## ➡️ Next Step

Lanjut ke [02-PRODUCT_CATALOG.md](02-PRODUCT_CATALOG.md) - Product & Category Models
