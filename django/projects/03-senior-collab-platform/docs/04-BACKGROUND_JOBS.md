# ⚙️ Step 4: Background Jobs

**Waktu:** 4-6 jam  
**Prerequisite:** Step 3 selesai

---

## 🎯 Tujuan

- Celery advanced patterns
- Task chaining & groups
- Scheduled tasks (Celery Beat)
- Error handling & retries
- Monitoring

---

## 📋 Tasks

### 4.1 Task Organization

**Buat `apps/core/tasks.py`:**

```python
from celery import shared_task, chain, group, chord
from config.celery import app

class BaseTask(app.Task):
    """Base task with error handling"""
    
    autoretry_for = (Exception,)
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes max
    retry_kwargs = {'max_retries': 3}
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Log task failure"""
        import logging
        logger = logging.getLogger('celery.tasks')
        logger.error(f"Task {self.name} failed: {exc}")
        
        # Optional: Send alert
        # send_alert_to_slack(f"Task {self.name} failed: {exc}")
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Log retry attempt"""
        import logging
        logger = logging.getLogger('celery.tasks')
        logger.warning(f"Task {self.name} retrying: {exc}")
```

### 4.2 Notification Tasks

**Buat `apps/notifications/tasks.py`:**

```python
from celery import shared_task
from apps.core.tasks import BaseTask
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@shared_task(base=BaseTask, bind=True)
def send_notification(self, user_id, notification_type, data):
    """Send notification to user"""
    from .models import Notification
    from .serializers import NotificationSerializer
    
    # Create notification in database
    notification = Notification.objects.create(
        user_id=user_id,
        type=notification_type,
        data=data
    )
    
    # Send real-time via WebSocket
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'notifications_{user_id}',
        {
            'type': 'notification',
            'data': NotificationSerializer(notification).data
        }
    )
    
    return notification.id


@shared_task(base=BaseTask)
def send_batch_notifications(user_ids, notification_type, data):
    """Send notification to multiple users"""
    from celery import group
    
    # Create a group of tasks
    job = group([
        send_notification.s(user_id, notification_type, data)
        for user_id in user_ids
    ])
    
    return job.apply_async()


@shared_task(base=BaseTask)
def send_push_notification(user_id, title, body, data=None):
    """Send push notification (FCM/APNs)"""
    from .services import PushNotificationService
    
    service = PushNotificationService()
    service.send(user_id, title, body, data)
```

**Referensi:** [BACKGROUND_JOBS.md](../../../docs/04-advanced/BACKGROUND_JOBS.md)

### 4.3 Document Tasks

**Buat `apps/documents/tasks.py`:**

```python
from celery import shared_task, chain
from apps.core.tasks import BaseTask

@shared_task(base=BaseTask)
def process_document_version(document_id, user_id):
    """Create document version snapshot"""
    from .models import Document, DocumentVersion
    
    document = Document.objects.get(id=document_id)
    
    DocumentVersion.objects.create(
        document=document,
        content=document.content,
        version=document.version,
        created_by_id=user_id
    )


@shared_task(base=BaseTask)
def index_document(document_id):
    """Index document for search"""
    from .models import Document
    from apps.search.services import SearchService
    
    document = Document.objects.get(id=document_id)
    SearchService.index_document(document)


@shared_task(base=BaseTask)
def cleanup_old_versions(document_id, keep_count=50):
    """Keep only last N versions"""
    from .models import DocumentVersion
    
    versions = DocumentVersion.objects.filter(
        document_id=document_id
    ).order_by('-created_at')
    
    # Get IDs to keep
    keep_ids = list(versions[:keep_count].values_list('id', flat=True))
    
    # Delete older versions
    DocumentVersion.objects.filter(
        document_id=document_id
    ).exclude(id__in=keep_ids).delete()


# Chain example: Process document update
def on_document_saved(document_id, user_id):
    """Chain of tasks after document save"""
    chain(
        process_document_version.s(document_id, user_id),
        index_document.s(document_id),
    ).apply_async()
```

### 4.4 Activity & Analytics Tasks

**Buat `apps/activity/tasks.py`:**

```python
from celery import shared_task
from apps.core.tasks import BaseTask

@shared_task(base=BaseTask)
def log_activity(workspace_id, user_id, action, target_type, target_id, metadata=None):
    """Log user activity"""
    from .models import Activity
    
    Activity.objects.create(
        workspace_id=workspace_id,
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        metadata=metadata or {}
    )


@shared_task(base=BaseTask)
def generate_daily_digest(workspace_id):
    """Generate daily activity digest"""
    from datetime import datetime, timedelta
    from .models import Activity
    from apps.notifications.tasks import send_batch_notifications
    from apps.workspaces.models import Member
    
    yesterday = datetime.now() - timedelta(days=1)
    
    activities = Activity.objects.filter(
        workspace_id=workspace_id,
        created_at__gte=yesterday
    ).select_related('user')
    
    if not activities.exists():
        return
    
    # Create digest
    digest = {
        'date': yesterday.strftime('%Y-%m-%d'),
        'activity_count': activities.count(),
        'top_contributors': list(
            activities.values('user__name').annotate(
                count=models.Count('id')
            ).order_by('-count')[:5]
        )
    }
    
    # Send to all members
    member_ids = list(Member.objects.filter(
        workspace_id=workspace_id
    ).values_list('user_id', flat=True))
    
    send_batch_notifications.delay(
        member_ids,
        'daily_digest',
        digest
    )
```

### 4.5 Scheduled Tasks (Celery Beat)

**Update `config/celery.py`:**

```python
from celery import Celery
from celery.schedules import crontab
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('collab_platform')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Scheduled tasks
app.conf.beat_schedule = {
    # Every day at 8 AM
    'generate-daily-digests': {
        'task': 'apps.activity.tasks.generate_all_digests',
        'schedule': crontab(hour=8, minute=0),
    },
    
    # Every hour
    'cleanup-expired-invites': {
        'task': 'apps.workspaces.tasks.cleanup_expired_invites',
        'schedule': crontab(minute=0),
    },
    
    # Every 5 minutes
    'sync-online-status': {
        'task': 'apps.core.tasks.sync_online_status',
        'schedule': 300.0,  # 5 minutes in seconds
    },
    
    # Every Sunday at midnight
    'cleanup-old-versions': {
        'task': 'apps.documents.tasks.cleanup_all_old_versions',
        'schedule': crontab(hour=0, minute=0, day_of_week=0),
    },
    
    # Every night at 2 AM
    'reindex-search': {
        'task': 'apps.search.tasks.full_reindex',
        'schedule': crontab(hour=2, minute=0),
    },
}
```

### 4.6 Task Chaining & Groups

```python
from celery import chain, group, chord

# Chain: Sequential execution
chain(
    task1.s(arg1),
    task2.s(),  # Result of task1 passed as first arg
    task3.s()
).apply_async()

# Group: Parallel execution
group([
    task1.s(item) for item in items
]).apply_async()

# Chord: Group + callback when all complete
chord(
    [task1.s(item) for item in items],
    callback_task.s()
).apply_async()


# Practical example: Process workspace export
@shared_task
def export_workspace(workspace_id):
    """Export all workspace data"""
    from celery import chord
    
    workspace = Workspace.objects.get(id=workspace_id)
    
    # Export each type in parallel, then combine
    chord(
        [
            export_documents.s(workspace_id),
            export_channels.s(workspace_id),
            export_files.s(workspace_id),
        ],
        combine_exports.s(workspace_id)
    ).apply_async()
```

### 4.7 Task Monitoring

**Add task events logging:**

```python
from celery.signals import task_prerun, task_postrun, task_failure
import logging

logger = logging.getLogger('celery.tasks')

@task_prerun.connect
def task_started(task_id, task, args, kwargs, **other):
    logger.info(f"Task {task.name}[{task_id}] started")


@task_postrun.connect
def task_completed(task_id, task, args, kwargs, retval, **other):
    logger.info(f"Task {task.name}[{task_id}] completed")


@task_failure.connect
def task_failed(task_id, exception, traceback, **other):
    logger.error(f"Task [{task_id}] failed: {exception}")
```

---

## ✅ Checklist

- [ ] BaseTask with error handling
- [ ] Notification tasks (single & batch)
- [ ] Document processing tasks
- [ ] Activity logging tasks
- [ ] Celery Beat scheduled tasks
- [ ] Task chaining & groups
- [ ] Task monitoring signals
- [ ] Retry configuration

---

## 🔗 Referensi

- [BACKGROUND_JOBS.md](../../../docs/04-advanced/BACKGROUND_JOBS.md) - Complete guide

---

## ➡️ Next Step

Lanjut ke [05-NOTIFICATION_SYSTEM.md](05-NOTIFICATION_SYSTEM.md) - Notification System
