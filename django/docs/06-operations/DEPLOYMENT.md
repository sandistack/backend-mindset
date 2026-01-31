# 🚀 DEPLOYMENT - Django (Junior → Senior)

Dokumentasi lengkap deployment Django dari development ke production.

---

## 🎯 Deployment Goals

- ✅ **Security:** No DEBUG=True, proper secrets management
- ✅ **Performance:** Optimized settings, caching, CDN
- ✅ **Reliability:** Zero-downtime deployment, health checks
- ✅ **Scalability:** Horizontal scaling, load balancing

---

## 1️⃣ JUNIOR LEVEL - Pre-Deployment Checklist

### Environment Variables

```bash
# .env.production
DEBUG=False
SECRET_KEY=your-super-secret-key-min-50-chars-long
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgres://user:pass@localhost:5432/dbname
REDIS_URL=redis://localhost:6379/1
```

### Settings Split

```python
# config/settings/production.py
from .base import *

DEBUG = False

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')

# Security
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Database with connection pooling
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL'),
        conn_max_age=600
    )
}

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'

# Media files
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'
```

### Collect Static Files

```bash
python manage.py collectstatic --noinput
```

---

## 2️⃣ MID LEVEL - Traditional Server (VPS)

### Deploy to DigitalOcean/Linode

#### Step 1: Setup Server

```bash
# SSH to server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y python3-pip python3-dev libpq-dev postgresql postgresql-contrib nginx curl
```

#### Step 2: Create Database

```bash
sudo -u postgres psql

postgres=# CREATE DATABASE taskdb;
postgres=# CREATE USER taskuser WITH PASSWORD 'securepassword';
postgres=# ALTER ROLE taskuser SET client_encoding TO 'utf8';
postgres=# ALTER ROLE taskuser SET default_transaction_isolation TO 'read committed';
postgres=# ALTER ROLE taskuser SET timezone TO 'UTC';
postgres=# GRANT ALL PRIVILEGES ON DATABASE taskdb TO taskuser;
postgres=# \q
```

#### Step 3: Deploy Code

```bash
# Clone repository
cd /var/www
git clone https://github.com/yourusername/task-api.git
cd task-api

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
nano .env  # Edit with production values

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser
python manage.py createsuperuser
```

#### Step 4: Gunicorn Setup

```bash
# Install Gunicorn
pip install gunicorn

# Test Gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

**Create systemd service:**

```bash
# /etc/systemd/system/gunicorn.service
[Unit]
Description=gunicorn daemon for task-api
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/task-api
ExecStart=/var/www/task-api/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/var/www/task-api/gunicorn.sock \
    config.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
# Start Gunicorn
systemctl start gunicorn
systemctl enable gunicorn
systemctl status gunicorn
```

#### Step 5: Nginx Setup

```nginx
# /etc/nginx/sites-available/task-api
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location /static/ {
        alias /var/www/task-api/staticfiles/;
    }

    location /media/ {
        alias /var/www/task-api/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/task-api/gunicorn.sock;
    }
}
```

```bash
# Enable site
ln -s /etc/nginx/sites-available/task-api /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

#### Step 6: SSL with Let's Encrypt

```bash
# Install Certbot
apt install certbot python3-certbot-nginx

# Get SSL certificate
certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal (already configured by certbot)
certbot renew --dry-run
```

---

## 3️⃣ MID-SENIOR LEVEL - Docker Deployment

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . /app/

# Collect static files
RUN python manage.py collectstatic --noinput

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "config.wsgi:application"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=taskdb
      - POSTGRES_USER=taskuser
      - POSTGRES_PASSWORD=securepassword
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  web:
    build: .
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "8000:8000"
    env_file:
      - .env.production
    depends_on:
      - db
      - redis

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - web

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

### nginx.conf (for Docker)

```nginx
upstream django {
    server web:8000;
}

server {
    listen 80;
    server_name yourdomain.com;

    location /static/ {
        alias /app/staticfiles/;
    }

    location /media/ {
        alias /app/media/;
    }

    location / {
        proxy_pass http://django;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        proxy_redirect off;
    }
}
```

### Deploy with Docker

```bash
# Build and run
docker-compose -f docker-compose.yml up -d --build

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# View logs
docker-compose logs -f web

# Stop
docker-compose down
```

---

## 4️⃣ SENIOR LEVEL - Cloud Platform (Heroku)

### Heroku Setup

```bash
# Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Login
heroku login

# Create app
heroku create task-api-prod

# Add PostgreSQL
heroku addons:create heroku-postgresql:mini

# Add Redis
heroku addons:create heroku-redis:mini
```

### Procfile

```
web: gunicorn config.wsgi --log-file -
release: python manage.py migrate
```

### runtime.txt

```
python-3.11.0
```

### Additional Files

```python
# config/settings/heroku.py
import dj_database_url

DEBUG = False
ALLOWED_HOSTS = ['.herokuapp.com']

# Database
DATABASES = {
    'default': dj_database_url.config(conn_max_age=600, ssl_require=True)
}

# Whitenoise for static files
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add this
    # ... other middleware
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

```bash
# Install whitenoise
pip install whitenoise

# Update requirements.txt
pip freeze > requirements.txt
```

### Deploy to Heroku

```bash
# Set environment variables
heroku config:set DEBUG=False
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DJANGO_SETTINGS_MODULE=config.settings.heroku

# Deploy
git add .
git commit -m "Heroku deployment"
git push heroku main

# Run migrations
heroku run python manage.py migrate

# Create superuser
heroku run python manage.py createsuperuser

# View logs
heroku logs --tail

# Open app
heroku open
```

---

## 5️⃣ SENIOR LEVEL - AWS Deployment

### AWS Services Used

- **EC2:** Virtual servers
- **RDS:** Managed PostgreSQL
- **S3:** Static/media files
- **CloudFront:** CDN
- **Elastic Load Balancer:** Load balancing
- **Route 53:** DNS management

### S3 for Static/Media Files

```bash
pip install boto3 django-storages
```

```python
# config/settings/aws.py

# S3 Configuration
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = 'us-east-1'
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

# Static files
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'

# Media files
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
```

### RDS PostgreSQL

```python
# From AWS RDS Console, get connection details
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'taskdb',
        'USER': 'admin',
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': 'task-db.xxxx.us-east-1.rds.amazonaws.com',
        'PORT': '5432',
    }
}
```

---

## 6️⃣ EXPERT LEVEL - CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/testdb
      run: |
        python manage.py test
    
    - name: Run linting
      run: |
        flake8 .

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Heroku
      uses: akhileshns/heroku-deploy@v3.12.12
      with:
        heroku_api_key: ${{secrets.HEROKU_API_KEY}}
        heroku_app_name: "task-api-prod"
        heroku_email: ${{secrets.HEROKU_EMAIL}}
```

### GitLab CI/CD

```yaml
# .gitlab-ci.yml
stages:
  - test
  - deploy

test:
  stage: test
  image: python:3.11
  services:
    - postgres:15
  variables:
    POSTGRES_DB: testdb
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: postgres
  script:
    - pip install -r requirements.txt
    - python manage.py test
    - flake8 .

deploy_production:
  stage: deploy
  only:
    - main
  script:
    - apt-get update -qy
    - apt-get install -y ruby-dev
    - gem install dpl
    - dpl --provider=heroku --app=task-api-prod --api-key=$HEROKU_API_KEY
```

---

## 7️⃣ EXPERT LEVEL - Zero-Downtime Deployment

### Blue-Green Deployment

```bash
# Two identical environments: Blue (current) and Green (new)

# Deploy to Green environment
docker-compose -f docker-compose.green.yml up -d

# Run health checks on Green
curl https://green.yourdomain.com/health/

# Switch traffic from Blue to Green (Nginx/Load Balancer)
# Update nginx config to point to Green

# Monitor Green for issues
# If OK: Keep Green active
# If errors: Switch back to Blue
```

### Rolling Deployment

```yaml
# docker-compose with rolling updates
version: '3.8'

services:
  web:
    image: task-api:latest
    deploy:
      replicas: 3
      update_config:
        parallelism: 1  # Update 1 instance at a time
        delay: 10s
        order: start-first  # Start new before stopping old
      rollback_config:
        parallelism: 1
        delay: 5s
```

---

## 8️⃣ EXPERT LEVEL - Monitoring & Health Checks

### Health Check Endpoint

```python
# apps/core/views.py
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    """
    Health check endpoint for load balancers
    """
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Check Redis connection
        from django.core.cache import cache
        cache.set('health_check', 'ok', 10)
        assert cache.get('health_check') == 'ok'
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'ok',
            'cache': 'ok'
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=503)


# urls.py
urlpatterns = [
    path('health/', health_check, name='health_check'),
]
```

### Application Monitoring (Sentry)

```bash
pip install sentry-sdk
```

```python
# config/settings/production.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=config('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=True,
    environment='production',
)
```

---

## 📊 Deployment Options Comparison

| Platform | Difficulty | Cost | Scalability | Use Case |
|----------|-----------|------|-------------|----------|
| **VPS (DigitalOcean)** | 🔴 Hard | 💰 Low | ⭐⭐ Manual | Full control |
| **Heroku** | 🟢 Easy | 💰💰 Medium | ⭐⭐⭐ Auto | Quick MVP |
| **AWS** | 🔴 Hard | 💰💰💰 Variable | ⭐⭐⭐⭐ Excellent | Enterprise |
| **Docker** | 🟡 Medium | 💰 Low | ⭐⭐⭐ Good | Anywhere |
| **Railway/Render** | 🟢 Easy | 💰 Low | ⭐⭐ Good | Small projects |

---

## 🎯 Best Practices

### 1. Security

```python
# ✅ Always set these in production
DEBUG = False
SECRET_KEY = config('SECRET_KEY')  # Long random string
ALLOWED_HOSTS = ['yourdomain.com']

# HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# HSTS
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
```

### 2. Performance

```python
# Database connection pooling
DATABASES = {
    'default': {
        # ...
        'CONN_MAX_AGE': 600,  # Keep connections for 10 minutes
    }
}

# Caching
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL'),
    }
}

# Compression
MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',  # Compress responses
    # ...
]
```

### 3. Logging

```python
# Production logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/error.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
```

---

## 💡 Summary

| Level | Technique |
|-------|-----------|
| **Junior** | Environment variables, settings split |
| **Mid** | VPS deployment, Gunicorn + Nginx |
| **Mid-Senior** | Docker + docker-compose |
| **Senior** | Cloud platforms (Heroku, AWS) |
| **Expert** | CI/CD, zero-downtime, monitoring |

**Deployment Checklist:**
- ✅ DEBUG=False
- ✅ SECRET_KEY from environment
- ✅ ALLOWED_HOSTS configured
- ✅ Database with connection pooling
- ✅ Static files collected
- ✅ HTTPS enabled
- ✅ Security headers set
- ✅ Monitoring (Sentry/CloudWatch)
- ✅ Health check endpoint
- ✅ Automated backups
- ✅ CI/CD pipeline

**Quick Deploy Commands:**
```bash
# Traditional
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn config.wsgi:application

# Docker
docker-compose up -d --build

# Heroku
git push heroku main
```
