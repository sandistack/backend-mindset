# 📊 Monitoring & Observability

## Kenapa Penting?

Tanpa monitoring yang baik:
- ❌ Tidak tahu kapan sistem down
- ❌ Tidak bisa debug production issues
- ❌ Tidak ada visibility ke performance
- ❌ Reaktif bukan proaktif

Dengan monitoring:
- ✅ Detect issues sebelum users complain
- ✅ Understand system behavior
- ✅ Make data-driven decisions
- ✅ Fast incident response

---

## 📚 Daftar Isi

1. [Observability Pillars](#1️⃣-observability-pillars)
2. [Application Logging](#2️⃣-application-logging)
3. [Metrics dengan Prometheus](#3️⃣-metrics-dengan-prometheus)
4. [Error Tracking dengan Sentry](#4️⃣-error-tracking-dengan-sentry)
5. [APM (Application Performance Monitoring)](#5️⃣-apm-application-performance-monitoring)
6. [Log Aggregation (ELK Stack)](#6️⃣-log-aggregation-elk-stack)
7. [Grafana Dashboards](#7️⃣-grafana-dashboards)
8. [Alerting](#8️⃣-alerting)
9. [Health Checks](#9️⃣-health-checks)
10. [Distributed Tracing](#🔟-distributed-tracing)

---

## 1️⃣ Observability Pillars

```
┌─────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY                            │
├─────────────────┬─────────────────┬─────────────────────────┤
│     LOGS        │    METRICS      │        TRACES           │
│                 │                 │                         │
│  What happened  │  How system is  │  Request flow across    │
│  (events)       │  performing     │  services               │
│                 │  (numbers)      │                         │
│  - Errors       │  - CPU/Memory   │  - Request path         │
│  - Requests     │  - Response time│  - Latency breakdown    │
│  - Debug info   │  - Error rate   │  - Service dependencies │
└─────────────────┴─────────────────┴─────────────────────────┘
```

---

## 2️⃣ Application Logging

### JUNIOR: Basic Logging

```python
# apps/tasks/views.py
import logging

logger = logging.getLogger(__name__)

class TaskCreateView(APIView):
    def post(self, request):
        logger.info(f"Creating task for user {request.user.id}")
        
        try:
            task = TaskService.create_task(request.user, request.data)
            logger.info(f"Task {task.id} created successfully")
            return Response({"success": True, "data": task})
        
        except Exception as e:
            logger.error(f"Failed to create task: {str(e)}", exc_info=True)
            raise
```

### MID: Structured Logging

```python
# config/settings/base.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d',
        },
    },
    
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'console_json': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/app.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 10,
            'formatter': 'json',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/error.log',
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 10,
            'formatter': 'json',
        },
    },
    
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console_json', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

```bash
pip install python-json-logger
```

### SENIOR: Contextual Logging

```python
# apps/core/logging.py
import logging
import threading
from functools import wraps

# Thread-local storage for request context
_request_context = threading.local()


class RequestContextFilter(logging.Filter):
    """Add request context to all log records"""
    
    def filter(self, record):
        record.request_id = getattr(_request_context, 'request_id', '-')
        record.user_id = getattr(_request_context, 'user_id', '-')
        record.ip = getattr(_request_context, 'ip', '-')
        return True


def set_request_context(request_id, user_id=None, ip=None):
    _request_context.request_id = request_id
    _request_context.user_id = user_id
    _request_context.ip = ip


def clear_request_context():
    _request_context.request_id = None
    _request_context.user_id = None
    _request_context.ip = None


# Middleware to set context
class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        import uuid
        
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        user_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
        ip = request.META.get('REMOTE_ADDR')
        
        set_request_context(request_id, user_id, ip)
        
        response = self.get_response(request)
        response['X-Request-ID'] = request_id
        
        clear_request_context()
        
        return response
```

```python
# config/settings/base.py
LOGGING = {
    # ...
    'formatters': {
        'with_context': {
            'format': '%(asctime)s [%(request_id)s] [user:%(user_id)s] %(levelname)s %(name)s: %(message)s',
        },
    },
    'filters': {
        'request_context': {
            '()': 'apps.core.logging.RequestContextFilter',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'with_context',
            'filters': ['request_context'],
        },
    },
}
```

---

## 3️⃣ Metrics dengan Prometheus

### Installation

```bash
pip install django-prometheus
```

### Configuration

```python
# config/settings/base.py
INSTALLED_APPS = [
    'django_prometheus',
    # ...
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    # ... other middleware ...
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

# Use prometheus-instrumented database backend
DATABASES = {
    'default': {
        'ENGINE': 'django_prometheus.db.backends.postgresql',
        # ...
    }
}

# Use prometheus-instrumented cache backend
CACHES = {
    'default': {
        'BACKEND': 'django_prometheus.cache.backends.redis.RedisCache',
        # ...
    }
}
```

```python
# config/urls.py
urlpatterns = [
    # ...
    path('', include('django_prometheus.urls')),  # /metrics endpoint
]
```

### Custom Business Metrics

```python
# apps/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge, Summary

# Counters - untuk events yang hanya naik
tasks_created_total = Counter(
    'tasks_created_total',
    'Total tasks created',
    ['priority', 'status']
)

api_requests_total = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status_code']
)

login_attempts_total = Counter(
    'login_attempts_total',
    'Total login attempts',
    ['success']
)

# Histograms - untuk distribusi (latency, size)
request_latency_seconds = Histogram(
    'request_latency_seconds',
    'Request latency in seconds',
    ['endpoint'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
)

task_processing_duration = Histogram(
    'task_processing_duration_seconds',
    'Time to process a task',
    ['task_type'],
    buckets=[0.1, 0.5, 1, 5, 10, 30, 60, 300]
)

# Gauges - untuk values yang bisa naik/turun
active_users = Gauge(
    'active_users',
    'Number of active users in last 5 minutes'
)

pending_tasks = Gauge(
    'pending_tasks',
    'Number of pending tasks',
    ['priority']
)

# Summary - mirip histogram tapi dengan quantiles
response_size_bytes = Summary(
    'response_size_bytes',
    'Response size in bytes',
    ['endpoint']
)
```

### Using Metrics

```python
# apps/tasks/services.py
from apps.core.metrics import tasks_created_total, task_processing_duration
import time


class TaskService:
    @staticmethod
    def create_task(user, data):
        task = Task.objects.create(user=user, **data)
        
        # Increment counter with labels
        tasks_created_total.labels(
            priority=task.priority,
            status=task.status
        ).inc()
        
        return task
    
    @staticmethod
    def process_task(task):
        start = time.time()
        
        # ... process task ...
        
        # Record duration
        duration = time.time() - start
        task_processing_duration.labels(
            task_type=task.task_type
        ).observe(duration)
```

### Metrics Middleware

```python
# apps/core/middleware.py
import time
from apps.core.metrics import api_requests_total, request_latency_seconds


class MetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start = time.time()
        
        response = self.get_response(request)
        
        # Record metrics
        duration = time.time() - start
        endpoint = self._get_endpoint_name(request)
        
        api_requests_total.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=response.status_code
        ).inc()
        
        request_latency_seconds.labels(
            endpoint=endpoint
        ).observe(duration)
        
        return response
    
    def _get_endpoint_name(self, request):
        if request.resolver_match:
            return request.resolver_match.url_name or request.resolver_match.route
        return 'unknown'
```

---

## 4️⃣ Error Tracking dengan Sentry

### Installation

```bash
pip install sentry-sdk
```

### Configuration

```python
# config/settings/production.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

sentry_sdk.init(
    dsn=config('SENTRY_DSN'),
    integrations=[
        DjangoIntegration(
            transaction_style='url',
            middleware_spans=True,
        ),
        CeleryIntegration(),
        RedisIntegration(),
        LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR,
        ),
    ],
    
    # Performance monitoring
    traces_sample_rate=0.1,  # 10% of transactions
    profiles_sample_rate=0.1,  # 10% of profiled transactions
    
    # Environment
    environment=config('ENVIRONMENT', default='production'),
    release=config('APP_VERSION', default='1.0.0'),
    
    # PII Settings
    send_default_pii=True,
    
    # Before send hook
    before_send=filter_sensitive_data,
)


def filter_sensitive_data(event, hint):
    """Filter sensitive data before sending to Sentry"""
    # Remove passwords
    if 'request' in event:
        if 'data' in event['request']:
            if 'password' in event['request']['data']:
                event['request']['data']['password'] = '[FILTERED]'
    
    return event
```

### Custom Error Context

```python
# apps/tasks/views.py
import sentry_sdk

class TaskView(APIView):
    def post(self, request):
        # Add context to Sentry
        sentry_sdk.set_user({
            "id": request.user.id,
            "email": request.user.email,
        })
        
        sentry_sdk.set_context("task_data", {
            "title": request.data.get('title'),
            "priority": request.data.get('priority'),
        })
        
        sentry_sdk.set_tag("feature", "task_creation")
        
        try:
            task = TaskService.create_task(request.user, request.data)
            return Response({"success": True})
        except Exception as e:
            sentry_sdk.capture_exception(e)
            raise
```

### Manual Error Capture

```python
# apps/core/utils.py
import sentry_sdk
from sentry_sdk import capture_message, capture_exception


def log_warning(message, extra=None):
    """Log warning to Sentry"""
    with sentry_sdk.push_scope() as scope:
        if extra:
            for key, value in extra.items():
                scope.set_extra(key, value)
        capture_message(message, level='warning')


def log_error(exception, extra=None):
    """Log error to Sentry with extra context"""
    with sentry_sdk.push_scope() as scope:
        if extra:
            for key, value in extra.items():
                scope.set_extra(key, value)
        capture_exception(exception)


# Usage
try:
    process_payment(order)
except PaymentError as e:
    log_error(e, extra={
        'order_id': order.id,
        'amount': order.total,
        'payment_method': order.payment_method,
    })
    raise
```

---

## 5️⃣ APM (Application Performance Monitoring)

### Django Silk (Development)

```bash
pip install django-silk
```

```python
# config/settings/development.py
INSTALLED_APPS = [
    # ...
    'silk',
]

MIDDLEWARE = [
    'silk.middleware.SilkyMiddleware',
    # ...
]

# Silk settings
SILKY_PYTHON_PROFILER = True
SILKY_PYTHON_PROFILER_BINARY = True
SILKY_PYTHON_PROFILER_RESULT_PATH = '/tmp/silk-profiles/'
SILKY_MAX_REQUEST_BODY_SIZE = 1024  # KB
SILKY_MAX_RESPONSE_BODY_SIZE = 1024  # KB
SILKY_META = True
SILKY_INTERCEPT_PERCENT = 100  # Profile 100% of requests in dev
```

```python
# config/urls.py
if settings.DEBUG:
    urlpatterns += [path('silk/', include('silk.urls', namespace='silk'))]
```

### New Relic (Production)

```bash
pip install newrelic
```

```ini
# newrelic.ini
[newrelic]
license_key = YOUR_LICENSE_KEY
app_name = Task API
monitor_mode = true
log_file = /var/log/newrelic/agent.log
log_level = info

[newrelic:development]
monitor_mode = false

[newrelic:production]
monitor_mode = true
```

```python
# gunicorn.conf.py
import newrelic.agent
newrelic.agent.initialize('/app/newrelic.ini')
```

### Custom Transaction Tracking

```python
# apps/tasks/services.py
import newrelic.agent

class TaskService:
    @newrelic.agent.background_task(name='process_heavy_task')
    def process_heavy_task(self, task_id):
        """Background task dengan custom naming"""
        task = Task.objects.get(id=task_id)
        
        # Add custom attributes
        newrelic.agent.add_custom_attribute('task_id', task_id)
        newrelic.agent.add_custom_attribute('task_type', task.task_type)
        
        # ... process task ...
        
        return result
```

---

## 6️⃣ Log Aggregation (ELK Stack)

### Fluentd Configuration

```yaml
# fluentd/fluent.conf
<source>
  @type tail
  path /var/log/django/*.log
  pos_file /var/log/fluentd/django.pos
  tag django.*
  <parse>
    @type json
    time_key asctime
    time_format %Y-%m-%d %H:%M:%S,%L
  </parse>
</source>

<filter django.**>
  @type record_transformer
  <record>
    hostname "#{Socket.gethostname}"
    service "task-api"
    environment "#{ENV['ENVIRONMENT']}"
  </record>
</filter>

<match django.**>
  @type elasticsearch
  host elasticsearch
  port 9200
  logstash_format true
  logstash_prefix django
  <buffer>
    @type file
    path /var/log/fluentd/buffer/django
    flush_interval 5s
  </buffer>
</match>
```

### Docker Compose for ELK

```yaml
# docker-compose.elk.yml
version: '3.8'

services:
  elasticsearch:
    image: elasticsearch:8.10.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"
  
  logstash:
    image: logstash:8.10.0
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline
    depends_on:
      - elasticsearch
  
  kibana:
    image: kibana:8.10.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch
  
  fluentd:
    image: fluent/fluentd:v1.16
    volumes:
      - ./fluentd:/fluentd/etc
      - /var/log/django:/var/log/django:ro
    depends_on:
      - elasticsearch

volumes:
  elasticsearch_data:
```

### Logstash Pipeline

```ruby
# logstash/pipeline/django.conf
input {
  beats {
    port => 5044
  }
}

filter {
  if [fields][type] == "django" {
    json {
      source => "message"
    }
    
    date {
      match => ["asctime", "yyyy-MM-dd HH:mm:ss,SSS"]
      target => "@timestamp"
    }
    
    mutate {
      remove_field => ["message", "asctime"]
    }
    
    # Extract request_id and user_id
    if [request_id] {
      mutate {
        add_field => { "trace_id" => "%{request_id}" }
      }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "django-logs-%{+YYYY.MM.dd}"
  }
}
```

---

## 7️⃣ Grafana Dashboards

### Django API Dashboard

```json
{
  "dashboard": {
    "title": "Django API Dashboard",
    "uid": "django-api",
    "panels": [
      {
        "title": "Requests per Second",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
        "targets": [
          {
            "expr": "rate(django_http_requests_total_by_method_total[5m])",
            "legendFormat": "{{method}}"
          }
        ]
      },
      {
        "title": "Response Time (p95)",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(django_http_requests_latency_seconds_by_view_method_bucket[5m]))",
            "legendFormat": "{{view}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "gauge",
        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 8},
        "targets": [
          {
            "expr": "sum(rate(django_http_responses_total_by_status_total{status=~\"5..\"}[5m])) / sum(rate(django_http_responses_total_by_status_total[5m])) * 100"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"color": "green", "value": null},
                {"color": "yellow", "value": 1},
                {"color": "red", "value": 5}
              ]
            }
          }
        }
      },
      {
        "title": "Database Connections",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 6, "x": 6, "y": 8},
        "targets": [
          {
            "expr": "django_db_execute_total",
            "legendFormat": "{{database}}"
          }
        ]
      },
      {
        "title": "Cache Hit Rate",
        "type": "stat",
        "gridPos": {"h": 8, "w": 6, "x": 12, "y": 8},
        "targets": [
          {
            "expr": "sum(rate(django_cache_get_hits_total[5m])) / sum(rate(django_cache_get_total[5m])) * 100"
          }
        ]
      },
      {
        "title": "Active Tasks",
        "type": "stat",
        "gridPos": {"h": 8, "w": 6, "x": 18, "y": 8},
        "targets": [
          {
            "expr": "pending_tasks"
          }
        ]
      }
    ]
  }
}
```

### Provisioning Dashboards

```yaml
# grafana/provisioning/dashboards/dashboard.yml
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    options:
      path: /var/lib/grafana/dashboards
```

---

## 8️⃣ Alerting

### Prometheus Alerting Rules

```yaml
# prometheus/alerts/django.yml
groups:
  - name: django-alerts
    rules:
      # High Error Rate
      - alert: HighErrorRate
        expr: |
          sum(rate(django_http_responses_total_by_status_total{status=~"5.."}[5m]))
          / sum(rate(django_http_responses_total_by_status_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is above 5% for the last 5 minutes"
      
      # Slow Response Time
      - alert: SlowResponseTime
        expr: |
          histogram_quantile(0.95, rate(django_http_requests_latency_seconds_by_view_method_bucket[5m])) > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Slow response time"
          description: "95th percentile response time is above 2 seconds"
      
      # High Memory Usage
      - alert: HighMemoryUsage
        expr: process_resident_memory_bytes / 1024 / 1024 > 500
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Application is using more than 500MB of memory"
      
      # Database Connection Pool Exhausted
      - alert: DatabaseConnectionPoolLow
        expr: django_db_execute_total > 100
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Database connections high"
          description: "Database connection count is unusually high"
```

### Alertmanager Configuration

```yaml
# alertmanager/config.yml
global:
  slack_api_url: 'https://hooks.slack.com/services/xxx/yyy/zzz'

route:
  receiver: 'slack-notifications'
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty-critical'
    - match:
        severity: warning
      receiver: 'slack-notifications'

receivers:
  - name: 'slack-notifications'
    slack_configs:
      - channel: '#alerts'
        send_resolved: true
        title: '{{ .Status | toUpper }}: {{ .CommonAnnotations.summary }}'
        text: '{{ .CommonAnnotations.description }}'
  
  - name: 'pagerduty-critical'
    pagerduty_configs:
      - service_key: 'your-pagerduty-key'
        severity: critical
```

### Django-based Alerting

```python
# apps/core/alerts.py
import requests
from django.conf import settings


class AlertService:
    @staticmethod
    def send_slack_alert(message, severity='info', channel=None):
        """Send alert to Slack"""
        webhook_url = settings.SLACK_WEBHOOK_URL
        channel = channel or settings.SLACK_ALERT_CHANNEL
        
        color_map = {
            'info': '#36a64f',
            'warning': '#ffcc00',
            'critical': '#ff0000'
        }
        
        payload = {
            "channel": channel,
            "attachments": [{
                "color": color_map.get(severity, '#36a64f'),
                "text": message,
                "footer": f"Task API | {settings.ENVIRONMENT}",
            }]
        }
        
        requests.post(webhook_url, json=payload)
    
    @staticmethod
    def send_pagerduty_alert(title, description, severity='warning'):
        """Send alert to PagerDuty"""
        requests.post(
            'https://events.pagerduty.com/v2/enqueue',
            json={
                "routing_key": settings.PAGERDUTY_ROUTING_KEY,
                "event_action": "trigger",
                "payload": {
                    "summary": title,
                    "source": "task-api",
                    "severity": severity,
                    "custom_details": {"description": description}
                }
            }
        )


# Usage
from apps.core.alerts import AlertService

try:
    process_critical_task()
except CriticalError as e:
    AlertService.send_pagerduty_alert(
        title="Critical task processing failed",
        description=str(e),
        severity="critical"
    )
    raise
```

---

## 9️⃣ Health Checks

### Comprehensive Health Check

```python
# apps/core/views.py
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import redis


def health_check(request):
    """
    Comprehensive health check endpoint
    
    Returns:
        - healthy: All systems operational
        - degraded: Some systems have issues
        - unhealthy: Critical systems down
    """
    checks = {}
    status = 'healthy'
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks['database'] = {'status': 'ok', 'latency_ms': 0}
    except Exception as e:
        checks['database'] = {'status': 'error', 'message': str(e)}
        status = 'unhealthy'
    
    # Redis/Cache check
    try:
        cache.set('health_check', 'ok', 10)
        result = cache.get('health_check')
        if result == 'ok':
            checks['cache'] = {'status': 'ok'}
        else:
            checks['cache'] = {'status': 'error', 'message': 'Cache read/write failed'}
            status = 'degraded'
    except Exception as e:
        checks['cache'] = {'status': 'error', 'message': str(e)}
        status = 'degraded'
    
    # Celery check
    try:
        from celery import current_app
        i = current_app.control.inspect()
        if i.ping():
            checks['celery'] = {'status': 'ok'}
        else:
            checks['celery'] = {'status': 'error', 'message': 'No workers responding'}
            status = 'degraded'
    except Exception as e:
        checks['celery'] = {'status': 'error', 'message': str(e)}
        status = 'degraded'
    
    # External API check (optional)
    try:
        import requests
        response = requests.get('https://api.external.com/health', timeout=5)
        if response.status_code == 200:
            checks['external_api'] = {'status': 'ok'}
        else:
            checks['external_api'] = {'status': 'degraded'}
    except:
        checks['external_api'] = {'status': 'error'}
    
    http_status = 200 if status == 'healthy' else (503 if status == 'unhealthy' else 200)
    
    return JsonResponse({
        'status': status,
        'checks': checks,
        'version': settings.APP_VERSION,
    }, status=http_status)


def liveness_probe(request):
    """Simple liveness check for Kubernetes"""
    return JsonResponse({'status': 'alive'})


def readiness_probe(request):
    """Readiness check - is app ready to receive traffic?"""
    try:
        # Check database
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({'status': 'ready'})
    except:
        return JsonResponse({'status': 'not ready'}, status=503)
```

```python
# config/urls.py
urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('health/live/', liveness_probe, name='liveness'),
    path('health/ready/', readiness_probe, name='readiness'),
]
```

---

## 🔟 Distributed Tracing

### OpenTelemetry Setup

```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-django opentelemetry-exporter-jaeger
```

```python
# config/telemetry.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor


def configure_tracing():
    # Set up tracer provider
    trace.set_tracer_provider(TracerProvider())
    
    # Configure Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name="jaeger",
        agent_port=6831,
    )
    
    # Add span processor
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(jaeger_exporter)
    )
    
    # Instrument Django
    DjangoInstrumentor().instrument()
    
    # Instrument HTTP requests
    RequestsInstrumentor().instrument()
    
    # Instrument PostgreSQL
    Psycopg2Instrumentor().instrument()


# Call in wsgi.py
configure_tracing()
```

### Custom Spans

```python
# apps/tasks/services.py
from opentelemetry import trace

tracer = trace.get_tracer(__name__)


class TaskService:
    @staticmethod
    def create_task(user, data):
        with tracer.start_as_current_span("create_task") as span:
            span.set_attribute("user.id", user.id)
            span.set_attribute("task.priority", data.get('priority'))
            
            # Validate
            with tracer.start_as_current_span("validate_data"):
                validated_data = TaskSerializer(data=data)
                validated_data.is_valid(raise_exception=True)
            
            # Create
            with tracer.start_as_current_span("save_to_db"):
                task = Task.objects.create(user=user, **validated_data.validated_data)
            
            # Notify
            with tracer.start_as_current_span("send_notification"):
                notify_task_created(task)
            
            span.set_attribute("task.id", task.id)
            
            return task
```

---

## 📋 Monitoring Checklist

### Junior ✅
- [ ] Basic logging setup
- [ ] Simple health check endpoint
- [ ] Error logging dengan exc_info

### Mid ✅
- [ ] Structured JSON logging
- [ ] Sentry untuk error tracking
- [ ] Request ID tracking
- [ ] Basic metrics (request count, latency)

### Senior ✅
- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK/CloudWatch)
- [ ] Comprehensive health checks

### Expert ✅
- [ ] Custom business metrics
- [ ] Distributed tracing (Jaeger/Zipkin)
- [ ] APM integration (New Relic/Datadog)
- [ ] Multi-channel alerting (Slack, PagerDuty)
- [ ] SLO/SLI monitoring
- [ ] Chaos engineering readiness
