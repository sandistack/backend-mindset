# 🏗️ ARCHITECTURE - Django (Junior → Senior)

Dokumentasi lengkap tentang arsitektur aplikasi Django dari struktur dasar hingga design patterns.

---

## 🎯 Kenapa Perlu Arsitektur yang Baik?

**Without Architecture:**
```
❌ Code tanpa struktur
❌ Logic campur di views
❌ Sulit maintenance
❌ Susah testing
❌ Team bingung
```

**With Good Architecture:**
```
✅ Code terorganisir
✅ Separation of concerns
✅ Mudah maintenance
✅ Testable
✅ Team collaboration smooth
```

---

## 1️⃣ JUNIOR LEVEL - MVT Pattern (Django Default)

### Konsep Dasar MVT

Django menggunakan **MVT (Model-View-Template)** pattern:

```
Request → URL Router → View → Model (Database)
                        ↓
                    Template (HTML)
                        ↓
                    Response
```

### Struktur Dasar

```python
# models.py - Data layer
from django.db import models

class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)


# views.py - Business logic
from django.shortcuts import render
from .models import Task

def task_list(request):
    tasks = Task.objects.all()
    return render(request, 'tasks.html', {'tasks': tasks})


# urls.py - Routing
from django.urls import path
from . import views

urlpatterns = [
    path('tasks/', views.task_list, name='task_list'),
]
```

**Problem dengan pendekatan ini:**
- ❌ Business logic campur di views
- ❌ Susah testing
- ❌ Code duplication
- ❌ Sulit scale untuk project besar

---

## 2️⃣ MID LEVEL - Layered Architecture

### 3-Layer Pattern

```
┌─────────────────────────────────────┐
│  Presentation Layer (Views/API)    │  ← User interaction
├─────────────────────────────────────┤
│  Business Logic Layer (Services)   │  ← Core logic
├─────────────────────────────────────┤
│  Data Access Layer (Models/ORM)    │  ← Database
└─────────────────────────────────────┘
```

### Implementasi

#### Layer 1: Models (Data Access)

```python
# apps/tasks/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Task(models.Model):
    STATUS_CHOICES = [
        ('TODO', 'To Do'),
        ('IN_PROGRESS', 'In Progress'),
        ('DONE', 'Done'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='TODO')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
```

#### Layer 2: Services (Business Logic)

```python
# apps/tasks/services.py
from django.db import transaction
from .models import Task

class TaskService:
    """
    Business logic untuk Task
    """
    
    @staticmethod
    def create_task(user, title, description='', status='TODO'):
        """
        Create task dengan validation
        """
        # Business rules
        if len(title) < 3:
            raise ValueError("Title must be at least 3 characters")
        
        # Create task
        task = Task.objects.create(
            user=user,
            title=title,
            description=description,
            status=status
        )
        
        # Business logic lainnya (send notification, log, etc)
        # ...
        
        return task
    
    @staticmethod
    def update_task_status(task_id, new_status):
        """
        Update task status dengan validation
        """
        task = Task.objects.get(id=task_id)
        
        # Business rules: tidak bisa dari DONE ke TODO
        if task.status == 'DONE' and new_status == 'TODO':
            raise ValueError("Cannot revert completed task to TODO")
        
        task.status = new_status
        task.save()
        
        return task
    
    @staticmethod
    def get_user_tasks(user, status=None):
        """
        Get tasks dengan filtering
        """
        tasks = Task.objects.filter(user=user)
        
        if status:
            tasks = tasks.filter(status=status)
        
        return tasks
    
    @staticmethod
    @transaction.atomic
    def bulk_update_status(task_ids, new_status):
        """
        Bulk update dengan transaction
        """
        tasks = Task.objects.filter(id__in=task_ids)
        tasks.update(status=new_status)
        
        return tasks.count()
```

#### Layer 3: Views/API (Presentation)

```python
# apps/tasks/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .services import TaskService
from .serializers import TaskSerializer

class TaskListCreateView(APIView):
    """
    View hanya handle HTTP request/response
    Business logic di service layer
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Get dari service
        tasks = TaskService.get_user_tasks(request.user)
        serializer = TaskSerializer(tasks, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def post(self, request):
        serializer = TaskSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Business logic di service
            task = TaskService.create_task(
                user=request.user,
                **serializer.validated_data
            )
            
            return Response({
                'success': True,
                'data': TaskSerializer(task).data
            }, status=status.HTTP_201_CREATED)
        
        except ValueError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
```

---

## 3️⃣ MID-SENIOR LEVEL - Design Patterns

### A) Repository Pattern

**Problem:** Direct model access di service, sulit mock untuk testing.

**Solution:** Repository sebagai abstraction layer.

```python
# apps/tasks/repositories.py
from typing import List, Optional
from .models import Task

class TaskRepository:
    """
    Abstraction layer untuk data access
    """
    
    @staticmethod
    def get_by_id(task_id: int) -> Optional[Task]:
        try:
            return Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return None
    
    @staticmethod
    def get_by_user(user, status: Optional[str] = None) -> List[Task]:
        queryset = Task.objects.filter(user=user)
        
        if status:
            queryset = queryset.filter(status=status)
        
        return list(queryset)
    
    @staticmethod
    def create(user, title: str, description: str = '', status: str = 'TODO') -> Task:
        return Task.objects.create(
            user=user,
            title=title,
            description=description,
            status=status
        )
    
    @staticmethod
    def update(task: Task, **kwargs) -> Task:
        for key, value in kwargs.items():
            setattr(task, key, value)
        task.save()
        return task
    
    @staticmethod
    def delete(task: Task) -> None:
        task.delete()


# Refactored service menggunakan repository
class TaskService:
    
    def __init__(self, repository=None):
        self.repository = repository or TaskRepository()
    
    def create_task(self, user, title, description='', status='TODO'):
        # Validation
        if len(title) < 3:
            raise ValueError("Title must be at least 3 characters")
        
        # Use repository
        task = self.repository.create(
            user=user,
            title=title,
            description=description,
            status=status
        )
        
        return task
    
    def get_user_tasks(self, user, status=None):
        return self.repository.get_by_user(user, status)
```

**Benefits:**
- ✅ Testable (bisa mock repository)
- ✅ Reusable queries
- ✅ Single responsibility

---

### B) Factory Pattern

**Problem:** Complex object creation.

```python
# apps/tasks/factories.py
from .models import Task
from django.contrib.auth import get_user_model

User = get_user_model()

class TaskFactory:
    """
    Factory untuk create object dengan default values
    """
    
    @staticmethod
    def create_todo_task(user, title, description=''):
        return Task.objects.create(
            user=user,
            title=title,
            description=description,
            status='TODO'
        )
    
    @staticmethod
    def create_urgent_task(user, title, description=''):
        """
        Urgent task langsung IN_PROGRESS
        """
        task = Task.objects.create(
            user=user,
            title=f"[URGENT] {title}",
            description=description,
            status='IN_PROGRESS'
        )
        
        # Send notification
        # ...
        
        return task
    
    @staticmethod
    def create_from_template(user, template_name):
        """
        Create task dari template
        """
        templates = {
            'daily_standup': {
                'title': 'Daily Standup',
                'description': 'Team daily standup meeting'
            },
            'code_review': {
                'title': 'Code Review',
                'description': 'Review pending pull requests'
            }
        }
        
        template = templates.get(template_name)
        
        if not template:
            raise ValueError(f"Template {template_name} not found")
        
        return Task.objects.create(
            user=user,
            **template,
            status='TODO'
        )
```

---

### C) Strategy Pattern

**Problem:** Different behavior based on context.

```python
# apps/tasks/strategies.py
from abc import ABC, abstractmethod

class TaskNotificationStrategy(ABC):
    """
    Abstract strategy untuk notification
    """
    
    @abstractmethod
    def send(self, task, message):
        pass


class EmailNotificationStrategy(TaskNotificationStrategy):
    def send(self, task, message):
        # Send email
        from django.core.mail import send_mail
        
        send_mail(
            subject=f'Task Update: {task.title}',
            message=message,
            from_email='noreply@example.com',
            recipient_list=[task.user.email],
        )


class PushNotificationStrategy(TaskNotificationStrategy):
    def send(self, task, message):
        # Send push notification
        # ...
        pass


class SlackNotificationStrategy(TaskNotificationStrategy):
    def send(self, task, message):
        # Send to Slack
        # ...
        pass


# Usage in service
class TaskService:
    
    def __init__(self, notification_strategy=None):
        self.notification_strategy = notification_strategy or EmailNotificationStrategy()
    
    def complete_task(self, task_id):
        task = Task.objects.get(id=task_id)
        task.status = 'DONE'
        task.save()
        
        # Notify using strategy
        self.notification_strategy.send(
            task,
            f"Task '{task.title}' has been completed!"
        )
        
        return task


# Different strategies for different users
# VIP user gets Slack notification
service = TaskService(notification_strategy=SlackNotificationStrategy())
service.complete_task(123)

# Regular user gets email
service = TaskService(notification_strategy=EmailNotificationStrategy())
service.complete_task(456)
```

---

## 4️⃣ SENIOR LEVEL - Project Structure

### Recommended Structure

```
project/
├── config/                      # Project settings
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
│
├── apps/                        # Applications
│   ├── core/                    # Shared utilities
│   │   ├── exceptions.py        # Custom exceptions
│   │   ├── permissions.py       # Reusable permissions
│   │   ├── pagination.py        # Custom pagination
│   │   └── utils/
│   │       ├── decorators.py
│   │       ├── validators.py
│   │       └── helpers.py
│   │
│   ├── authentication/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── services.py          # Business logic
│   │   ├── repositories.py      # Data access
│   │   ├── views.py             # API endpoints
│   │   ├── urls.py
│   │   └── tests/
│   │       ├── test_models.py
│   │       ├── test_services.py
│   │       └── test_views.py
│   │
│   └── tasks/
│       ├── models.py
│       ├── serializers.py
│       ├── services.py
│       ├── repositories.py
│       ├── factories.py         # Object creation
│       ├── strategies.py        # Strategy patterns
│       ├── views.py
│       ├── urls.py
│       └── tests/
│
├── tests/                       # Integration tests
│   └── integration/
│
├── docs/                        # Documentation
├── logs/                        # Log files
└── manage.py
```

---

## 5️⃣ SENIOR LEVEL - Domain-Driven Design (DDD)

### Konsep DDD

```
Domain Layer (Core Business Logic)
    ├── Entities (Business objects)
    ├── Value Objects (Immutable objects)
    ├── Aggregates (Cluster of entities)
    └── Domain Services (Business operations)

Application Layer (Use Cases)
    └── Application Services (Orchestrate domain)

Infrastructure Layer (Technical details)
    ├── Repositories (Data persistence)
    └── External Services (API, Email, etc)

Presentation Layer (User Interface)
    └── Views/API (HTTP handlers)
```

### Implementasi

```python
# Domain Layer
# apps/tasks/domain/entities.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Task:
    """
    Domain entity (pure business object)
    """
    id: Optional[int]
    title: str
    description: str
    status: str
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    def complete(self):
        """Domain logic"""
        if self.status == 'DONE':
            raise ValueError("Task already completed")
        
        self.status = 'DONE'
        self.updated_at = datetime.now()
    
    def reopen(self):
        """Domain logic"""
        if self.status != 'DONE':
            raise ValueError("Only completed tasks can be reopened")
        
        self.status = 'TODO'
        self.updated_at = datetime.now()


# Application Layer
# apps/tasks/application/services.py
class TaskApplicationService:
    """
    Application service (orchestrate domain)
    """
    
    def __init__(self, task_repository):
        self.task_repository = task_repository
    
    def complete_task(self, task_id: int, user_id: int):
        """
        Use case: Complete a task
        """
        # Get from repository
        task = self.task_repository.get_by_id(task_id)
        
        if not task:
            raise ValueError("Task not found")
        
        # Authorization
        if task.user_id != user_id:
            raise PermissionError("Not authorized")
        
        # Domain logic
        task.complete()
        
        # Save
        self.task_repository.save(task)
        
        return task
```

---

## 6️⃣ EXPERT LEVEL - CQRS Pattern

### Command Query Responsibility Segregation

**Konsep:** Pisahkan operasi **Write (Command)** dan **Read (Query)**.

```python
# Commands (Write operations)
# apps/tasks/commands/create_task.py
from dataclasses import dataclass

@dataclass
class CreateTaskCommand:
    user_id: int
    title: str
    description: str
    status: str = 'TODO'


class CreateTaskCommandHandler:
    """
    Handle command untuk create task
    """
    
    def __init__(self, repository):
        self.repository = repository
    
    def handle(self, command: CreateTaskCommand):
        # Validation
        if len(command.title) < 3:
            raise ValueError("Title too short")
        
        # Create
        task = self.repository.create(
            user_id=command.user_id,
            title=command.title,
            description=command.description,
            status=command.status
        )
        
        # Publish event (optional)
        # event_bus.publish(TaskCreatedEvent(task.id))
        
        return task


# Queries (Read operations)
# apps/tasks/queries/get_user_tasks.py
@dataclass
class GetUserTasksQuery:
    user_id: int
    status: Optional[str] = None


class GetUserTasksQueryHandler:
    """
    Handle query untuk get tasks
    """
    
    def __init__(self, repository):
        self.repository = repository
    
    def handle(self, query: GetUserTasksQuery):
        return self.repository.get_by_user(
            user_id=query.user_id,
            status=query.status
        )


# Usage in views
from .commands.create_task import CreateTaskCommand, CreateTaskCommandHandler
from .queries.get_user_tasks import GetUserTasksQuery, GetUserTasksQueryHandler

class TaskView(APIView):
    
    def post(self, request):
        # Command
        command = CreateTaskCommand(
            user_id=request.user.id,
            title=request.data['title'],
            description=request.data.get('description', ''),
        )
        
        handler = CreateTaskCommandHandler(repository=TaskRepository())
        task = handler.handle(command)
        
        return Response({'data': task})
    
    def get(self, request):
        # Query
        query = GetUserTasksQuery(
            user_id=request.user.id,
            status=request.query_params.get('status')
        )
        
        handler = GetUserTasksQueryHandler(repository=TaskRepository())
        tasks = handler.handle(query)
        
        return Response({'data': tasks})
```

**Benefits:**
- ✅ Separate read/write optimization
- ✅ Clear responsibility
- ✅ Scalable (different databases for read/write)

---

## 7️⃣ EXPERT LEVEL - Event-Driven Architecture

```python
# Event system
# apps/core/events.py
from typing import Callable, Dict, List

class EventBus:
    """
    Simple event bus untuk publish/subscribe
    """
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event_type: str, handler: Callable):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        self._subscribers[event_type].append(handler)
    
    def publish(self, event):
        event_type = event.__class__.__name__
        
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                handler(event)


# Global event bus
event_bus = EventBus()


# Domain events
# apps/tasks/events.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TaskCreated:
    task_id: int
    user_id: int
    title: str
    created_at: datetime


@dataclass
class TaskCompleted:
    task_id: int
    user_id: int
    completed_at: datetime


# Event handlers
# apps/tasks/event_handlers.py
def send_task_created_email(event: TaskCreated):
    """Handler untuk TaskCreated event"""
    from django.core.mail import send_mail
    
    send_mail(
        subject=f'New Task Created: {event.title}',
        message=f'Your task "{event.title}" has been created',
        from_email='noreply@example.com',
        recipient_list=['user@example.com'],
    )


def log_task_completed(event: TaskCompleted):
    """Handler untuk TaskCompleted event"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Task {event.task_id} completed by user {event.user_id}")


# Register event handlers
from apps.core.events import event_bus

event_bus.subscribe('TaskCreated', send_task_created_email)
event_bus.subscribe('TaskCompleted', log_task_completed)


# Service publishes events
class TaskService:
    
    def create_task(self, user, title, description):
        task = Task.objects.create(
            user=user,
            title=title,
            description=description
        )
        
        # Publish event
        event_bus.publish(TaskCreated(
            task_id=task.id,
            user_id=user.id,
            title=task.title,
            created_at=task.created_at
        ))
        
        return task
```

---

## 📊 Architecture Comparison

| Pattern | Complexity | Use Case | Project Size |
|---------|-----------|----------|--------------|
| **MVT** | 🟢 Simple | Simple CRUD | Small |
| **Layered (3-tier)** | 🟡 Medium | Most projects | Small-Medium |
| **Repository** | 🟡 Medium | Need testability | Medium |
| **DDD** | 🔴 Complex | Complex domain | Large |
| **CQRS** | 🔴 Complex | High read/write load | Large |
| **Event-Driven** | 🔴 Complex | Microservices, async | Enterprise |

---

## 🎯 Best Practices

### 1. Start Simple, Evolve

```python
# ✅ Junior project: MVT is fine
def task_list(request):
    tasks = Task.objects.all()
    return render(request, 'tasks.html', {'tasks': tasks})


# ✅ Mid project: Add service layer
class TaskService:
    @staticmethod
    def get_all_tasks():
        return Task.objects.all()


# ✅ Senior project: Add repository + patterns
class TaskRepository:
    def get_all(self):
        return Task.objects.all()

class TaskService:
    def __init__(self, repo):
        self.repo = repo
```

### 2. Separation of Concerns

```python
# ❌ Bad: Everything in views
def create_task(request):
    # Validation
    if len(request.POST['title']) < 3:
        return JsonResponse({'error': 'Too short'})
    
    # Business logic
    task = Task.objects.create(...)
    
    # Send email
    send_mail(...)
    
    # Log
    logger.info(...)
    
    return JsonResponse({'success': True})


# ✅ Good: Separate responsibilities
def create_task(request):
    serializer = TaskSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    task = TaskService.create_task(
        user=request.user,
        **serializer.validated_data
    )
    
    return Response({'data': TaskSerializer(task).data})
```

### 3. Keep It DRY

```python
# ❌ Bad: Duplicate logic
def view1(request):
    if not request.user.is_authenticated:
        return Response({'error': 'Unauthorized'})
    # ...

def view2(request):
    if not request.user.is_authenticated:
        return Response({'error': 'Unauthorized'})
    # ...


# ✅ Good: Reusable components
from rest_framework.permissions import IsAuthenticated

class TaskView(APIView):
    permission_classes = [IsAuthenticated]  # Reusable
```

---

## 💡 Summary

| Level | Architecture |
|-------|-------------|
| **Junior** | MVT (Model-View-Template) |
| **Mid** | Layered (3-tier) + Service layer |
| **Mid-Senior** | Repository + Factory patterns |
| **Senior** | DDD, proper project structure |
| **Expert** | CQRS, Event-Driven Architecture |

**Key Takeaways:**
- ✅ **Junior:** Focus on Django basics (MVT)
- ✅ **Mid:** Add service layer untuk business logic
- ✅ **Senior:** Use design patterns (Repository, Factory, Strategy)
- ✅ **Expert:** Advanced patterns (DDD, CQRS, Event-Driven)

**Golden Rule:**
> "Start simple, add complexity only when needed" 

**Recommended Path:**
1. Start: MVT ✅
2. Grow: Add Service Layer ✅
3. Mature: Add Repository Pattern ✅
4. Scale: Consider DDD/CQRS ✅
