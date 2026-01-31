# 🚀 Step 8: Production Deployment

**Waktu:** 6-8 jam  
**Prerequisite:** Step 7 selesai

---

## 🎯 Tujuan

- Production Docker configuration
- Nginx reverse proxy
- CI/CD pipeline
- Monitoring & logging
- Security hardening

---

## 📋 Tasks

### 8.1 Production Docker Compose

**Buat `docker-compose.prod.yml`:**

```yaml
version: '3.8'

services:
  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./static:/app/static:ro
    depends_on:
      - api
      - websocket
    restart: always

  # Django API
  api:
    build:
      context: .
      dockerfile: Dockerfile.prod
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --threads 2
    volumes:
      - static_volume:/app/static
    env_file:
      - .env.prod
    depends_on:
      - db
      - redis
    restart: always
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1'
          memory: 1G

  # WebSocket Server
  websocket:
    build:
      context: .
      dockerfile: Dockerfile.prod
    command: daphne -b 0.0.0.0 -p 8001 config.asgi:application
    env_file:
      - .env.prod
    depends_on:
      - db
      - redis
    restart: always
    deploy:
      replicas: 2

  # Celery Worker
  celery:
    build:
      context: .
      dockerfile: Dockerfile.prod
    command: celery -A config worker -l info -c 4
    env_file:
      - .env.prod
    depends_on:
      - db
      - redis
    restart: always
    deploy:
      replicas: 2

  # Celery Beat
  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile.prod
    command: celery -A config beat -l info
    env_file:
      - .env.prod
    depends_on:
      - redis
    restart: always

  # PostgreSQL
  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G

  # Redis
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: always

  # Elasticsearch
  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G

volumes:
  postgres_data:
  redis_data:
  elasticsearch_data:
  static_volume:
```

### 8.2 Production Dockerfile

**Buat `Dockerfile.prod`:**

```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Production stage
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy application
COPY --chown=appuser:appuser . .

# Collect static files
RUN python manage.py collectstatic --noinput

USER appuser

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### 8.3 Nginx Configuration

**Buat `nginx/nginx.conf`:**

```nginx
upstream api {
    server api:8000;
}

upstream websocket {
    server websocket:8001;
}

server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;

    client_max_body_size 100M;

    # Static files
    location /static/ {
        alias /app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # API endpoints
    location /api/ {
        proxy_pass http://api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket endpoints
    location /ws/ {
        proxy_pass http://websocket;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }

    # Health check
    location /health/ {
        proxy_pass http://api;
        access_log off;
    }
}
```

### 8.4 GitHub Actions CI/CD

**Buat `.github/workflows/deploy.yml`:**

```yaml
name: Deploy

on:
  push:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
      redis:
        image: redis:7
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-django pytest-cov
      
      - name: Run tests
        env:
          DATABASE_URL: postgres://postgres:postgres@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379
        run: |
          pytest --cov=apps --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          file: Dockerfile.prod
          push: true
          tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    
    steps:
      - name: Deploy to server
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SERVER_SSH_KEY }}
          script: |
            cd /app/collab-platform
            docker-compose -f docker-compose.prod.yml pull
            docker-compose -f docker-compose.prod.yml up -d
            docker-compose -f docker-compose.prod.yml exec -T api python manage.py migrate
            docker system prune -f
```

### 8.5 Production Settings

**Di `config/settings/production.py`:**

```python
from .base import *
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

DEBUG = False

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

# Security
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# Database with connection pooling
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}

# Redis with password
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"redis://:{env('REDIS_PASSWORD')}@{env('REDIS_HOST')}:6379/0",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Sentry error tracking
sentry_sdk.init(
    dsn=env('SENTRY_DSN'),
    integrations=[
        DjangoIntegration(),
        CeleryIntegration(),
    ],
    traces_sample_rate=0.1,
    send_default_pii=True
)

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

**Referensi:** [DEPLOYMENT.md](../../../docs/06-operations/DEPLOYMENT.md)

### 8.6 Health Checks

**Buat `apps/core/views.py`:**

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import connection
from django.core.cache import cache

class HealthCheckView(APIView):
    permission_classes = []
    authentication_classes = []
    
    def get(self, request):
        health = {
            'status': 'healthy',
            'database': self.check_database(),
            'cache': self.check_cache(),
        }
        
        # Check if any component is unhealthy
        if not all(v == 'ok' for v in health.values() if v != 'healthy'):
            health['status'] = 'unhealthy'
            return Response(health, status=503)
        
        return Response(health)
    
    def check_database(self):
        try:
            connection.ensure_connection()
            return 'ok'
        except Exception as e:
            return str(e)
    
    def check_cache(self):
        try:
            cache.set('health_check', 'ok', 1)
            return 'ok' if cache.get('health_check') == 'ok' else 'fail'
        except Exception as e:
            return str(e)
```

### 8.7 Backup Script

**Buat `scripts/backup.sh`:**

```bash
#!/bin/bash

# Database backup
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/backups

# PostgreSQL backup
docker-compose -f docker-compose.prod.yml exec -T db \
    pg_dump -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Upload to S3
aws s3 cp $BACKUP_DIR/db_$DATE.sql.gz s3://your-bucket/backups/

# Keep only last 7 days locally
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Backup completed: db_$DATE.sql.gz"
```

---

## 📊 Monitoring

### Sentry untuk Error Tracking
- Real-time error alerts
- Performance monitoring
- Release tracking

### Prometheus + Grafana (Optional)
- Metrics collection
- Dashboards
- Alerting

---

## ✅ Final Checklist

### Deployment
- [ ] Production Docker Compose
- [ ] Production Dockerfile (multi-stage)
- [ ] Nginx reverse proxy
- [ ] SSL/TLS configuration
- [ ] GitHub Actions CI/CD

### Security
- [ ] Environment variables
- [ ] Secure headers
- [ ] Non-root user in container
- [ ] Database password
- [ ] Redis password

### Monitoring
- [ ] Health check endpoint
- [ ] Sentry integration
- [ ] JSON logging

### Operations
- [ ] Database backups
- [ ] Static files
- [ ] Migrations in CI/CD

---

## 🎉 Project Complete!

Selamat! Kamu telah menyelesaikan project Collaboration Platform level Senior. Kamu telah belajar:

1. ✅ **Architecture** - Scalable multi-service design
2. ✅ **WebSocket** - Real-time collaboration
3. ✅ **Caching** - Multi-layer caching strategy
4. ✅ **Background Jobs** - Advanced Celery patterns
5. ✅ **Notifications** - Push & real-time
6. ✅ **File Storage** - S3 integration
7. ✅ **Search** - Elasticsearch full-text search
8. ✅ **Deployment** - Production-ready CI/CD

---

## 🔗 Referensi

- [DEPLOYMENT.md](../../../docs/06-operations/DEPLOYMENT.md) - Deployment guide
- [LOG.md](../../../docs/06-operations/LOG.md) - Logging best practices
- [SECURITY.md](../../../docs/03-authentication/SECURITY.md) - Security

---

## ➡️ What's Next?

1. **Performance Testing** - Load test dengan Locust
2. **Security Audit** - OWASP checklist
3. **Documentation** - API docs dengan Swagger
4. **Launch** - Production release!
