# 📡 SIGNALS - Django (Junior → Senior)

Dokumentasi lengkap tentang Django Signals untuk decoupled logic.

---

## 🎯 Apa itu Django Signals?

**Signals** = Event-driven mechanism untuk menjalankan code ketika suatu aksi terjadi.

```
┌──────────────┐      Signal       ┌──────────────┐
│    Sender    │ ───────────────► │   Receiver   │
│  (Model)     │   "Hey, I was    │  (Function)  │
│              │    saved!"       │              │
└──────────────┘                  └──────────────┘

Contoh:
- User created → Send welcome email
- Order saved → Update inventory
- Task deleted → Log audit trail
```

**Benefits:**
- ✅ Decoupled code (sender tidak perlu tahu receiver)
- ✅ Separation of concerns
- ✅ Multiple receivers untuk satu signal
- ✅ Easy to add/remove functionality

**Cautions:**
- ⚠️ Bisa membuat flow sulit di-trace
- ⚠️ Implicit behavior (tidak terlihat di views)
- ⚠️ Performance overhead jika terlalu banyak

---

## 1️⃣ JUNIOR LEVEL - Built-in Signals

### Model Signals

```python
# apps/tasks/signals.py
from django.db.models.signals import (
    pre_save,
    post_save,
    pre_delete,
    post_delete,
    m2m_changed
)
from django.dispatch import receiver
from .models import Task


# ──────────────────────────────────────────
# POST_SAVE - After model is saved
# ──────────────────────────────────────────
@receiver(post_save, sender=Task)
def task_post_save(sender, instance, created, **kwargs):
    """
    Triggered after Task is saved
    
    Args:
        sender: Model class (Task)
        instance: The actual Task object
        created: True if new, False if update
        **kwargs: raw, using, update_fields
    """
    if created:
        print(f"New task created: {instance.title}")
        # Send notification, create related objects, etc.
    else:
        print(f"Task updated: {instance.title}")


# ──────────────────────────────────────────
# PRE_SAVE - Before model is saved
# ──────────────────────────────────────────
@receiver(pre_save, sender=Task)
def task_pre_save(sender, instance, **kwargs):
    """
    Triggered before Task is saved
    Good for: validation, auto-fill fields
    """
    # Auto-generate slug if empty
    if not instance.slug:
        instance.slug = slugify(instance.title)
    
    # Set completed_at when status changes to DONE
    if instance.status == 'DONE' and not instance.completed_at:
        instance.completed_at = timezone.now()


# ──────────────────────────────────────────
# POST_DELETE - After model is deleted
# ──────────────────────────────────────────
@receiver(post_delete, sender=Task)
def task_post_delete(sender, instance, **kwargs):
    """
    Triggered after Task is deleted
    Good for: cleanup, audit log
    """
    print(f"Task deleted: {instance.title}")
    # Delete related files, send notification, etc.


# ──────────────────────────────────────────
# PRE_DELETE - Before model is deleted
# ──────────────────────────────────────────
@receiver(pre_delete, sender=Task)
def task_pre_delete(sender, instance, **kwargs):
    """
    Triggered before Task is deleted
    Good for: validation, backup
    """
    # Prevent deletion if task is in progress
    if instance.status == 'IN_PROGRESS':
        raise ValueError("Cannot delete task in progress!")
```

### Register Signals in apps.py

```python
# apps/tasks/apps.py
from django.apps import AppConfig


class TasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.tasks'

    def ready(self):
        # Import signals to register them
        import apps.tasks.signals  # noqa: F401
```

### Signal Arguments

| Signal | Arguments |
|--------|-----------|
| `pre_save` | sender, instance, raw, using, update_fields |
| `post_save` | sender, instance, created, raw, using, update_fields |
| `pre_delete` | sender, instance, using |
| `post_delete` | sender, instance, using |
| `m2m_changed` | sender, instance, action, reverse, model, pk_set |

---

## 2️⃣ MID LEVEL - User Signals

### User Registration Signal

```python
# apps/authentication/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from .models import Profile

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Auto-create Profile when User is created
    """
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    """
    Send welcome email to new users
    """
    if created:
        send_mail(
            subject='Welcome to TaskAPI!',
            message=f'Hi {instance.username}, thanks for joining!',
            from_email='noreply@taskapi.com',
            recipient_list=[instance.email],
            fail_silently=True,  # Don't break if email fails
        )
```

### Many-to-Many Signal

```python
# apps/tasks/signals.py
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from .models import Task


@receiver(m2m_changed, sender=Task.assignees.through)
def task_assignees_changed(sender, instance, action, pk_set, **kwargs):
    """
    Triggered when Task.assignees (M2M) is modified
    
    Actions:
        - pre_add, post_add
        - pre_remove, post_remove
        - pre_clear, post_clear
    """
    if action == 'post_add':
        # Get newly added users
        from django.contrib.auth import get_user_model
        User = get_user_model()
        new_assignees = User.objects.filter(pk__in=pk_set)
        
        for user in new_assignees:
            print(f"User {user.username} assigned to task {instance.title}")
            # Send notification to each new assignee
            
    elif action == 'post_remove':
        print(f"Users removed from task {instance.title}")
```

---

## 3️⃣ MID-SENIOR LEVEL - Custom Signals

### Define Custom Signal

```python
# apps/tasks/signals.py
from django.dispatch import Signal

# Define custom signals
task_completed = Signal()  # Args: task, completed_by
task_overdue = Signal()    # Args: task
task_assigned = Signal()   # Args: task, assignee, assigned_by


# ──────────────────────────────────────────
# Signal receivers
# ──────────────────────────────────────────
from django.dispatch import receiver

@receiver(task_completed)
def handle_task_completed(sender, task, completed_by, **kwargs):
    """
    Handle task completion
    """
    print(f"Task '{task.title}' completed by {completed_by.username}")
    
    # Update statistics
    from apps.core.models import Statistics
    Statistics.objects.increment_completed(completed_by)
    
    # Notify task creator
    if task.created_by != completed_by:
        send_notification(
            user=task.created_by,
            message=f"Your task '{task.title}' has been completed"
        )


@receiver(task_assigned)
def handle_task_assigned(sender, task, assignee, assigned_by, **kwargs):
    """
    Handle new task assignment
    """
    send_notification(
        user=assignee,
        message=f"You've been assigned to task '{task.title}'"
    )
```

### Send Custom Signal

```python
# apps/tasks/services.py
from .signals import task_completed, task_assigned


class TaskService:
    @staticmethod
    def complete_task(task, user):
        """
        Complete a task and emit signal
        """
        task.status = 'DONE'
        task.completed_at = timezone.now()
        task.completed_by = user
        task.save()
        
        # Emit custom signal
        task_completed.send(
            sender=TaskService,
            task=task,
            completed_by=user
        )
        
        return task
    
    @staticmethod
    def assign_task(task, assignee, assigned_by):
        """
        Assign task to user and emit signal
        """
        task.assignees.add(assignee)
        
        # Emit custom signal
        task_assigned.send(
            sender=TaskService,
            task=task,
            assignee=assignee,
            assigned_by=assigned_by
        )
        
        return task
```

---

## 4️⃣ SENIOR LEVEL - Advanced Patterns

### Audit Trail with Signals

```python
# apps/core/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from .models import AuditLog


def create_audit_receiver(model_class):
    """
    Factory function to create audit receivers for any model
    """
    
    @receiver(post_save, sender=model_class)
    def audit_save(sender, instance, created, **kwargs):
        action = 'CREATE' if created else 'UPDATE'
        
        AuditLog.objects.create(
            content_type=ContentType.objects.get_for_model(sender),
            object_id=instance.pk,
            action=action,
            user=getattr(instance, '_current_user', None),
            data=serialize_instance(instance)
        )
    
    @receiver(post_delete, sender=model_class)
    def audit_delete(sender, instance, **kwargs):
        AuditLog.objects.create(
            content_type=ContentType.objects.get_for_model(sender),
            object_id=instance.pk,
            action='DELETE',
            user=getattr(instance, '_current_user', None),
            data=serialize_instance(instance)
        )
    
    return audit_save, audit_delete


# Register for multiple models
from apps.tasks.models import Task, Project
from apps.authentication.models import Profile

for model in [Task, Project, Profile]:
    create_audit_receiver(model)
```

### Middleware to Pass Current User

```python
# apps/core/middleware.py
from threading import local

_user = local()


class CurrentUserMiddleware:
    """
    Middleware to make current user available in signals
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        _user.value = request.user if request.user.is_authenticated else None
        response = self.get_response(request)
        return response


def get_current_user():
    """
    Get current user from thread local
    """
    return getattr(_user, 'value', None)


# Usage in signal
@receiver(post_save, sender=Task)
def audit_task(sender, instance, created, **kwargs):
    user = get_current_user()
    # Now you have the current user in signal!
```

### Signal with Transaction

```python
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=Task)
def handle_task_save(sender, instance, created, **kwargs):
    """
    Run signal handler after transaction commits
    """
    def on_commit():
        # This runs AFTER the transaction is committed
        # Safe for external API calls, emails, etc.
        send_notification(instance)
        update_search_index(instance)
    
    transaction.on_commit(on_commit)
```

### Disable Signals Temporarily

```python
# apps/core/utils.py
from contextlib import contextmanager
from django.db.models.signals import post_save, pre_save


@contextmanager
def disable_signals(signal, sender):
    """
    Context manager to temporarily disable a signal
    """
    receivers = signal.receivers
    signal.receivers = []
    
    try:
        yield
    finally:
        signal.receivers = receivers


# Usage
from apps.tasks.models import Task

with disable_signals(post_save, Task):
    # Signals won't fire here
    Task.objects.bulk_create([
        Task(title='Task 1'),
        Task(title='Task 2'),
    ])
```

---

## 5️⃣ EXPERT LEVEL - Signal Best Practices

### Async Signal Handler

```python
# apps/tasks/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Task


@receiver(post_save, sender=Task)
def handle_task_save(sender, instance, created, **kwargs):
    """
    Trigger async task from signal
    """
    if created:
        # Don't do heavy work in signal!
        # Delegate to Celery task
        from .tasks import process_new_task
        
        transaction.on_commit(lambda: process_new_task.delay(instance.id))
```

```python
# apps/tasks/tasks.py
from celery import shared_task


@shared_task
def process_new_task(task_id):
    """
    Heavy processing in background
    """
    task = Task.objects.get(id=task_id)
    
    # Do heavy work here
    send_email(task)
    update_analytics(task)
    sync_external_system(task)
```

### Testing Signals

```python
# apps/tasks/tests/test_signals.py
from django.test import TestCase
from django.db.models.signals import post_save
from unittest.mock import patch
from apps.tasks.models import Task
from apps.tasks.signals import task_post_save


class SignalTestCase(TestCase):
    
    @patch('apps.tasks.signals.send_notification')
    def test_task_created_sends_notification(self, mock_send):
        """
        Test that creating a task sends notification
        """
        task = Task.objects.create(title='Test Task')
        
        mock_send.assert_called_once()
    
    def test_task_created_without_signal(self):
        """
        Test model creation without triggering signals
        """
        # Disconnect signal
        post_save.disconnect(task_post_save, sender=Task)
        
        try:
            task = Task.objects.create(title='Test')
            # Signal not called
        finally:
            # Reconnect signal
            post_save.connect(task_post_save, sender=Task)
    
    @patch('apps.tasks.signals.task_completed')
    def test_custom_signal_emitted(self, mock_signal):
        """
        Test that custom signal is emitted
        """
        from apps.tasks.services import TaskService
        
        task = Task.objects.create(title='Test')
        user = User.objects.create(username='testuser')
        
        TaskService.complete_task(task, user)
        
        mock_signal.send.assert_called_once()
```

---

## 📊 Signal Quick Reference

### Built-in Model Signals

| Signal | Timing | Use Case |
|--------|--------|----------|
| `pre_save` | Before save | Validation, auto-fill fields |
| `post_save` | After save | Notifications, create related objects |
| `pre_delete` | Before delete | Validation, backup |
| `post_delete` | After delete | Cleanup, audit log |
| `m2m_changed` | M2M modified | Sync, notifications |
| `pre_init` | Before `__init__` | Rarely used |
| `post_init` | After `__init__` | Set default values |

### Built-in Request Signals

| Signal | Timing |
|--------|--------|
| `request_started` | Before request processing |
| `request_finished` | After response sent |
| `got_request_exception` | Exception during request |

### Signals vs Alternatives

| Approach | Use When |
|----------|----------|
| **Signals** | Decoupled, multiple receivers, cross-app |
| **Model.save()** | Logic tightly coupled to model |
| **Service Layer** | Complex business logic, explicit flow |
| **Celery Tasks** | Heavy/async processing |

---

## 💡 Summary

| Level | Focus |
|-------|-------|
| **Junior** | post_save, post_delete basics |
| **Mid** | User signals, M2M signals |
| **Mid-Senior** | Custom signals, signal factories |
| **Senior** | Transaction handling, disable signals |
| **Expert** | Async signals, testing strategies |

**Best Practices:**
- ✅ Keep signal handlers lightweight
- ✅ Use transaction.on_commit for external calls
- ✅ Use Celery for heavy work
- ✅ Document what signals do
- ✅ Test signals properly
- ❌ Don't use signals for critical business logic
- ❌ Don't create circular dependencies
- ❌ Don't overuse signals (makes code hard to trace)
