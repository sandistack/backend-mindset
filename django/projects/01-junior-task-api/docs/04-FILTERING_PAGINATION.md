# 🔍 Step 4: Filtering, Search & Pagination

**Waktu:** 3-4 jam  
**Prerequisite:** Step 3 selesai (Task CRUD berfungsi)

---

## 🎯 Tujuan

- Implementasi filtering dengan django-filter
- Full-text search
- Ordering/sorting
- Custom pagination

---

## 📋 Tasks

### 4.1 Setup django-filter

Pastikan sudah install dan tambahkan di settings:

**Di `settings/base.py`:**

```python
INSTALLED_APPS = [
    # ...
    'django_filters',
]

REST_FRAMEWORK = {
    # ...
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}
```

---

### 4.2 Task Filter

**Buat `apps/tasks/filters.py`:**

```python
import django_filters
from .models import Task

class TaskFilter(django_filters.FilterSet):
    # Exact match
    status = django_filters.CharFilter(field_name='status')
    priority = django_filters.CharFilter(field_name='priority')
    category = django_filters.NumberFilter(field_name='category__id')
    
    # Date range
    due_date_from = django_filters.DateFilter(
        field_name='due_date', 
        lookup_expr='gte'
    )
    due_date_to = django_filters.DateFilter(
        field_name='due_date', 
        lookup_expr='lte'
    )
    
    # Created date range
    created_from = django_filters.DateFilter(
        field_name='created_at', 
        lookup_expr='gte'
    )
    created_to = django_filters.DateFilter(
        field_name='created_at', 
        lookup_expr='lte'
    )
    
    # Boolean
    is_completed = django_filters.BooleanFilter(
        method='filter_is_completed'
    )
    is_overdue = django_filters.BooleanFilter(
        method='filter_is_overdue'
    )
    
    class Meta:
        model = Task
        fields = ['status', 'priority', 'category']
    
    def filter_is_completed(self, queryset, name, value):
        if value:
            return queryset.filter(status='done')
        return queryset.exclude(status='done')
    
    def filter_is_overdue(self, queryset, name, value):
        from django.utils import timezone
        now = timezone.now()
        if value:
            return queryset.filter(
                due_date__lt=now,
                status__in=['pending', 'in_progress']
            )
        return queryset
```

**Referensi:** [FILTERING_SEARCH.md](../../../docs/02-database/FILTERING_SEARCH.md)

---

### 4.3 Apply Filter ke ViewSet

**Di `apps/tasks/views.py`:**

```python
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .filters import TaskFilter

class TaskViewSet(viewsets.ModelViewSet):
    # ...
    
    # Filter backends
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    # django-filter
    filterset_class = TaskFilter
    
    # Search fields
    search_fields = ['title', 'description']
    
    # Ordering
    ordering_fields = ['created_at', 'updated_at', 'due_date', 'priority']
    ordering = ['-created_at']  # Default ordering
```

---

### 4.4 Custom Pagination

**Buat `apps/core/pagination.py`:**

```python
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'success': True,
            'data': data,
            'pagination': {
                'count': self.page.paginator.count,
                'page': self.page.number,
                'page_size': self.get_page_size(self.request),
                'total_pages': self.page.paginator.num_pages,
                'has_next': self.page.has_next(),
                'has_previous': self.page.has_previous(),
            }
        })
```

**Apply ke ViewSet:**

```python
from apps.core.pagination import CustomPagination

class TaskViewSet(viewsets.ModelViewSet):
    # ...
    pagination_class = CustomPagination
```

**Atau set globally di settings:**

```python
REST_FRAMEWORK = {
    # ...
    'DEFAULT_PAGINATION_CLASS': 'apps.core.pagination.CustomPagination',
    'PAGE_SIZE': 10,
}
```

**Referensi:** [PAGINATION.md](../../../docs/02-database/PAGINATION.md)

---

### 4.5 Category Filter (Bonus)

Buat filter untuk categories juga:

```python
class CategoryFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = Category
        fields = ['name']
```

---

## 📊 Query Examples

```
# Filter by status
GET /api/tasks/?status=pending

# Filter by priority
GET /api/tasks/?priority=high

# Filter by category
GET /api/tasks/?category=1

# Date range
GET /api/tasks/?due_date_from=2024-01-01&due_date_to=2024-12-31

# Search
GET /api/tasks/?search=meeting

# Ordering
GET /api/tasks/?ordering=-due_date
GET /api/tasks/?ordering=priority,-created_at

# Combine filters
GET /api/tasks/?status=pending&priority=high&search=project&ordering=-due_date

# Pagination
GET /api/tasks/?page=2&page_size=20

# Overdue tasks
GET /api/tasks/?is_overdue=true

# Completed tasks
GET /api/tasks/?is_completed=true
```

---

## ✅ Checklist

- [ ] django-filter terkonfigurasi
- [ ] TaskFilter dengan semua fields
- [ ] Date range filters berfungsi
- [ ] Custom filters (is_completed, is_overdue)
- [ ] Search berfungsi (title, description)
- [ ] Ordering berfungsi
- [ ] Custom pagination class
- [ ] Pagination response format sesuai
- [ ] CategoryFilter (bonus)

---

## 🧪 Testing Manual

```bash
# Filter by status
curl "http://localhost:8000/api/tasks/?status=pending" \
  -H "Authorization: Bearer <token>"

# Search
curl "http://localhost:8000/api/tasks/?search=meeting" \
  -H "Authorization: Bearer <token>"

# Combined
curl "http://localhost:8000/api/tasks/?status=pending&priority=high&ordering=-due_date&page=1&page_size=5" \
  -H "Authorization: Bearer <token>"

# Overdue
curl "http://localhost:8000/api/tasks/?is_overdue=true" \
  -H "Authorization: Bearer <token>"
```

---

## 📝 Expected Response

```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "title": "Complete project documentation",
            "status": "pending",
            "priority": "high",
            "due_date": "2024-03-15T17:00:00Z",
            "category": {
                "id": 1,
                "name": "Work",
                "color": "#EF4444"
            },
            "created_at": "2024-03-01T10:30:00Z"
        }
    ],
    "pagination": {
        "count": 25,
        "page": 1,
        "page_size": 10,
        "total_pages": 3,
        "has_next": true,
        "has_previous": false
    }
}
```

---

## 🔗 Referensi

- [FILTERING_SEARCH.md](../../../docs/02-database/FILTERING_SEARCH.md) - Complete filtering guide
- [PAGINATION.md](../../../docs/02-database/PAGINATION.md) - Pagination patterns

---

## ➡️ Next Step

Lanjut ke [05-TESTING.md](05-TESTING.md) - Unit & Integration Tests
