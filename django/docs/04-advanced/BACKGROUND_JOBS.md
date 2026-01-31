# ⚙️ BACKGROUND JOBS - Django (Junior → Senior)

Dokumentasi lengkap tentang background jobs, async tasks, dan scheduled tasks di Django.

---

## 🎯 Kenapa Butuh Background Jobs?

### Problem dengan Synchronous

```python
# ❌ Blocking request (user tunggu lama)
def register_user(request):
    user = User.objects.create(...)
    
    # Send welcome email (3 seconds)
    send_mail(...)
    
    # Generate report (10 seconds)
    generate_report(...)
    
    # Update analytics (2 seconds)
    update_analytics(...)
    
    return Response({'success': True})  # User tunggu 15 detik! 😱
```

### Solution dengan Async

```python
# ✅ Non-blocking (user langsung dapat response)
def register_user(request):
    user = User.objects.create(...)
    
    # Run in background
    send_welcome_email.delay(user.id)  # Async
    generate_report.delay(user.id)     # Async
    update_analytics.delay(user.id)    # Async
    
    return Response({'success': True})  # User dapat response < 1 detik! 🚀
```

---

## 1️⃣ JUNIOR LEVEL - Threading (Simple)

### Basic Threading

```python
import threading
from django.core.mail import send_mail

def send_email_background(user_email, subject, message):
    """
    Send email in background thread
    """
    def send():
        send_mail(
            subject=subject,
            message=message,
            from_email='noreply@example.com',
            recipient_list=[user_email],
        )
    
    thread = threading.Thread(target=send)
    thread.start()


# Usage in views
def register(request):
    user = User.objects.create(...)
    
    # Send email in background
    send_email_background(
        user.email,
        'Welcome!',
        'Thank you for registering'
    )
    
    return Response({'success': True})
```

**⚠️ Limitations:**
- ❌ No retry mechanism
- ❌ No monitoring
- ❌ Task lost if server restart
- ❌ Not scalable
- ✅ Good for: Simple, non-critical tasks

---

## 2️⃣ MID LEVEL - Celery Basics

### Install & Setup

```bash
pip install celery redis
```

### Configuration

```python
# config/celery.py
import os
from celery import Celery

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('task_api')

# Load config from Django settings (prefix: CELERY_)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()


# config/__init__.py
from .celery import app as celery_app

__all__ = ('celery_app',)


# config/settings/base.py
# Celery configuration
CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
```

### Create Tasks

```python
# apps/tasks/tasks.py
from celery import shared_task
from django.core.mail import send_mail
import time

@shared_task
def send_email_task(user_email, subject, message):
    """
    Celery task untuk send email
    """
    send_mail(
        subject=subject,
        message=message,
        from_email='noreply@example.com',
        recipient_list=[user_email],
    )
    
    return f"Email sent to {user_email}"


@shared_task
def generate_report_task(user_id):
    """
    Generate user report (heavy task)
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    user = User.objects.get(id=user_id)
    
    # Simulate heavy processing
    time.sleep(10)
    
    report = f"Report for {user.email} generated"
    
    return report


@shared_task
def cleanup_old_tasks():
    """
    Cleanup tasks older than 30 days
    """
    from datetime import timedelta
    from django.utils import timezone
    from apps.tasks.models import Task
    
    cutoff_date = timezone.now() - timedelta(days=30)
    
    deleted_count = Task.objects.filter(
        created_at__lt=cutoff_date,
        status='DONE'
    ).delete()[0]
    
    return f"Deleted {deleted_count} old tasks"
```

### Use in Views

```python
# apps/authentication/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.tasks.tasks import send_email_task, generate_report_task

class RegisterView(APIView):
    
    def post(self, request):
        # Create user
        user = User.objects.create_user(
            username=request.data['username'],
            email=request.data['email'],
            password=request.data['password']
        )
        
        # Send email asynchronously
        send_email_task.delay(
            user.email,
            'Welcome to Task API!',
            'Thank you for registering'
        )
        
        # Generate report asynchronously
        generate_report_task.delay(user.id)
        
        return Response({
            'success': True,
            'message': 'User registered. Email will be sent shortly.'
        })
```

### Run Celery Worker

```bash
# Terminal 1: Django server
python manage.py runserver

# Terminal 2: Celery worker
celery -A config worker --loglevel=info

# Terminal 3: Redis (if not running)
redis-server
```

---

## 3️⃣ MID-SENIOR LEVEL - Advanced Celery

### A) Task Options

```python
@shared_task(
    bind=True,              # Access to task instance (self)
    max_retries=3,          # Max retry attempts
    default_retry_delay=60, # Retry after 60 seconds
    time_limit=300,         # Hard time limit (5 minutes)
    soft_time_limit=240,    # Soft time limit (4 minutes)
)
def send_email_with_retry(self, user_email, subject, message):
    """
    Send email with retry logic
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email='noreply@example.com',
            recipient_list=[user_email],
        )
        
        return f"Email sent to {user_email}"
    
    except Exception as exc:
        # Retry if failed
        raise self.retry(exc=exc, countdown=60)  # Retry after 60 seconds
```

### B) Task Chaining

```python
from celery import chain

# Execute tasks in sequence
@shared_task
def step1(user_id):
    print(f"Step 1: Processing user {user_id}")
    return user_id

@shared_task
def step2(user_id):
    print(f"Step 2: Processing user {user_id}")
    return user_id

@shared_task
def step3(user_id):
    print(f"Step 3: Finalizing user {user_id}")
    return f"Completed for user {user_id}"


# Chain tasks
workflow = chain(step1.s(123), step2.s(), step3.s())
result = workflow.apply_async()

# Or shorthand
(step1.s(123) | step2.s() | step3.s()).apply_async()
```

### C) Task Groups (Parallel)

```python
from celery import group

# Execute tasks in parallel
@shared_task
def process_item(item_id):
    print(f"Processing item {item_id}")
    return item_id


# Group tasks (run parallel)
job = group(
    process_item.s(1),
    process_item.s(2),
    process_item.s(3),
    process_item.s(4),
)

result = job.apply_async()

# Wait for all tasks to complete
results = result.get()  # [1, 2, 3, 4]
```

### D) Task Callbacks

```python
from celery import chord

# Chord: group + callback
@shared_task
def process_task(task_id):
    print(f"Processing {task_id}")
    return task_id

@shared_task
def finalize(results):
    print(f"All tasks completed: {results}")
    return f"Finalized {len(results)} tasks"


# Run tasks in parallel, then callback
callback = chord(
    (process_task.s(i) for i in range(1, 5)),
    finalize.s()
)

result = callback.apply_async()
```

---

## 4️⃣ SENIOR LEVEL - Periodic Tasks (Celery Beat)

### Install Celery Beat

```bash
pip install django-celery-beat
```

### Configuration

```python
# config/settings/base.py
INSTALLED_APPS += ['django_celery_beat']

# Celery Beat configuration
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
```

```bash
# Run migrations
python manage.py migrate django_celery_beat
```

### Define Periodic Tasks

```python
# apps/tasks/tasks.py
from celery import shared_task

@shared_task
def cleanup_old_tasks():
    """
    Run daily to cleanup old tasks
    """
    from datetime import timedelta
    from django.utils import timezone
    from apps.tasks.models import Task
    
    cutoff = timezone.now() - timedelta(days=30)
    deleted = Task.objects.filter(
        created_at__lt=cutoff,
        status='DONE'
    ).delete()[0]
    
    return f"Deleted {deleted} old tasks"


@shared_task
def send_daily_digest():
    """
    Send daily email digest to all users
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    users = User.objects.filter(is_active=True)
    
    for user in users:
        # Send digest email
        send_mail(
            subject='Daily Task Digest',
            message='Here are your tasks for today...',
            from_email='noreply@example.com',
            recipient_list=[user.email],
        )
    
    return f"Sent digest to {users.count()} users"


@shared_task
def backup_database():
    """
    Backup database every 6 hours
    """
    import subprocess
    from datetime import datetime
    
    backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    
    subprocess.run([
        'pg_dump',
        '-U', 'postgres',
        '-d', 'taskdb',
        '-f', f'/backups/{backup_file}'
    ])
    
    return f"Backup created: {backup_file}"
```

### Schedule in Django Admin

```python
# Run Celery Beat
celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# Or combined worker + beat
celery -A config worker --beat --loglevel=info
```

**Schedule via Django Admin:**
1. Go to `/admin/django_celery_beat/periodictask/`
2. Add periodic task:
   - Name: "Cleanup Old Tasks"
   - Task: `apps.tasks.tasks.cleanup_old_tasks`
   - Schedule: Crontab `0 2 * * *` (every day at 2 AM)

### Schedule in Code

```python
# config/celery.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    'cleanup-old-tasks': {
        'task': 'apps.tasks.tasks.cleanup_old_tasks',
        'schedule': crontab(hour=2, minute=0),  # Every day at 2 AM
    },
    'send-daily-digest': {
        'task': 'apps.tasks.tasks.send_daily_digest',
        'schedule': crontab(hour=8, minute=0),  # Every day at 8 AM
    },
    'backup-database': {
        'task': 'apps.tasks.tasks.backup_database',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
    },
}
```

---

## 5️⃣ SENIOR LEVEL - Task Monitoring

### A) Track Task State

```python
from celery.result import AsyncResult

# Get task result
def check_task_status(request, task_id):
    """
    Check status of async task
    """
    result = AsyncResult(task_id)
    
    return Response({
        'task_id': task_id,
        'status': result.status,  # PENDING, STARTED, SUCCESS, FAILURE
        'result': result.result if result.ready() else None,
    })


# Usage in views
class TaskView(APIView):
    
    def post(self, request):
        # Start async task
        task = generate_report_task.delay(request.user.id)
        
        return Response({
            'task_id': task.id,
            'status': 'Processing...',
            'check_url': f'/api/tasks/status/{task.id}/'
        })
    
    def get(self, request, task_id):
        # Check task status
        result = AsyncResult(task_id)
        
        return Response({
            'task_id': task_id,
            'status': result.status,
            'result': result.result if result.ready() else None
        })
```

### B) Custom Task State

```python
@shared_task(bind=True)
def long_running_task(self, total_items):
    """
    Task with progress tracking
    """
    for i in range(total_items):
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={
                'current': i + 1,
                'total': total_items,
                'percent': int((i + 1) / total_items * 100)
            }
        )
        
        # Do work
        time.sleep(1)
    
    return {'status': 'Complete', 'total': total_items}


# Check progress
def task_progress(request, task_id):
    result = AsyncResult(task_id)
    
    if result.state == 'PROGRESS':
        response = {
            'state': result.state,
            'current': result.info.get('current', 0),
            'total': result.info.get('total', 1),
            'percent': result.info.get('percent', 0),
        }
    elif result.state == 'SUCCESS':
        response = {
            'state': result.state,
            'result': result.result
        }
    else:
        response = {'state': result.state}
    
    return Response(response)
```

---

## 6️⃣ EXPERT LEVEL - Celery Best Practices

### A) Task Result Persistence

```python
# config/settings/base.py
# Store task results in Django database
CELERY_RESULT_BACKEND = 'django-db'

# Install
pip install django-celery-results

# Add to INSTALLED_APPS
INSTALLED_APPS += ['django_celery_results']

# Migrate
python manage.py migrate django_celery_results
```

### B) Task Routing

```python
# config/celery.py
# Different queues for different task types
app.conf.task_routes = {
    'apps.tasks.tasks.send_email_task': {'queue': 'emails'},
    'apps.tasks.tasks.generate_report_task': {'queue': 'reports'},
    'apps.tasks.tasks.cleanup_old_tasks': {'queue': 'maintenance'},
}


# Run workers for specific queues
# Terminal 1: Email worker
celery -A config worker -Q emails --loglevel=info

# Terminal 2: Report worker
celery -A config worker -Q reports --loglevel=info

# Terminal 3: Maintenance worker
celery -A config worker -Q maintenance --loglevel=info
```

### C) Task Rate Limiting

```python
@shared_task(rate_limit='10/m')  # Max 10 tasks per minute
def send_email_task(user_email, subject, message):
    """
    Rate-limited email task
    """
    send_mail(...)
    return "Email sent"


@shared_task(rate_limit='100/h')  # Max 100 tasks per hour
def api_call_task(endpoint):
    """
    Rate-limited API calls
    """
    response = requests.get(endpoint)
    return response.json()
```

### D) Task Priority

```python
# config/celery.py
app.conf.task_default_priority = 5  # Default priority

# High priority task
send_email_task.apply_async(
    args=[user_email, subject, message],
    priority=9  # Higher priority (0-9, 9 is highest)
)

# Low priority task
cleanup_task.apply_async(
    priority=1  # Lower priority
)
```

---

## 7️⃣ EXPERT LEVEL - Alternative: Django-Q

### Why Django-Q?

- ✅ Simpler than Celery
- ✅ Native Django integration
- ✅ Django ORM for storage
- ✅ Good for small-medium projects

### Install & Setup

```bash
pip install django-q
```

```python
# config/settings/base.py
INSTALLED_APPS += ['django_q']

Q_CLUSTER = {
    'name': 'TaskAPI',
    'workers': 4,
    'recycle': 500,
    'timeout': 300,
    'compress': True,
    'save_limit': 250,
    'queue_limit': 500,
    'cpu_affinity': 1,
    'label': 'Django Q',
    'redis': {
        'host': '127.0.0.1',
        'port': 6379,
        'db': 0,
    }
}
```

```bash
# Run migrations
python manage.py migrate

# Run worker
python manage.py qcluster
```

### Create Tasks

```python
from django_q.tasks import async_task, schedule
from django_q.models import Schedule

# Async task
def send_email(user_email, subject, message):
    from django.core.mail import send_mail
    
    send_mail(
        subject=subject,
        message=message,
        from_email='noreply@example.com',
        recipient_list=[user_email],
    )


# Use in views
def register(request):
    user = User.objects.create(...)
    
    # Run async
    async_task(
        'apps.tasks.utils.send_email',
        user.email,
        'Welcome!',
        'Thank you for registering'
    )
    
    return Response({'success': True})


# Schedule periodic task
schedule(
    'apps.tasks.utils.cleanup_old_tasks',
    schedule_type=Schedule.DAILY,
    next_run=timezone.now() + timedelta(hours=1)
)
```

---

## 📊 Comparison: Threading vs Celery vs Django-Q

| Feature | Threading | Celery | Django-Q |
|---------|-----------|--------|----------|
| **Setup** | 🟢 None | 🔴 Complex | 🟡 Medium |
| **Reliability** | 🔴 Poor | 🟢 Excellent | 🟢 Good |
| **Monitoring** | ❌ No | ✅ Yes | ✅ Yes |
| **Retry** | ❌ No | ✅ Yes | ✅ Yes |
| **Scheduled Tasks** | ❌ No | ✅ Yes (Beat) | ✅ Yes |
| **Scalability** | 🔴 Poor | 🟢 Excellent | 🟡 Good |
| **Learning Curve** | 🟢 Easy | 🔴 Steep | 🟡 Medium |
| **Best For** | Simple tasks | Production | Small-medium apps |

---

## 🎯 Use Cases

### When to Use Background Jobs

```python
# ✅ Use async for:
- Email sending (3-5 seconds)
- File processing (images, videos)
- Report generation (heavy queries)
- External API calls (slow, unreliable)
- Database cleanup (maintenance)
- Scheduled tasks (daily, weekly)


# ❌ Don't use async for:
- Simple database queries (< 100ms)
- User authentication (must be immediate)
- Data validation (return errors immediately)
- Critical user operations (payment, booking)
```

---

## 💡 Summary

| Level | Technique |
|-------|-----------|
| **Junior** | Threading (simple, non-critical) |
| **Mid** | Celery basics (async tasks) |
| **Mid-Senior** | Task chaining, groups, retries |
| **Senior** | Periodic tasks (Celery Beat) |
| **Expert** | Monitoring, routing, Django-Q |

**Key Points:**
- ✅ Use background jobs for slow operations
- ✅ Celery for production (reliable, scalable)
- ✅ Django-Q for simple projects
- ✅ Always add retry logic
- ✅ Monitor task status
- ✅ Use task queues for organization

**Quick Start:**
```bash
# Install
pip install celery redis

# Run Redis
redis-server

# Run Celery worker
celery -A config worker --loglevel=info

# Run Celery beat (scheduled tasks)
celery -A config beat --loglevel=info
```

**Common Pattern:**
```python
# Define task
@shared_task
def my_task(arg1, arg2):
    # Do work
    return result

# Call async
my_task.delay(arg1, arg2)

# Call with options
my_task.apply_async(
    args=[arg1, arg2],
    countdown=60,  # Delay 60 seconds
    retry=True
)
```
