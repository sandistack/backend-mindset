# 📝 LOGGING STRATEGIES - Django (Junior → Senior)

Dokumentasi lengkap tentang logging di Django, dari cara basic sampai advanced patterns.

---

## 🎯 Kenapa Logging Penting?

| Benefit | Penjelasan |
|---------|------------|
| **Debugging** | Tahu apa yang terjadi saat error |
| **Monitoring** | Track performance & user behavior |
| **Audit Trail** | Siapa melakukan apa & kapan |
| **Compliance** | Regulatory requirements (GDPR, etc.) |

---

## 📊 File Logging vs Database Logging

| Aspek | File Logging | Database Logging |
|-------|-------------|------------------|
| **Use Case** | Technical logs (errors, debug) | User activity audit |
| **Speed** | ⚡ Cepat (write to disk) | 🐢 Slower (DB query) |
| **Query** | Susah (grep/search file) | Mudah (SQL query) |
| **Retention** | Auto-rotate (7-90 hari) | Manual cleanup |
| **Best For** | Developer debugging | Admin dashboard |

**Hybrid Approach (Recommended):**
- File Logging → Technical logs
- Database Logging → Audit trail

---

## 1️⃣ JUNIOR LEVEL - Basic Logging

### Setup Dasar (settings.py)

```python
# config/settings/base.py
import os

LOGS_DIR = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '[{levelname}] {asctime} | {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGS_DIR, 'app.log'),
            'formatter': 'simple',
        },
    },
    'loggers': {
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    },
}
```

### Cara Pakai di Code

```python
# apps/tasks/services.py
import logging

logger = logging.getLogger('apps')

def create_task(user, data):
    logger.info(f"Creating task for user {user.username}")
    
    try:
        task = Task.objects.create(**data)
        logger.info(f"Task created: ID={task.id}")
        return task
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise
```

**Log Levels:**
- `DEBUG` → Detailed info (development only)
- `INFO` → Normal operations
- `WARNING` → Something unexpected but still works
- `ERROR` → Error occurred
- `CRITICAL` → System-level failure

---

## 2️⃣ MID LEVEL - Auto-Rotating Logs

### RotatingFileHandler (berdasarkan size)

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '[{levelname}] {asctime} | {name} | {funcName} | {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'app.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,      # Keep 5 old files
            'formatter': 'detailed',
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'error.log'),
            'maxBytes': 10485760,
            'backupCount': 5,
            'formatter': 'detailed',
            'level': 'ERROR',
        },
    },
    'loggers': {
        'apps': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
        },
    },
}
```

**Result:**
```
logs/
├── app.log          # Current
├── app.log.1        # 10MB ago
├── app.log.2        # 20MB ago
├── error.log
└── error.log.1
```

### TimedRotatingFileHandler (berdasarkan waktu)

```python
'file': {
    'class': 'logging.handlers.TimedRotatingFileHandler',
    'filename': os.path.join(LOGS_DIR, 'app.log'),
    'when': 'midnight',     # Rotate setiap midnight
    'interval': 1,          # Setiap 1 hari
    'backupCount': 30,      # Keep 30 days
    'formatter': 'detailed',
},
```

**Options:**
- `when='S'` → Seconds
- `when='M'` → Minutes
- `when='H'` → Hours
- `when='D'` → Days
- `when='midnight'` → Setiap midnight

---

## 3️⃣ MID-SENIOR LEVEL - Database Audit Logging

### Create AuditLog Model

```python
# apps/core/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class AuditLog(models.Model):
    """
    Track user activities di database
    """
    
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('ERROR', 'Error'),
    ]
    
    STATUS_CHOICES = [
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]
    
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='audit_logs'
    )
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, db_index=True)
    feature = models.CharField(max_length=100, db_index=True)  # 'task', 'user', etc.
    description = models.TextField()
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='SUCCESS',
        db_index=True
    )
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'action']),
            models.Index(fields=['feature', 'status']),
        ]
    
    def __str__(self):
        return f"{self.action} | {self.feature} | {self.user}"
```

### Helper Function

```python
# apps/core/utils/audit.py
from apps.core.models import AuditLog
import logging

logger = logging.getLogger('apps')

def log_activity(user, action, feature, description, request=None, status='SUCCESS'):
    """
    Log user activity ke database
    
    Args:
        user: User instance
        action: 'CREATE', 'UPDATE', 'DELETE', 'ERROR'
        feature: 'task', 'user', etc.
        description: Human-readable description
        request: HTTP request object (optional)
        status: 'SUCCESS' or 'FAILED'
    
    Example:
        log_activity(
            user=request.user,
            action='CREATE',
            feature='task',
            description='Created task: Buy milk',
            request=request
        )
    """
    
    # Extract IP & User Agent
    ip_address = None
    user_agent = ''
    
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Save to database
    audit_log = AuditLog.objects.create(
        user=user,
        action=action,
        feature=feature,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        status=status
    )
    
    # Also log to file
    log_message = f"{action} | {feature} | {description} | User: {user.username if user else 'Anonymous'}"
    
    if status == 'SUCCESS':
        logger.info(log_message)
    else:
        logger.error(log_message)
    
    return audit_log
```

### Pakai di Service Layer

```python
# apps/tasks/services.py
from apps.core.utils.audit import log_activity

class TaskService:
    
    @staticmethod
    def create_task(user, validated_data, request=None):
        try:
            task = Task.objects.create(user=user, **validated_data)
            
            # Audit log (SUCCESS)
            log_activity(
                user=user,
                action='CREATE',
                feature='task',
                description=f"Created task: {task.title}",
                request=request,
                status='SUCCESS'
            )
            
            return task
            
        except Exception as e:
            # Audit log (FAILED)
            log_activity(
                user=user,
                action='ERROR',
                feature='task',
                description=f"Error creating task: {str(e)}",
                request=request,
                status='FAILED'
            )
            
            raise
```

---

## 4️⃣ SENIOR LEVEL - Advanced Patterns

### A) Auto-Cleanup Old Logs (Database)

```python
# apps/core/management/commands/cleanup_audit_logs.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.core.models import AuditLog

class Command(BaseCommand):
    help = 'Delete audit logs older than 90 days'

    def handle(self, *args, **options):
        cutoff_date = timezone.now() - timedelta(days=90)
        deleted_count, _ = AuditLog.objects.filter(timestamp__lt=cutoff_date).delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted {deleted_count} old audit logs')
        )
```

**Jalankan via cron:**
```bash
# Setiap hari jam 2 pagi
0 2 * * * cd /path/to/project && python manage.py cleanup_audit_logs
```

### B) Structured Logging (JSON Format)

```python
# Install: pip install python-json-logger

LOGGING = {
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        },
    },
    'handlers': {
        'json_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'app.json'),
            'maxBytes': 10485760,
            'backupCount': 5,
            'formatter': 'json',
        },
    },
}
```

**Output:**
```json
{
  "asctime": "2026-01-31 10:30:45",
  "name": "apps",
  "levelname": "INFO",
  "message": "Task created: ID=123"
}
```

### C) Custom Log Filters

```python
# apps/core/logging_filters.py
import logging

class RequireDebugFalse(logging.Filter):
    """Only log when DEBUG=False (production)"""
    def filter(self, record):
        from django.conf import settings
        return not settings.DEBUG

class RequireDebugTrue(logging.Filter):
    """Only log when DEBUG=True (development)"""
    def filter(self, record):
        from django.conf import settings
        return settings.DEBUG
```

```python
# settings.py
LOGGING = {
    'filters': {
        'require_debug_false': {
            '()': 'apps.core.logging_filters.RequireDebugFalse',
        },
    },
    'handlers': {
        'production_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'production.log'),
            'filters': ['require_debug_false'],
        },
    },
}
```

### D) Sentry Integration (Production Monitoring)

```bash
pip install sentry-sdk
```

```python
# config/settings/production.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
    send_default_pii=True
)
```

### E) Decorator Pattern (DRY Logging)

```python
# apps/core/decorators.py
import logging
from functools import wraps
from apps.core.utils.audit import log_activity

logger = logging.getLogger('apps')

def log_service_call(feature, action='EXECUTE'):
    """
    Decorator untuk auto-log service calls
    
    Usage:
        @log_service_call(feature='task', action='CREATE')
        def create_task(user, data, request=None):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = kwargs.get('user') or (args[0] if args else None)
            request = kwargs.get('request')
            
            try:
                logger.info(f"[{feature}] {action} started by {user}")
                
                result = func(*args, **kwargs)
                
                log_activity(
                    user=user,
                    action=action,
                    feature=feature,
                    description=f"{func.__name__} executed successfully",
                    request=request,
                    status='SUCCESS'
                )
                
                return result
                
            except Exception as e:
                logger.error(f"[{feature}] {action} failed: {e}", exc_info=True)
                
                log_activity(
                    user=user,
                    action='ERROR',
                    feature=feature,
                    description=f"{func.__name__} failed: {str(e)}",
                    request=request,
                    status='FAILED'
                )
                
                raise
        
        return wrapper
    return decorator
```

**Pakai:**
```python
# apps/tasks/services.py
from apps.core.decorators import log_service_call

class TaskService:
    
    @staticmethod
    @log_service_call(feature='task', action='CREATE')
    def create_task(user, validated_data, request=None):
        # No need manual logging, decorator handle it
        return Task.objects.create(user=user, **validated_data)
    
    @staticmethod
    @log_service_call(feature='task', action='UPDATE')
    def update_task(task, validated_data, request=None):
        for key, value in validated_data.items():
            setattr(task, key, value)
        task.save()
        return task
```

---

## 📋 Best Practices Summary

| Level | Practice |
|-------|----------|
| **Junior** | Basic logging di service layer, console + file |
| **Mid** | Auto-rotating logs, separate error.log |
| **Senior** | Hybrid (File + DB), structured logging, Sentry |
| **Expert** | Decorator pattern, custom filters, auto-cleanup |

---

## 🚨 What NOT to Log

❌ **Never log:**
- Passwords (plain or hashed)
- API keys / secrets
- Credit card numbers
- Personal Identifiable Information (PII) - harus encrypted
- Full JWT tokens

✅ **Safe to log:**
- User ID (bukan password)
- Actions (CREATE, UPDATE, DELETE)
- Timestamps
- IP addresses (with user consent)
- Error types (bukan full stack trace di production)

---

## 🔍 Log Aggregation Tools

| Tool | Best For | Complexity |
|------|----------|-----------|
| **Sentry** | Error tracking | Low |
| **Logstash** | Large scale, ELK stack | High |
| **Papertrail** | Small-medium apps | Low |
| **Datadog** | Enterprise monitoring | High |
| **CloudWatch** | AWS environments | Medium |

---

## 📚 Further Reading

- [Django Logging Documentation](https://docs.djangoproject.com/en/4.2/topics/logging/)
- [Python Logging Cookbook](https://docs.python.org/3/howto/logging-cookbook.html)
- [Sentry Django Integration](https://docs.sentry.io/platforms/python/guides/django/)
