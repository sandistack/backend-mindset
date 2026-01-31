# 👥 GROUPS & PERMISSIONS - Django (Junior → Senior)

Dokumentasi lengkap tentang Django Groups, Permissions, dan Role-Based Access Control.

---

## 🎯 Authentication vs Authorization

| Konsep | Pertanyaan | Contoh |
|--------|-----------|--------|
| **Authentication** | Siapa kamu? | Login dengan email & password |
| **Authorization** | Apa yang boleh kamu lakukan? | User bisa edit own data, Admin bisa edit all data |

---

## 🔐 Permission Levels

| Level | Complexity | Use Case |
|-------|-----------|----------|
| **Simple Role** (USER, ADMIN) | Low | Small apps, 1-3 roles |
| **Django Groups** | Medium | Medium apps, multiple roles |
| **Custom RBAC** | High | Enterprise, complex permissions |

---

## 1️⃣ JUNIOR LEVEL - Simple Role (Boolean Field)

### Model

```python
# apps/authentication/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True)
    is_admin = models.BooleanField(default=False)  # Simple role
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.email
```

### Permission Check in Views

```python
# apps/tasks/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class TaskListView(APIView):
    def get(self, request):
        # User: own tasks only
        if request.user.is_admin:
            tasks = Task.objects.all()
        else:
            tasks = Task.objects.filter(user=request.user)
        
        serializer = TaskSerializer(tasks, many=True)
        return Response({"data": serializer.data})


class TaskDetailView(APIView):
    def delete(self, request, pk):
        task = Task.objects.get(pk=pk)
        
        # Only owner or admin can delete
        if task.user != request.user and not request.user.is_admin:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        task.delete()
        return Response({"message": "Task deleted"})
```

**Pros:**
- ✅ Simple & straightforward
- ✅ Easy to understand

**Cons:**
- ❌ Not scalable (add more roles = more boolean fields)
- ❌ Permission logic scattered di views

---

## 2️⃣ MID LEVEL - Django Built-in Permissions

Django otomatis create 4 permissions untuk setiap model:
- `add_<model>` → Create
- `view_<model>` → Read
- `change_<model>` → Update
- `delete_<model>` → Delete

### Check Permissions

```python
# apps/tasks/views.py
from rest_framework.permissions import BasePermission

class CanDeleteTask(BasePermission):
    """
    Only task owner or users with delete_task permission
    """
    def has_object_permission(self, request, view, obj):
        # Owner always can delete
        if obj.user == request.user:
            return True
        
        # Check Django permission
        return request.user.has_perm('tasks.delete_task')


class TaskDetailView(APIView):
    permission_classes = [CanDeleteTask]
    
    def delete(self, request, pk):
        task = Task.objects.get(pk=pk)
        self.check_object_permissions(request, task)
        
        task.delete()
        return Response({"message": "Task deleted"})
```

### Assign Permission di Admin

```python
# Django Admin atau Shell
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

User = get_user_model()

user = User.objects.get(email='john@example.com')
permission = Permission.objects.get(codename='delete_task')

user.user_permissions.add(permission)
```

---

## 3️⃣ MID-SENIOR LEVEL - Django Groups

Groups = Collection of permissions.

### Create Groups (Migration)

```python
# apps/authentication/migrations/0002_create_groups.py
from django.db import migrations

def create_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    
    # Create Groups
    user_group = Group.objects.create(name='User')
    admin_group = Group.objects.create(name='Admin')
    moderator_group = Group.objects.create(name='Moderator')
    
    # User permissions (own tasks only)
    user_permissions = Permission.objects.filter(
        codename__in=[
            'add_task',
            'view_task',
            'change_task',
            'delete_task',
        ]
    )
    user_group.permissions.set(user_permissions)
    
    # Moderator permissions (view all, moderate)
    moderator_permissions = Permission.objects.filter(
        codename__in=[
            'view_task',
            'change_task',
        ]
    )
    moderator_group.permissions.set(moderator_permissions)
    
    # Admin permissions (all permissions)
    admin_permissions = Permission.objects.all()
    admin_group.permissions.set(admin_permissions)


class Migration(migrations.Migration):
    dependencies = [
        ('authentication', '0001_initial'),
        ('tasks', '0001_initial'),
    ]
    
    operations = [
        migrations.RunPython(create_groups),
    ]
```

### Assign User to Group

```python
# apps/authentication/services.py
from django.contrib.auth.models import Group

class AuthService:
    @staticmethod
    def register_user(validated_data, request=None):
        user = User.objects.create_user(**validated_data)
        
        # Auto-assign to "User" group
        user_group = Group.objects.get(name='User')
        user.groups.add(user_group)
        
        return user
```

### Check Group in Views

```python
# apps/tasks/views.py
class TaskListView(APIView):
    def get(self, request):
        # Admin & Moderator can see all tasks
        if request.user.groups.filter(name__in=['Admin', 'Moderator']).exists():
            tasks = Task.objects.all()
        else:
            tasks = Task.objects.filter(user=request.user)
        
        serializer = TaskSerializer(tasks, many=True)
        return Response({"data": serializer.data})
```

### Custom Permission Class

```python
# apps/core/permissions.py
from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    """Only users in Admin group"""
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Admin').exists()


class IsModerator(BasePermission):
    """Users in Moderator or Admin group"""
    def has_permission(self, request, view):
        return request.user.groups.filter(name__in=['Moderator', 'Admin']).exists()


class IsOwnerOrAdmin(BasePermission):
    """Owner or Admin can access"""
    def has_object_permission(self, request, view, obj):
        # Owner
        if obj.user == request.user:
            return True
        
        # Admin
        return request.user.groups.filter(name='Admin').exists()
```

### Use in Views

```python
from apps.core.permissions import IsAdmin, IsOwnerOrAdmin

class AllTasksView(APIView):
    permission_classes = [IsAdmin]  # Admin only
    
    def get(self, request):
        tasks = Task.objects.all()
        return Response({"data": TaskSerializer(tasks, many=True).data})


class TaskDetailView(APIView):
    permission_classes = [IsOwnerOrAdmin]
    
    def put(self, request, pk):
        task = Task.objects.get(pk=pk)
        self.check_object_permissions(request, task)
        
        # Update task
        serializer = TaskSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"data": serializer.data})
        
        return Response({"errors": serializer.errors}, status=400)
```

---

## 4️⃣ SENIOR LEVEL - Custom Permissions (Advanced)

### Custom Permission Model

```python
# apps/core/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomPermission(models.Model):
    """
    Fine-grained permissions beyond CRUD
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    resource = models.CharField(max_length=50)  # 'task', 'project', etc.
    action = models.CharField(max_length=50)    # 'approve', 'publish', etc.
    
    class Meta:
        unique_together = ['user', 'resource', 'action']
    
    def __str__(self):
        return f"{self.user.email} can {self.action} {self.resource}"


# Helper function
def user_can(user, action, resource):
    """
    Check if user has custom permission
    
    Usage:
        if user_can(request.user, 'approve', 'task'):
            # Do something
    """
    return CustomPermission.objects.filter(
        user=user,
        action=action,
        resource=resource
    ).exists()
```

### Row-Level Permissions (Object-Level)

```python
# apps/tasks/models.py
class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    is_public = models.BooleanField(default=False)
    
    def can_view(self, user):
        """Custom visibility logic"""
        # Owner can always view
        if self.user == user:
            return True
        
        # Public tasks visible to all
        if self.is_public:
            return True
        
        # Admin can view all
        if user.groups.filter(name='Admin').exists():
            return True
        
        return False
    
    def can_edit(self, user):
        """Only owner or admin"""
        return self.user == user or user.groups.filter(name='Admin').exists()
```

### Use in Views

```python
class TaskDetailView(APIView):
    def get(self, request, pk):
        task = Task.objects.get(pk=pk)
        
        # Check custom permission
        if not task.can_view(request.user):
            return Response(
                {"error": "You don't have permission to view this task"},
                status=403
            )
        
        return Response({"data": TaskSerializer(task).data})
    
    def put(self, request, pk):
        task = Task.objects.get(pk=pk)
        
        if not task.can_edit(request.user):
            return Response({"error": "Permission denied"}, status=403)
        
        # Update logic
        ...
```

---

## 5️⃣ SENIOR LEVEL - Service Layer Permissions

Move permission logic dari views ke service layer (cleaner).

```python
# apps/tasks/services.py
from django.core.exceptions import PermissionDenied

class TaskService:
    
    @staticmethod
    def get_user_tasks(user):
        """
        Get tasks based on user role
        """
        if user.groups.filter(name__in=['Admin', 'Moderator']).exists():
            return Task.objects.all()
        
        return Task.objects.filter(user=user)
    
    @staticmethod
    def update_task(task, user, validated_data):
        """
        Update task with permission check
        """
        # Permission check
        if task.user != user and not user.groups.filter(name='Admin').exists():
            raise PermissionDenied("You don't have permission to edit this task")
        
        # Update
        for key, value in validated_data.items():
            setattr(task, key, value)
        task.save()
        
        return task
    
    @staticmethod
    def delete_task(task, user):
        """
        Delete task with permission check
        """
        if task.user != user and not user.groups.filter(name='Admin').exists():
            raise PermissionDenied("You don't have permission to delete this task")
        
        task.delete()
```

### Views (Clean & Thin)

```python
# apps/tasks/views.py
from apps.tasks.services import TaskService

class TaskListView(APIView):
    def get(self, request):
        # Service handles permission logic
        tasks = TaskService.get_user_tasks(request.user)
        
        serializer = TaskSerializer(tasks, many=True)
        return Response({"data": serializer.data})


class TaskDetailView(APIView):
    def put(self, request, pk):
        task = Task.objects.get(pk=pk)
        serializer = TaskSerializer(data=request.data, partial=True)
        
        if serializer.is_valid():
            try:
                # Service handles permission
                updated_task = TaskService.update_task(
                    task, request.user, serializer.validated_data
                )
                return Response({"data": TaskSerializer(updated_task).data})
            
            except PermissionDenied as e:
                return Response({"error": str(e)}, status=403)
        
        return Response({"errors": serializer.errors}, status=400)
```

---

## 6️⃣ EXPERT LEVEL - Decorator Pattern

```python
# apps/core/decorators.py
from functools import wraps
from django.core.exceptions import PermissionDenied

def require_group(*group_names):
    """
    Decorator untuk check user group
    
    Usage:
        @require_group('Admin', 'Moderator')
        def some_service_method(user, ...):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Assume first arg or 'user' kwarg is User
            user = kwargs.get('user') or (args[0] if args else None)
            
            if not user:
                raise PermissionDenied("User not provided")
            
            if not user.groups.filter(name__in=group_names).exists():
                raise PermissionDenied(
                    f"User must be in one of these groups: {', '.join(group_names)}"
                )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_permission(permission_codename):
    """
    Decorator untuk check Django permission
    
    Usage:
        @require_permission('tasks.delete_task')
        def delete_all_tasks(user):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = kwargs.get('user') or (args[0] if args else None)
            
            if not user.has_perm(permission_codename):
                raise PermissionDenied(
                    f"User does not have permission: {permission_codename}"
                )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator
```

### Use Decorators

```python
# apps/tasks/services.py
from apps.core.decorators import require_group, require_permission

class TaskService:
    
    @staticmethod
    @require_group('Admin')
    def delete_all_tasks(user):
        """Only Admin can delete all tasks"""
        Task.objects.all().delete()
    
    @staticmethod
    @require_permission('tasks.change_task')
    def bulk_update_status(user, task_ids, new_status):
        """Only users with change_task permission"""
        Task.objects.filter(id__in=task_ids).update(status=new_status)
```

---

## 📊 Comparison Table

| Approach | Complexity | Scalability | Use Case |
|----------|-----------|-------------|----------|
| **Boolean Field** | ⭐ | ⭐ | 1-2 roles |
| **Django Permissions** | ⭐⭐ | ⭐⭐ | CRUD permissions |
| **Django Groups** | ⭐⭐⭐ | ⭐⭐⭐ | 3-5 roles |
| **Custom Permissions** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Complex business rules |
| **Third-party (django-guardian)** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Object-level permissions |

---

## 🎯 Best Practices

### 1. Choose Based on Scale

```python
# Small app (< 100 users)
→ Simple Boolean Field (is_admin)

# Medium app (100-10K users, 3-5 roles)
→ Django Groups

# Large app (10K+ users, complex permissions)
→ Custom RBAC or django-guardian
```

### 2. Separate Permission Logic

```python
# ❌ Bad: Permission logic in views
class TaskDetailView(APIView):
    def put(self, request, pk):
        task = Task.objects.get(pk=pk)
        if task.user != request.user and not request.user.is_admin:
            return Response({"error": "Denied"}, status=403)
        # ... update logic

# ✅ Good: Permission logic in service
class TaskDetailView(APIView):
    def put(self, request, pk):
        task = Task.objects.get(pk=pk)
        try:
            updated_task = TaskService.update_task(task, request.user, data)
            return Response({"data": TaskSerializer(updated_task).data})
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=403)
```

### 3. Test Permissions

```python
# apps/tasks/tests.py
from django.test import TestCase
from django.contrib.auth.models import Group

class PermissionTestCase(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(email='admin@test.com', password='pass')
        self.user = User.objects.create_user(email='user@test.com', password='pass')
        
        admin_group = Group.objects.get(name='Admin')
        self.admin.groups.add(admin_group)
    
    def test_admin_can_view_all_tasks(self):
        tasks = TaskService.get_user_tasks(self.admin)
        self.assertEqual(tasks.count(), Task.objects.count())
    
    def test_user_can_only_view_own_tasks(self):
        tasks = TaskService.get_user_tasks(self.user)
        self.assertEqual(tasks.count(), Task.objects.filter(user=self.user).count())
```

---

## 📚 Further Reading

- [Django Permissions Docs](https://docs.djangoproject.com/en/4.2/topics/auth/default/#permissions-and-authorization)
- [django-guardian](https://django-guardian.readthedocs.io/) (Object-level permissions)
- [DRF Permissions Guide](https://www.django-rest-framework.org/api-guide/permissions/)

---

## 💡 Summary

| Level | Implementation |
|-------|---------------|
| **Junior** | Boolean field (`is_admin`) |
| **Mid** | Django built-in permissions |
| **Mid-Senior** | Django Groups |
| **Senior** | Service layer + custom permissions |
| **Expert** | Decorator pattern + row-level permissions |
