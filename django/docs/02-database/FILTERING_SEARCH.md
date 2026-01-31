# 🔍 FILTERING & SEARCH - Django REST Framework (Junior → Senior)

Dokumentasi lengkap tentang filtering, searching, dan ordering di DRF.

---

## 🎯 Kenapa Filtering Penting?

```
Without Filtering:
GET /api/tasks/ → Returns 10,000 tasks

With Filtering:
GET /api/tasks/?status=TODO → Returns 50 tasks
GET /api/tasks/?priority=HIGH&status=TODO → Returns 10 tasks
```

**Benefits:**
- ✅ Faster response time
- ✅ Better UX
- ✅ Reduced server load
- ✅ More flexible API

---

## 1️⃣ JUNIOR LEVEL - Manual Filtering

### Basic Query Parameters

```python
# apps/tasks/views.py
from rest_framework.views import APIView
from rest_framework.response import Response

class TaskListView(APIView):
    def get(self, request):
        tasks = Task.objects.filter(user=request.user)
        
        # Manual filtering by status
        status = request.query_params.get('status')
        if status:
            tasks = tasks.filter(status=status)
        
        # Manual filtering by priority
        priority = request.query_params.get('priority')
        if priority:
            tasks = tasks.filter(priority=priority)
        
        serializer = TaskSerializer(tasks, many=True)
        return Response({"data": serializer.data})


# Usage:
# GET /api/tasks/?status=TODO
# GET /api/tasks/?status=TODO&priority=HIGH
```

### Search by Title

```python
def get(self, request):
    tasks = Task.objects.filter(user=request.user)
    
    # Search
    search = request.query_params.get('search')
    if search:
        tasks = tasks.filter(title__icontains=search)
    
    serializer = TaskSerializer(tasks, many=True)
    return Response({"data": serializer.data})


# Usage:
# GET /api/tasks/?search=buy
```

---

## 2️⃣ MID LEVEL - Multiple Filters

### Combined Filters

```python
class TaskListView(APIView):
    def get(self, request):
        tasks = Task.objects.filter(user=request.user)
        
        # Status filter
        status = request.query_params.get('status')
        if status:
            tasks = tasks.filter(status=status)
        
        # Priority filter
        priority = request.query_params.get('priority')
        if priority:
            tasks = tasks.filter(priority=priority)
        
        # Search (title or description)
        search = request.query_params.get('search')
        if search:
            from django.db.models import Q
            tasks = tasks.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
        
        # Date range filter
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')
        
        if from_date:
            tasks = tasks.filter(created_at__gte=from_date)
        if to_date:
            tasks = tasks.filter(created_at__lte=to_date)
        
        # Ordering
        ordering = request.query_params.get('ordering', '-created_at')
        tasks = tasks.order_by(ordering)
        
        serializer = TaskSerializer(tasks, many=True)
        return Response({"data": serializer.data})


# Usage:
# GET /api/tasks/?status=TODO&priority=HIGH&search=buy&ordering=title
# GET /api/tasks/?from_date=2026-01-01&to_date=2026-01-31
```

---

## 3️⃣ MID-SENIOR LEVEL - django-filter (Recommended)

### Install django-filter

```bash
pip install django-filter
```

### Setup

```python
# config/settings/base.py
INSTALLED_APPS = [
    ...
    'django_filters',
]

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}
```

### Basic FilterSet

```python
# apps/tasks/filters.py
import django_filters
from .models import Task

class TaskFilter(django_filters.FilterSet):
    """
    FilterSet untuk Task model
    """
    
    # Exact match
    status = django_filters.CharFilter(field_name='status')
    priority = django_filters.CharFilter(field_name='priority')
    
    # Case-insensitive contains
    title = django_filters.CharFilter(field_name='title', lookup_expr='icontains')
    
    # Date range
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    # Boolean
    is_completed = django_filters.BooleanFilter(method='filter_completed')
    
    class Meta:
        model = Task
        fields = ['status', 'priority', 'title']
    
    def filter_completed(self, queryset, name, value):
        """Custom filter method"""
        if value:
            return queryset.filter(status='DONE')
        return queryset.exclude(status='DONE')
```

### Use in ViewSet

```python
# apps/tasks/views.py
from rest_framework import viewsets
from .filters import TaskFilter

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    filterset_class = TaskFilter  # ← Use FilterSet
    
    def get_queryset(self):
        # User can only see own tasks
        return Task.objects.filter(user=self.request.user)


# Usage:
# GET /api/tasks/?status=TODO
# GET /api/tasks/?priority=HIGH&status=TODO
# GET /api/tasks/?title=buy
# GET /api/tasks/?created_after=2026-01-01
# GET /api/tasks/?is_completed=true
```

---

## 4️⃣ SENIOR LEVEL - Advanced Filtering

### Multiple Lookup Expressions

```python
class TaskFilter(django_filters.FilterSet):
    # Title (exact, contains, startswith, endswith)
    title = django_filters.CharFilter(lookup_expr='icontains')
    title_exact = django_filters.CharFilter(field_name='title', lookup_expr='exact')
    title_starts = django_filters.CharFilter(field_name='title', lookup_expr='istartswith')
    
    # Priority (multiple choice)
    priority = django_filters.MultipleChoiceFilter(
        choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High')]
    )
    
    # Created date (range)
    created_at = django_filters.DateFromToRangeFilter()
    
    # Due date (is null or not null)
    has_due_date = django_filters.BooleanFilter(field_name='due_date', lookup_expr='isnull', exclude=True)
    
    class Meta:
        model = Task
        fields = {
            'status': ['exact', 'in'],  # ?status=TODO or ?status__in=TODO,DONE
            'priority': ['exact'],
            'created_at': ['gte', 'lte', 'exact'],
        }


# Usage:
# GET /api/tasks/?priority=HIGH,MEDIUM  (multiple)
# GET /api/tasks/?status__in=TODO,IN_PROGRESS
# GET /api/tasks/?created_at_after=2026-01-01&created_at_before=2026-01-31
# GET /api/tasks/?has_due_date=true
```

### Custom Filter Methods

```python
class TaskFilter(django_filters.FilterSet):
    # Custom filter: tasks due soon
    due_soon = django_filters.BooleanFilter(method='filter_due_soon')
    
    # Custom filter: overdue tasks
    overdue = django_filters.BooleanFilter(method='filter_overdue')
    
    # Custom filter: by tag name
    tag = django_filters.CharFilter(method='filter_by_tag')
    
    def filter_due_soon(self, queryset, name, value):
        """Tasks due within 3 days"""
        if value:
            from django.utils import timezone
            from datetime import timedelta
            
            now = timezone.now()
            soon = now + timedelta(days=3)
            
            return queryset.filter(
                due_date__gte=now,
                due_date__lte=soon
            )
        return queryset
    
    def filter_overdue(self, queryset, name, value):
        """Tasks past due date and not done"""
        if value:
            from django.utils import timezone
            
            return queryset.filter(
                due_date__lt=timezone.now(),
                status__in=['TODO', 'IN_PROGRESS']
            )
        return queryset
    
    def filter_by_tag(self, queryset, name, value):
        """Filter by tag name (many-to-many)"""
        return queryset.filter(tags__name__icontains=value).distinct()
    
    class Meta:
        model = Task
        fields = []


# Usage:
# GET /api/tasks/?due_soon=true
# GET /api/tasks/?overdue=true
# GET /api/tasks/?tag=urgent
```

---

## 5️⃣ SENIOR LEVEL - Search & Ordering

### Search Multiple Fields

```python
# config/settings/base.py
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',  # ← Enable search
        'rest_framework.filters.OrderingFilter',  # ← Enable ordering
    ],
}
```

```python
# apps/tasks/views.py
class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    filterset_class = TaskFilter
    
    # Search fields
    search_fields = ['title', 'description', 'tags__name']
    
    # Ordering fields
    ordering_fields = ['created_at', 'updated_at', 'title', 'priority', 'due_date']
    ordering = ['-created_at']  # Default ordering


# Usage:
# GET /api/tasks/?search=buy milk
# GET /api/tasks/?ordering=title
# GET /api/tasks/?ordering=-created_at  (descending)
# GET /api/tasks/?ordering=priority,title  (multiple)
```

### Custom Search

```python
from rest_framework import filters

class CustomSearchFilter(filters.SearchFilter):
    """
    Custom search filter with weights
    """
    
    def filter_queryset(self, request, queryset, view):
        search_term = request.query_params.get('search', '')
        
        if search_term:
            from django.db.models import Q, Value, CharField
            from django.db.models.functions import Concat
            
            # Search in multiple fields with OR
            queryset = queryset.filter(
                Q(title__icontains=search_term) |
                Q(description__icontains=search_term) |
                Q(tags__name__icontains=search_term)
            ).distinct()
        
        return queryset
```

---

## 6️⃣ EXPERT LEVEL - Full-Text Search (PostgreSQL)

### PostgreSQL Full-Text Search

```python
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank

class TaskViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        queryset = Task.objects.filter(user=self.request.user)
        
        search = self.request.query_params.get('search')
        
        if search:
            # Full-text search
            search_vector = SearchVector('title', weight='A') + \
                            SearchVector('description', weight='B')
            
            search_query = SearchQuery(search)
            
            queryset = queryset.annotate(
                rank=SearchRank(search_vector, search_query)
            ).filter(rank__gte=0.1).order_by('-rank')
        
        return queryset


# Benefits:
# - Faster than LIKE queries
# - Supports stemming (run, running, ran)
# - Relevance ranking
```

### Add Full-Text Search Index

```python
# Migration
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector

class Migration(migrations.Migration):
    operations = [
        migrations.AddIndex(
            model_name='task',
            index=GinIndex(
                SearchVector('title', 'description'),
                name='task_search_idx'
            ),
        ),
    ]
```

---

## 7️⃣ EXPERT LEVEL - Dynamic Filtering

### Allow Any Field Filtering

```python
class DynamicFilterBackend(filters.BaseFilterBackend):
    """
    Allow filtering on any field via query params
    
    Usage: GET /api/tasks/?title=Buy&status=TODO
    """
    
    def filter_queryset(self, request, queryset, view):
        # Get all query params
        filter_params = {}
        
        for param, value in request.query_params.items():
            # Skip reserved params
            if param in ['search', 'ordering', 'page', 'page_size']:
                continue
            
            # Check if field exists in model
            if hasattr(queryset.model, param):
                filter_params[param] = value
        
        return queryset.filter(**filter_params)
```

---

## 📊 Filter Types Comparison

| Type | Use Case | Example |
|------|----------|---------|
| **CharFilter** | Text exact match | `?status=TODO` |
| **icontains** | Case-insensitive contains | `?title__icontains=buy` |
| **NumberFilter** | Numeric fields | `?priority=1` |
| **BooleanFilter** | True/False | `?is_active=true` |
| **DateFilter** | Date exact | `?created_at=2026-01-31` |
| **DateRangeFilter** | Date range | `?created_at_after=2026-01-01` |
| **MultipleChoiceFilter** | Multiple values | `?status=TODO,DONE` |
| **MethodFilter** | Custom logic | `?overdue=true` |

---

## 🎯 Best Practices

### 1. Index Filtered Fields

```python
class Task(models.Model):
    status = models.CharField(max_length=20, db_index=True)  # ← Index
    priority = models.CharField(max_length=20, db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['status', 'priority']),  # Composite
            models.Index(fields=['-created_at']),
        ]
```

### 2. Limit Allowed Filters

```python
# ❌ Bad: Allow any field
class TaskFilter(django_filters.FilterSet):
    class Meta:
        model = Task
        fields = '__all__'  # Dangerous!

# ✅ Good: Explicit fields only
class TaskFilter(django_filters.FilterSet):
    class Meta:
        model = Task
        fields = ['status', 'priority', 'created_at']
```

### 3. Validate Filter Values

```python
def filter_status(self, queryset, name, value):
    allowed = ['TODO', 'IN_PROGRESS', 'DONE']
    
    if value not in allowed:
        return queryset.none()
    
    return queryset.filter(status=value)
```

### 4. Performance: Use select_related/prefetch_related

```python
class TaskViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Task.objects.select_related('user') \
                           .prefetch_related('tags') \
                           .filter(user=self.request.user)
```

---

## 💡 Summary

| Level | Technique |
|-------|-----------|
| **Junior** | Manual filtering via query params |
| **Mid** | Multiple filters with Q objects |
| **Mid-Senior** | django-filter (FilterSet) |
| **Senior** | Custom filters, search, ordering |
| **Expert** | Full-text search, dynamic filtering |

**Key Points:**
- ✅ Use django-filter for clean code
- ✅ Index filtered fields
- ✅ Validate filter inputs
- ✅ Use SearchFilter for text search
- ✅ PostgreSQL full-text for large datasets

**Common Query Patterns:**
```
# Filters
?status=TODO&priority=HIGH

# Search
?search=buy milk

# Ordering
?ordering=-created_at

# Combined
?status=TODO&search=buy&ordering=priority
```
