# 🔄 API VERSIONING - Django REST Framework (Junior → Senior)

Dokumentasi lengkap tentang API versioning di Django REST Framework.

---

## 🎯 Kenapa API Versioning Penting?

| Problem | Solution |
|---------|----------|
| Breaking changes | Version baru, old version tetap jalan |
| Multiple clients | Support berbagai versi client |
| Gradual migration | Client bisa migrate pelan-pelan |
| Backward compatibility | Old apps tetap works |

**Real World Examples:**
- `api.example.com/v1/users`
- `api.example.com/v2/users`
- Header: `Accept: application/vnd.api+json; version=2`

---

## 📊 Versioning Strategies

| Strategy | Example | Pros | Cons |
|----------|---------|------|------|
| **URL Path** | `/api/v1/users` | Simple, obvious | URL changes |
| **Query Param** | `/api/users?version=1` | Easy to implement | Can be cached wrong |
| **Header** | `Accept-Version: 1.0` | Clean URLs | Hidden from users |
| **Accept Header** | `Accept: application/vnd.api.v1+json` | RESTful | Complex |
| **Hostname** | `v1.api.example.com` | Complete isolation | Infrastructure heavy |

---

## 1️⃣ JUNIOR LEVEL - URL Path Versioning

### Setup

```python
# config/settings/base.py
REST_FRAMEWORK = {
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_VERSION': 'v1',
    'ALLOWED_VERSIONS': ['v1', 'v2'],
    'VERSION_PARAM': 'version',
}
```

### URL Configuration

```python
# config/urls.py
from django.urls import path, include

urlpatterns = [
    path('api/v1/', include('apps.api.v1.urls')),
    path('api/v2/', include('apps.api.v2.urls')),
]
```

### Directory Structure

```
apps/
└── api/
    ├── v1/
    │   ├── __init__.py
    │   ├── urls.py
    │   ├── views.py
    │   └── serializers.py
    └── v2/
        ├── __init__.py
        ├── urls.py
        ├── views.py
        └── serializers.py
```

### V1 Implementation

```python
# apps/api/v1/serializers.py
from rest_framework import serializers
from apps.tasks.models import Task

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'status', 'created_at']


# apps/api/v1/views.py
from rest_framework import generics
from apps.tasks.models import Task
from .serializers import TaskSerializer

class TaskListView(generics.ListCreateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer


# apps/api/v1/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('tasks/', views.TaskListView.as_view(), name='v1-task-list'),
]
```

### V2 dengan Perubahan

```python
# apps/api/v2/serializers.py
from rest_framework import serializers
from apps.tasks.models import Task

class TaskSerializer(serializers.ModelSerializer):
    # V2: Tambah field baru
    owner = serializers.StringRelatedField(source='user')
    priority = serializers.CharField()
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status',
            'priority', 'owner', 'is_overdue',  # New fields
            'created_at', 'updated_at'
        ]
    
    def get_is_overdue(self, obj):
        from django.utils import timezone
        if obj.due_date:
            return obj.due_date < timezone.now().date()
        return False


# apps/api/v2/views.py
from rest_framework import generics
from apps.tasks.models import Task
from .serializers import TaskSerializer

class TaskListView(generics.ListCreateAPIView):
    queryset = Task.objects.select_related('user')
    serializer_class = TaskSerializer
    filterset_fields = ['status', 'priority']  # V2: Add filtering


# apps/api/v2/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('tasks/', views.TaskListView.as_view(), name='v2-task-list'),
]
```

---

## 2️⃣ MID LEVEL - Namespace Versioning

### Single URLconf dengan Version Detection

```python
# config/urls.py
from django.urls import path, include, re_path

urlpatterns = [
    re_path(r'^api/(?P<version>v[1-2])/', include('apps.api.urls')),
]
```

```python
# apps/api/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('tasks/', views.TaskListView.as_view(), name='task-list'),
    path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task-detail'),
]
```

### Version-Aware Views

```python
# apps/api/views.py
from rest_framework import generics
from rest_framework.response import Response
from apps.tasks.models import Task
from . import serializers

class TaskListView(generics.ListCreateAPIView):
    queryset = Task.objects.all()
    
    def get_serializer_class(self):
        """Return different serializer based on version"""
        if self.request.version == 'v2':
            return serializers.TaskSerializerV2
        return serializers.TaskSerializerV1
    
    def get_queryset(self):
        """Different queryset per version"""
        qs = super().get_queryset()
        
        if self.request.version == 'v2':
            return qs.select_related('user').prefetch_related('tags')
        return qs


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Task.objects.all()
    
    def get_serializer_class(self):
        if self.request.version == 'v2':
            return serializers.TaskSerializerV2
        return serializers.TaskSerializerV1
    
    def destroy(self, request, *args, **kwargs):
        # V2: Soft delete instead of hard delete
        if request.version == 'v2':
            instance = self.get_object()
            instance.is_deleted = True
            instance.save()
            return Response(status=204)
        
        return super().destroy(request, *args, **kwargs)
```

---

## 3️⃣ MID-SENIOR LEVEL - Header Versioning

### Accept Header Versioning

```python
# config/settings/base.py
REST_FRAMEWORK = {
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.AcceptHeaderVersioning',
    'DEFAULT_VERSION': '1.0',
    'ALLOWED_VERSIONS': ['1.0', '1.1', '2.0'],
    'VERSION_PARAM': 'version',
}
```

### Request Format

```bash
# Request v1.0
curl -H "Accept: application/json; version=1.0" https://api.com/tasks/

# Request v2.0
curl -H "Accept: application/json; version=2.0" https://api.com/tasks/
```

### Custom Header Versioning

```python
# apps/core/versioning.py
from rest_framework.versioning import BaseVersioning

class CustomHeaderVersioning(BaseVersioning):
    """
    Version via custom header: X-API-Version
    """
    default_version = '1'
    allowed_versions = ['1', '2', '3']
    
    def determine_version(self, request, *args, **kwargs):
        version = request.META.get('HTTP_X_API_VERSION', self.default_version)
        
        if version not in self.allowed_versions:
            version = self.default_version
        
        return version
    
    def reverse(self, viewname, args=None, kwargs=None, request=None, format=None, **extra):
        # Return URL without version in path
        from django.urls import reverse
        return reverse(viewname, args=args, kwargs=kwargs)


# settings.py
REST_FRAMEWORK = {
    'DEFAULT_VERSIONING_CLASS': 'apps.core.versioning.CustomHeaderVersioning',
}
```

---

## 4️⃣ SENIOR LEVEL - Advanced Versioning Patterns

### Version Mixins

```python
# apps/core/mixins.py
class VersionedSerializerMixin:
    """
    Mixin untuk otomatis pilih serializer berdasarkan version
    
    Naming convention:
    - TaskSerializerV1
    - TaskSerializerV2
    """
    
    serializer_class_prefix = None  # e.g., 'TaskSerializer'
    
    def get_serializer_class(self):
        if self.serializer_class_prefix:
            version = getattr(self.request, 'version', 'v1')
            version_suffix = version.upper().replace('.', '_')
            
            # Try to get versioned serializer
            serializer_name = f'{self.serializer_class_prefix}{version_suffix}'
            
            from apps.api import serializers
            serializer_class = getattr(serializers, serializer_name, None)
            
            if serializer_class:
                return serializer_class
        
        return super().get_serializer_class()


class VersionedQuerySetMixin:
    """
    Mixin untuk version-specific querysets
    """
    
    def get_queryset(self):
        qs = super().get_queryset()
        version = getattr(self.request, 'version', 'v1')
        
        # Call version-specific method if exists
        method_name = f'get_queryset_{version.replace(".", "_")}'
        method = getattr(self, method_name, None)
        
        if method:
            return method(qs)
        
        return qs


# Usage
class TaskViewSet(VersionedSerializerMixin, VersionedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class_prefix = 'TaskSerializer'
    queryset = Task.objects.all()
    
    def get_queryset_v2(self, qs):
        return qs.select_related('user').prefetch_related('tags')
```

### Deprecation Headers

```python
# apps/core/middleware.py
from django.utils import timezone
from datetime import timedelta

class VersionDeprecationMiddleware:
    """
    Add deprecation headers for old API versions
    """
    
    DEPRECATION_INFO = {
        'v1': {
            'deprecated': True,
            'sunset_date': '2024-12-31',
            'message': 'API v1 is deprecated. Please migrate to v2.'
        },
        '1.0': {
            'deprecated': True,
            'sunset_date': '2024-12-31',
            'message': 'API version 1.0 is deprecated.'
        }
    }
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        version = getattr(request, 'version', None)
        
        if version and version in self.DEPRECATION_INFO:
            info = self.DEPRECATION_INFO[version]
            
            if info.get('deprecated'):
                response['Deprecation'] = 'true'
                response['Sunset'] = info.get('sunset_date', '')
                response['X-API-Deprecation-Message'] = info.get('message', '')
        
        return response
```

### Version Migration Helper

```python
# apps/core/utils.py
from functools import wraps

def deprecated_in_version(version, message=None):
    """
    Decorator to mark endpoint as deprecated in specific version
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            import warnings
            
            current_version = getattr(request, 'version', 'v1')
            
            if current_version >= version:
                msg = message or f'This endpoint is deprecated in {version}'
                warnings.warn(msg, DeprecationWarning)
                
                # Add header
                response = func(self, request, *args, **kwargs)
                response['X-Deprecated'] = 'true'
                response['X-Deprecated-Message'] = msg
                return response
            
            return func(self, request, *args, **kwargs)
        return wrapper
    return decorator


def available_from_version(version):
    """
    Decorator to restrict endpoint to specific version and above
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            from rest_framework.exceptions import NotFound
            
            current_version = getattr(request, 'version', 'v1')
            
            if current_version < version:
                raise NotFound(f'This endpoint is only available from {version}')
            
            return func(self, request, *args, **kwargs)
        return wrapper
    return decorator


# Usage
class TaskViewSet(viewsets.ModelViewSet):
    
    @deprecated_in_version('v2', 'Use /tasks/export/ instead')
    def download(self, request, *args, **kwargs):
        # Old download method
        pass
    
    @available_from_version('v2')
    def bulk_update(self, request, *args, **kwargs):
        # New in v2
        pass
```

### Complete Versioned API Structure

```
apps/
└── api/
    ├── __init__.py
    ├── urls.py              # Main router
    ├── versioning.py        # Custom versioning classes
    │
    ├── base/                # Shared base classes
    │   ├── views.py
    │   └── serializers.py
    │
    ├── v1/
    │   ├── __init__.py
    │   ├── urls.py
    │   ├── views/
    │   │   ├── __init__.py
    │   │   ├── tasks.py
    │   │   └── users.py
    │   └── serializers/
    │       ├── __init__.py
    │       ├── tasks.py
    │       └── users.py
    │
    └── v2/
        ├── __init__.py
        ├── urls.py
        ├── views/
        │   ├── __init__.py
        │   ├── tasks.py      # New/modified views
        │   └── users.py
        └── serializers/
            ├── __init__.py
            ├── tasks.py      # New/modified serializers
            └── users.py
```

### Shared Base Classes

```python
# apps/api/base/views.py
from rest_framework import viewsets

class BaseTaskViewSet(viewsets.ModelViewSet):
    """Base class shared between versions"""
    
    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)


# apps/api/v1/views/tasks.py
from apps.api.base.views import BaseTaskViewSet
from ..serializers.tasks import TaskSerializer

class TaskViewSet(BaseTaskViewSet):
    serializer_class = TaskSerializer


# apps/api/v2/views/tasks.py
from apps.api.base.views import BaseTaskViewSet
from ..serializers.tasks import TaskSerializer

class TaskViewSet(BaseTaskViewSet):
    serializer_class = TaskSerializer
    filterset_fields = ['status', 'priority']  # V2 feature
    
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related('user')  # V2 optimization
```

---

## 📋 Version Changelog

Maintain a changelog for API versions:

```python
# apps/api/changelog.py
API_CHANGELOG = {
    'v2.0': {
        'released': '2024-01-01',
        'changes': [
            'Added priority field to tasks',
            'Added bulk operations',
            'Soft delete instead of hard delete',
            'Added filtering and search',
        ]
    },
    'v1.1': {
        'released': '2023-06-01',
        'changes': [
            'Added due_date field',
            'Fixed pagination',
        ]
    },
    'v1.0': {
        'released': '2023-01-01',
        'changes': [
            'Initial release',
        ]
    }
}
```

---

## ✅ Checklist Implementasi

| Level | Fitur | Status |
|-------|-------|--------|
| Junior | URL path versioning | ⬜ |
| Junior | Separate serializers per version | ⬜ |
| Mid | Version-aware views | ⬜ |
| Mid | Header versioning | ⬜ |
| Senior | Deprecation headers | ⬜ |
| Senior | Version mixins | ⬜ |
| Senior | Version changelog | ⬜ |

---

## 🔗 Referensi

- [DRF Versioning](https://www.django-rest-framework.org/api-guide/versioning/)
- [API Versioning Best Practices](https://restfulapi.net/versioning/)
