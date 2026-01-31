# 💡 DJANGO TIPS & TRICKS (Junior → Senior)

Kumpulan tips praktis Django untuk berbagai skenario.

---

## 1) 🔐 Cara Ubah Login Admin Django

### Option 1: Default (Username & Password)

```python
# Default Django behavior
# Login: /admin/ dengan username
```

### Option 2: Email & Password

```python
# apps/authentication/models.py
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    email = models.EmailField(unique=True)
    
    USERNAME_FIELD = 'email'  # ← Login pakai email
    REQUIRED_FIELDS = ['username']  # Required untuk createsuperuser
    
    def __str__(self):
        return self.email
```

```python
# config/settings/base.py
AUTH_USER_MODEL = 'authentication.User'
```

```bash
# Create superuser
python manage.py createsuperuser
# Akan prompt email (bukan username)
```

### Option 3: Flexible (Email OR Username)

```python
# apps/authentication/backends.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailOrUsernameBackend(ModelBackend):
    """
    Allow login dengan email atau username
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Try email first, fallback to username
            user = User.objects.get(
                Q(email=username) | Q(username=username)
            )
            
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
```

```python
# config/settings/base.py
AUTHENTICATION_BACKENDS = [
    'apps.authentication.backends.EmailOrUsernameBackend',  # Custom
    'django.contrib.auth.backends.ModelBackend',           # Default fallback
]
```

---

## 2) 🗄️ Setup PostgreSQL di Django

### Install Driver

```bash
pip install psycopg2-binary
```

### Database Config

```python
# config/settings/development.py
from decouple import config

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}
```

### Environment Variables (.env)

```bash
# .env
DB_NAME=task_db
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432
```

### Create Database (PostgreSQL)

```bash
# Login to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE task_db;

# Create user
CREATE USER task_user WITH PASSWORD 'yourpassword';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE task_db TO task_user;

# Exit
\q
```

### Run Migrations

```bash
python manage.py migrate
```

---

## 3) 🔐 Setup Environment Variables

### Install python-decouple

```bash
pip install python-decouple
```

### Create .env File

```bash
# .env (root project)
SECRET_KEY=django-insecure-your-secret-key
DEBUG=True

# Database
DB_NAME=task_db
DB_USER=postgres
DB_PASSWORD=pass123
DB_HOST=localhost
DB_PORT=5432

# JWT
JWT_ACCESS_TOKEN_LIFETIME=60  # minutes
JWT_REFRESH_TOKEN_LIFETIME=1440  # minutes (1 day)
```

### Use in Settings

```python
# config/settings/base.py
from decouple import config

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432', cast=int),
    }
}

# JWT
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=config('JWT_ACCESS_TOKEN_LIFETIME', default=60, cast=int)),
    'REFRESH_TOKEN_LIFETIME': timedelta(minutes=config('JWT_REFRESH_TOKEN_LIFETIME', default=1440, cast=int)),
}
```

### .gitignore

```bash
# .gitignore
.env
*.pyc
__pycache__/
db.sqlite3
```

---

## 4) 🌐 Setup CORS di Django

### Install django-cors-headers

```bash
pip install django-cors-headers
```

### Config Settings

```python
# config/settings/base.py

INSTALLED_APPS = [
    ...
    'corsheaders',  # ← Add
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # ← Add (top position)
    'django.middleware.common.CommonMiddleware',
    ...
]

# Development: Allow all origins
CORS_ALLOW_ALL_ORIGINS = True

# Production: Whitelist specific origins
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',      # React dev
    'http://localhost:8080',      # Vue dev
    'https://myapp.com',          # Production frontend
]

# Allow credentials (cookies, auth headers)
CORS_ALLOW_CREDENTIALS = True

# Allow specific headers
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
```

---

## 5) 🔄 Switch Development/Production Settings

### Structure

```
config/
  settings/
    __init__.py
    base.py          # Common settings
    development.py   # Dev settings
    production.py    # Prod settings
```

### base.py (Common)

```python
# config/settings/base.py
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config('SECRET_KEY')

INSTALLED_APPS = [
    # Common apps
]

MIDDLEWARE = [
    # Common middleware
]

# Etc...
```

### development.py

```python
# config/settings/development.py
from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# SQLite for quick dev
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Console email backend (print emails to console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

### production.py

```python
# config/settings/production.py
from .base import *

DEBUG = False

ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=lambda v: [s.strip() for s in v.split(',')])

# PostgreSQL for production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
    }
}

# Real email backend
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')

# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### Switch Environment

```bash
# Development
export DJANGO_SETTINGS_MODULE=config.settings.development
python manage.py runserver

# Production
export DJANGO_SETTINGS_MODULE=config.settings.production
gunicorn config.wsgi:application
```

### Or via manage.py

```python
# manage.py
import os
import sys

def main():
    # Default to development
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
    
    # Override for production
    # os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
    
    ...
```

---

## 6) 👤 Custom User Model (Best Practices)

### Always Start with Custom User

**Bahkan jika gak butuh custom fields, SELALU pakai custom User dari awal!**

```python
# apps/authentication/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Custom User - extend later as needed
    """
    email = models.EmailField(unique=True)
    
    # Add custom fields
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.email
```

### Settings

```python
# config/settings/base.py
AUTH_USER_MODEL = 'authentication.User'
```

### Important: Migrate BEFORE Creating Any Data!

```bash
# First migration (before any data)
python manage.py makemigrations
python manage.py migrate
```

---

## 7) 🔑 Setup JWT Authentication

### Install djangorestframework-simplejwt

```bash
pip install djangorestframework-simplejwt
```

### Settings

```python
# config/settings/base.py
INSTALLED_APPS = [
    ...
    'rest_framework',
    'rest_framework_simplejwt',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

# JWT Settings
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
}
```

### URLs

```python
# apps/authentication/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
]
```

### Login View

```python
# apps/authentication/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        # Authenticate
        user = authenticate(username=email, password=password)
        
        if user:
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                "success": True,
                "message": "Login successful",
                "data": {
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "username": user.username
                    },
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh)
                }
            }, status=status.HTTP_200_OK)
        
        return Response({
            "success": False,
            "message": "Invalid credentials"
        }, status=status.HTTP_401_UNAUTHORIZED)
```

### Protected View

```python
class ProfileView(APIView):
    # permission_classes = [IsAuthenticated]  ← Default dari settings
    
    def get(self, request):
        user = request.user
        
        return Response({
            "success": True,
            "data": {
                "id": user.id,
                "email": user.email,
                "username": user.username
            }
        })
```

### Frontend Usage

```javascript
// Login
const response = await fetch('/api/auth/login/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({email: 'user@example.com', password: 'pass123'})
});

const data = await response.json();
const accessToken = data.data.access_token;
const refreshToken = data.data.refresh_token;

// Store tokens
localStorage.setItem('access_token', accessToken);
localStorage.setItem('refresh_token', refreshToken);

// Protected request
const profileResponse = await fetch('/api/auth/profile/', {
    headers: {
        'Authorization': `Bearer ${accessToken}`
    }
});

// Refresh token when expired
const refreshResponse = await fetch('/api/auth/refresh/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({refresh: refreshToken})
});

const newData = await refreshResponse.json();
const newAccessToken = newData.access;
```

---

## 8) 📝 Django Shell Tricks

### Basic Shell

```bash
python manage.py shell
```

```python
# Import models
from apps.tasks.models import Task
from django.contrib.auth import get_user_model

User = get_user_model()

# Create user
user = User.objects.create_user(
    email='test@example.com',
    username='testuser',
    password='pass123'
)

# Create task
task = Task.objects.create(
    user=user,
    title='Test Task',
    status='TODO'
)

# Query
Task.objects.filter(status='TODO')
Task.objects.filter(user__email='test@example.com')

# Update
task.status = 'DONE'
task.save()

# Delete
task.delete()
```

### Shell Plus (Better Shell)

```bash
pip install django-extensions
```

```python
# settings.py
INSTALLED_APPS = [
    ...
    'django_extensions',
]
```

```bash
# Auto-import all models
python manage.py shell_plus
```

---

## 9) 🚀 Performance Tips

### Use select_related() for ForeignKey

```python
# ❌ Bad: N+1 query
tasks = Task.objects.all()
for task in tasks:
    print(task.user.email)  # Each iteration = 1 query

# ✅ Good: 1 query with JOIN
tasks = Task.objects.select_related('user').all()
for task in tasks:
    print(task.user.email)  # No extra queries
```

### Use prefetch_related() for ManyToMany

```python
# ❌ Bad: N+1 query
tasks = Task.objects.all()
for task in tasks:
    print(task.tags.all())  # Each iteration = 1 query

# ✅ Good: 2 queries total
tasks = Task.objects.prefetch_related('tags').all()
for task in tasks:
    print(task.tags.all())  # From cache
```

### Database Indexing

```python
class Task(models.Model):
    status = models.CharField(max_length=20, db_index=True)  # ← Index
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'status']),  # Composite index
            models.Index(fields=['-created_at']),     # Reverse index
        ]
```

### Use only() and defer()

```python
# Only get specific fields
tasks = Task.objects.only('id', 'title')

# Exclude specific fields
tasks = Task.objects.defer('description')
```

---

## 10) 🧪 Quick Testing

```bash
# Run tests
python manage.py test

# Specific app
python manage.py test apps.tasks

# Keep database (faster)
python manage.py test --keepdb

# Parallel
python manage.py test --parallel

# Coverage
pip install coverage
coverage run manage.py test
coverage report
coverage html  # Open htmlcov/index.html
```

---

## 💡 Bonus Tips

### Generate Secret Key

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### Clear All Data (Dev Only!)

```bash
python manage.py flush
```

### Load Fixtures

```bash
# Export
python manage.py dumpdata apps.tasks --indent 2 > tasks.json

# Import
python manage.py loaddata tasks.json
```

### Create Management Command

```python
# apps/tasks/management/commands/cleanup_tasks.py
from django.core.management.base import BaseCommand
from apps.tasks.models import Task

class Command(BaseCommand):
    help = 'Delete old completed tasks'
    
    def handle(self, *args, **options):
        deleted = Task.objects.filter(status='DONE').delete()
        self.stdout.write(
            self.style.SUCCESS(f'Deleted {deleted[0]} tasks')
        )
```

```bash
python manage.py cleanup_tasks
```

---

## 📚 Useful Packages

| Package | Use Case |
|---------|----------|
| `django-extensions` | shell_plus, runserver_plus |
| `django-debug-toolbar` | Debug queries di browser |
| `django-filter` | Advanced filtering |
| `drf-spectacular` | Auto API documentation |
| `celery` | Background tasks |
| `django-redis` | Caching |
| `pillow` | Image handling |
| `python-decouple` | Environment variables |

---

Semoga membantu! 🚀


