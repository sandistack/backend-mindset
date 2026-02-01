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

## 9️⃣ EXPERT LEVEL - Kubernetes Deployment

### Docker Image Optimization

```dockerfile
# Dockerfile.prod (Multi-stage build)
# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Stage 2: Production
FROM python:3.11-slim

# Create non-root user
RUN useradd --create-home appuser
WORKDIR /home/appuser/app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels and install
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy application
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Collect static files
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "config.wsgi:application"]
```

### Kubernetes Manifests

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: task-api
---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: task-api-config
  namespace: task-api
data:
  DJANGO_SETTINGS_MODULE: "config.settings.production"
  ALLOWED_HOSTS: ".yourdomain.com"
  REDIS_URL: "redis://redis-service:6379/0"
---
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: task-api-secrets
  namespace: task-api
type: Opaque
data:
  SECRET_KEY: <base64-encoded-secret>
  DATABASE_URL: <base64-encoded-db-url>
  SENTRY_DSN: <base64-encoded-sentry-dsn>
```

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: task-api
  namespace: task-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: task-api
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  template:
    metadata:
      labels:
        app: task-api
    spec:
      containers:
      - name: task-api
        image: your-registry/task-api:latest
        ports:
        - containerPort: 8000
        
        envFrom:
        - configMapRef:
            name: task-api-config
        - secretRef:
            name: task-api-secrets
        
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        
        livenessProbe:
          httpGet:
            path: /health/
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          failureThreshold: 3
        
        readinessProbe:
          httpGet:
            path: /health/
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
          failureThreshold: 3
        
        lifecycle:
          preStop:
            exec:
              command: ["sleep", "10"]  # Graceful shutdown
---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: task-api-service
  namespace: task-api
spec:
  selector:
    app: task-api
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: task-api-ingress
  namespace: task-api
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.yourdomain.com
    secretName: task-api-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: task-api-service
            port:
              number: 80
```

### Horizontal Pod Autoscaler

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: task-api-hpa
  namespace: task-api
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: task-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
```

---

## 🔟 EXPERT LEVEL - Monitoring & Observability

### Prometheus + Grafana Setup

```python
# Install django-prometheus
# pip install django-prometheus

# config/settings/production.py
INSTALLED_APPS = [
    # ...
    'django_prometheus',
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    # ... other middleware ...
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

# Database monitoring
DATABASES = {
    'default': {
        'ENGINE': 'django_prometheus.db.backends.postgresql',
        # ... other settings
    }
}

# Cache monitoring  
CACHES = {
    'default': {
        'BACKEND': 'django_prometheus.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL'),
    }
}
```

```python
# apps/core/urls.py
urlpatterns = [
    # ...
    path('', include('django_prometheus.urls')),  # /metrics endpoint
]
```

```yaml
# k8s/prometheus-servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: task-api-monitor
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: task-api
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
  namespaceSelector:
    matchNames:
    - task-api
```

### Custom Metrics

```python
# apps/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Counters
api_requests_total = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

task_created_total = Counter(
    'task_created_total',
    'Total tasks created',
    ['priority']
)

# Histograms
request_latency = Histogram(
    'request_latency_seconds',
    'Request latency in seconds',
    ['endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
)

# Gauges
active_users = Gauge(
    'active_users',
    'Number of active users in last 5 minutes'
)


# Middleware to track metrics
class MetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start = time.time()
        
        response = self.get_response(request)
        
        # Record metrics
        latency = time.time() - start
        endpoint = request.resolver_match.url_name if request.resolver_match else 'unknown'
        
        api_requests_total.labels(
            method=request.method,
            endpoint=endpoint,
            status=response.status_code
        ).inc()
        
        request_latency.labels(endpoint=endpoint).observe(latency)
        
        return response


# In services
class TaskService:
    @staticmethod
    def create_task(user, data):
        task = Task.objects.create(user=user, **data)
        
        # Track metric
        task_created_total.labels(priority=task.priority).inc()
        
        return task
```

### Grafana Dashboard JSON

```json
{
  "dashboard": {
    "title": "Task API Dashboard",
    "panels": [
      {
        "title": "Requests per Second",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(api_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Request Latency (p95)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(request_latency_seconds_bucket[5m]))",
            "legendFormat": "{{endpoint}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "singlestat",
        "targets": [
          {
            "expr": "sum(rate(api_requests_total{status=~\"5..\"}[5m])) / sum(rate(api_requests_total[5m])) * 100"
          }
        ]
      },
      {
        "title": "Active Users",
        "type": "gauge",
        "targets": [
          {
            "expr": "active_users"
          }
        ]
      }
    ]
  }
}
```

---

## 1️⃣1️⃣ EXPERT LEVEL - Infrastructure as Code (Terraform)

### AWS Infrastructure

```hcl
# terraform/main.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket = "task-api-terraform-state"
    key    = "prod/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  
  name = "task-api-vpc"
  cidr = "10.0.0.0/16"
  
  azs             = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
  
  enable_nat_gateway = true
  single_nat_gateway = true
  
  tags = {
    Environment = var.environment
    Project     = "task-api"
  }
}

# RDS PostgreSQL
module "rds" {
  source = "terraform-aws-modules/rds/aws"
  
  identifier = "task-api-db"
  
  engine               = "postgres"
  engine_version       = "15.4"
  family               = "postgres15"
  major_engine_version = "15"
  instance_class       = "db.t3.medium"
  
  allocated_storage     = 20
  max_allocated_storage = 100
  
  db_name  = "taskdb"
  username = "admin"
  port     = 5432
  
  multi_az               = true
  db_subnet_group_name   = module.vpc.database_subnet_group
  vpc_security_group_ids = [module.security_group_rds.security_group_id]
  
  backup_retention_period = 7
  deletion_protection     = true
  
  performance_insights_enabled = true
  
  tags = {
    Environment = var.environment
  }
}

# ElastiCache Redis
module "elasticache" {
  source = "terraform-aws-modules/elasticache/aws"
  
  cluster_id           = "task-api-redis"
  engine               = "redis"
  engine_version       = "7.0"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 2
  
  subnet_group_name    = module.vpc.elasticache_subnet_group_name
  security_group_ids   = [module.security_group_redis.security_group_id]
  
  snapshot_retention_limit = 7
  
  tags = {
    Environment = var.environment
  }
}

# EKS Cluster
module "eks" {
  source = "terraform-aws-modules/eks/aws"
  
  cluster_name    = "task-api-cluster"
  cluster_version = "1.28"
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  
  eks_managed_node_groups = {
    main = {
      min_size     = 2
      max_size     = 10
      desired_size = 3
      
      instance_types = ["t3.medium"]
      capacity_type  = "ON_DEMAND"
    }
  }
  
  tags = {
    Environment = var.environment
  }
}

# S3 for static/media files
resource "aws_s3_bucket" "static" {
  bucket = "task-api-static-${var.environment}"
  
  tags = {
    Environment = var.environment
  }
}

resource "aws_s3_bucket_public_access_block" "static" {
  bucket = aws_s3_bucket.static.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# CloudFront CDN
resource "aws_cloudfront_distribution" "static" {
  origin {
    domain_name = aws_s3_bucket.static.bucket_regional_domain_name
    origin_id   = "S3-${aws_s3_bucket.static.id}"
    
    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.static.cloudfront_access_identity_path
    }
  }
  
  enabled             = true
  default_root_object = "index.html"
  
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${aws_s3_bucket.static.id}"
    
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
    
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 86400
    max_ttl                = 31536000
  }
  
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
  
  viewer_certificate {
    acm_certificate_arn = var.acm_certificate_arn
    ssl_support_method  = "sni-only"
  }
}
```

```hcl
# terraform/variables.tf
variable "aws_region" {
  description = "AWS region"
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  default     = "production"
}

variable "acm_certificate_arn" {
  description = "ACM certificate ARN for CloudFront"
  type        = string
}
```

```bash
# Deploy infrastructure
cd terraform
terraform init
terraform plan -out=plan.out
terraform apply plan.out
```

---

## 1️⃣2️⃣ EXPERT LEVEL - Database Migration Strategy

### Safe Migration Patterns

```python
# apps/tasks/migrations/0015_add_status_index.py
from django.db import migrations


class Migration(migrations.Migration):
    atomic = False  # Allow CREATE INDEX CONCURRENTLY
    
    dependencies = [
        ('tasks', '0014_previous'),
    ]
    
    operations = [
        migrations.RunSQL(
            sql="""
            CREATE INDEX CONCURRENTLY IF NOT EXISTS
            tasks_task_status_idx ON tasks_task (status);
            """,
            reverse_sql="""
            DROP INDEX CONCURRENTLY IF EXISTS tasks_task_status_idx;
            """,
        ),
    ]
```

### Zero-Downtime Column Addition

```python
# Step 1: Add nullable column
class Migration(migrations.Migration):
    operations = [
        migrations.AddField(
            model_name='task',
            name='new_field',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
    ]


# Step 2: Backfill data (separate migration)
def backfill_new_field(apps, schema_editor):
    Task = apps.get_model('tasks', 'Task')
    
    # Batch update to avoid locking
    batch_size = 1000
    while True:
        batch = Task.objects.filter(
            new_field__isnull=True
        ).values_list('id', flat=True)[:batch_size]
        
        if not batch:
            break
        
        Task.objects.filter(id__in=list(batch)).update(
            new_field='default_value'
        )


class Migration(migrations.Migration):
    operations = [
        migrations.RunPython(backfill_new_field, migrations.RunPython.noop),
    ]


# Step 3: Add constraint (after deployment uses new field)
class Migration(migrations.Migration):
    operations = [
        migrations.AlterField(
            model_name='task',
            name='new_field',
            field=models.CharField(max_length=100, default='default_value'),
        ),
    ]
```

### Migration CI Check

```yaml
# .github/workflows/migration-check.yml
name: Migration Safety Check

on: [pull_request]

jobs:
  check-migrations:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Check for dangerous migrations
      run: |
        # Check for ALTER TABLE without CONCURRENTLY
        if grep -r "CREATE INDEX" --include="*.py" apps/*/migrations/ | grep -v "CONCURRENTLY"; then
          echo "ERROR: Use CREATE INDEX CONCURRENTLY"
          exit 1
        fi
        
        # Check for NOT NULL without default
        if grep -r "null=False" --include="*.py" apps/*/migrations/ | grep -v "default="; then
          echo "WARNING: Adding NOT NULL column may lock table"
        fi
    
    - name: Check migration conflicts
      run: |
        python manage.py makemigrations --check --dry-run
```

---

## 📊 Deployment Options Comparison

| Platform | Difficulty | Cost | Scalability | Use Case |
|----------|-----------|------|-------------|----------|
| **VPS (DigitalOcean)** | 🔴 Hard | 💰 Low | ⭐⭐ Manual | Full control |
| **Heroku** | 🟢 Easy | 💰💰 Medium | ⭐⭐⭐ Auto | Quick MVP |
| **AWS** | 🔴 Hard | 💰💰💰 Variable | ⭐⭐⭐⭐ Excellent | Enterprise |
| **Docker** | 🟡 Medium | 💰 Low | ⭐⭐⭐ Good | Anywhere |
| **Kubernetes** | 🔴 Hard | 💰💰 Medium | ⭐⭐⭐⭐⭐ Best | High scale |
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
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json'
        },
        'file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/error.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'json'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
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
| **Senior** | Cloud platforms (Heroku, AWS), CI/CD |
| **Expert** | Kubernetes, Terraform, Prometheus/Grafana, Zero-downtime migrations |

---

## 📋 Complete Deployment Checklist

### Junior ✅
- [ ] DEBUG=False
- [ ] SECRET_KEY from environment
- [ ] ALLOWED_HOSTS configured

### Mid ✅
- [ ] Database with connection pooling
- [ ] Static files collected
- [ ] Gunicorn + Nginx setup
- [ ] Basic health check endpoint

### Senior ✅
- [ ] Docker multi-stage build
- [ ] CI/CD pipeline (GitHub Actions/GitLab CI)
- [ ] HTTPS enabled
- [ ] Security headers set
- [ ] Application monitoring (Sentry)
- [ ] Automated backups

### Expert ✅
- [ ] Kubernetes deployment
- [ ] Horizontal Pod Autoscaler
- [ ] Prometheus metrics + Grafana dashboards
- [ ] Infrastructure as Code (Terraform)
- [ ] Zero-downtime migrations
- [ ] Database migration safety checks
- [ ] Canary/Blue-green deployments
- [ ] Log aggregation (ELK/CloudWatch)
- [ ] Distributed tracing
- [ ] Disaster recovery plan

---

## 🚀 Quick Deploy Commands

```bash
# Traditional
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn config.wsgi:application

# Docker
docker-compose up -d --build

# Heroku
git push heroku main

# Kubernetes
kubectl apply -f k8s/
kubectl rollout status deployment/task-api

# Terraform
terraform plan && terraform apply
```
