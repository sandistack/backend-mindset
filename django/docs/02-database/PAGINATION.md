# 📄 PAGINATION - Django REST Framework (Junior → Senior)

Dokumentasi lengkap tentang pagination di Django REST Framework.

---

## 🎯 Kenapa Pagination Penting?

| Tanpa Pagination | Dengan Pagination |
|-----------------|-------------------|
| Load 10,000 records sekaligus | Load 10-20 records per request |
| Response time 5-10 detik | Response time < 1 detik |
| Frontend freeze | Smooth user experience |
| Database overload | Efficient queries |
| Server crash saat 1M+ records | Scale to millions |

**Real World Example:**
- Instagram: Infinite scroll (pagination)
- Google Search: Page 1, 2, 3 (pagination)
- Gmail: Load 50 emails at a time (pagination)

---

## 🔢 Types of Pagination

| Type | Use Case | Example |
|------|----------|---------|
| **Page Number** | Simple apps, admin panels | `?page=2&page_size=10` |
| **Limit Offset** | More flexible control | `?limit=10&offset=20` |
| **Cursor** | Social feeds, large datasets (1M+) | `?cursor=abc123` |

---

## 1️⃣ JUNIOR LEVEL - Manual Pagination

### Django Paginator (Template Based)

```python
# views.py
from django.core.paginator import Paginator
from django.shortcuts import render

def task_list(request):
    tasks = Task.objects.all()
    
    # Paginate: 10 items per page
    paginator = Paginator(tasks, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'tasks.html', {'page_obj': page_obj})
```

```html
<!-- tasks.html -->
{% for task in page_obj %}
    <div>{{ task.title }}</div>
{% endfor %}

<!-- Pagination controls -->
<div class="pagination">
    {% if page_obj.has_previous %}
        <a href="?page=1">First</a>
        <a href="?page={{ page_obj.previous_page_number }}">Previous</a>
    {% endif %}
    
    <span>Page {{ page_obj.number }} of {{ page_obj.paginator.num_pages }}</span>
    
    {% if page_obj.has_next %}
        <a href="?page={{ page_obj.next_page_number }}">Next</a>
        <a href="?page={{ page_obj.paginator.num_pages }}">Last</a>
    {% endif %}
</div>
```

### REST API - Manual Pagination

```python
# views.py (APIView)
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.paginator import Paginator

class TaskListView(APIView):
    def get(self, request):
        tasks = Task.objects.filter(user=request.user)
        
        # Get page number from query param
        page_number = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 10)
        
        # Paginate
        paginator = Paginator(tasks, page_size)
        page_obj = paginator.get_page(page_number)
        
        # Serialize
        serializer = TaskSerializer(page_obj, many=True)
        
        return Response({
            "success": True,
            "message": "Tasks retrieved successfully",
            "data": serializer.data,
            "pagination": {
                "count": paginator.count,
                "current_page": page_obj.number,
                "total_pages": paginator.num_pages,
                "has_next": page_obj.has_next(),
                "has_previous": page_obj.has_previous()
            }
        })
```

**Cons:**
- Repetitive code di setiap view
- Not DRY
- Inconsistent format

---

## 2️⃣ MID LEVEL - PageNumberPagination (DRF Built-in)

Django REST Framework punya built-in pagination classes.

### Setup Global Pagination

```python
# config/settings/base.py
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10
}
```

### Pakai di ViewSet (Simplest)

```python
# apps/tasks/views.py
from rest_framework import viewsets

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    # Pagination auto-enabled!
```

**Request:**
```
GET /api/tasks/?page=2
```

**Response:**
```json
{
    "count": 50,
    "next": "http://api.com/tasks/?page=3",
    "previous": "http://api.com/tasks/?page=1",
    "results": [
        {"id": 11, "title": "Task 11"},
        {"id": 12, "title": "Task 12"}
    ]
}
```

### Pakai di APIView (Manual)

```python
from rest_framework.pagination import PageNumberPagination

class TaskListView(APIView):
    def get(self, request):
        tasks = Task.objects.filter(user=request.user)
        
        # Use paginator
        paginator = PageNumberPagination()
        paginated_tasks = paginator.paginate_queryset(tasks, request)
        
        serializer = TaskSerializer(paginated_tasks, many=True)
        
        # Return paginated response
        return paginator.get_paginated_response(serializer.data)
```

---

## 3️⃣ MID-SENIOR LEVEL - Custom Pagination Class

### Standard Pagination dengan Custom Format

```python
# apps/core/pagination.py
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class StandardPagination(PageNumberPagination):
    """
    Standard pagination dengan custom response format
    """
    page_size = 10
    page_size_query_param = 'page_size'  # Allow ?page_size=20
    max_page_size = 100                   # Max limit
    
    def get_paginated_response(self, data):
        return Response({
            "success": True,
            "message": "Data retrieved successfully",
            "data": data,
            "pagination": {
                "count": self.page.paginator.count,
                "current_page": self.page.number,
                "total_pages": self.page.paginator.num_pages,
                "page_size": self.page_size,
                "next": self.page.has_next(),
                "previous": self.page.has_previous(),
                "next_url": self.get_next_link(),
                "previous_url": self.get_previous_link()
            }
        })
```

### Setup di Settings

```python
# config/settings/base.py
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'apps.core.pagination.StandardPagination',
    'PAGE_SIZE': 10
}
```

### Response Format

```json
{
    "success": true,
    "message": "Data retrieved successfully",
    "data": [
        {"id": 1, "title": "Task 1"},
        {"id": 2, "title": "Task 2"}
    ],
    "pagination": {
        "count": 50,
        "current_page": 1,
        "total_pages": 5,
        "page_size": 10,
        "next": true,
        "previous": false,
        "next_url": "http://api.com/tasks/?page=2",
        "previous_url": null
    }
}
```

---

## 4️⃣ SENIOR LEVEL - Multiple Pagination Types

### A) LimitOffsetPagination

Lebih flexible untuk skip records.

```python
# apps/core/pagination.py
from rest_framework.pagination import LimitOffsetPagination

class StandardLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 100
    
    def get_paginated_response(self, data):
        return Response({
            "success": True,
            "message": "Data retrieved successfully",
            "data": data,
            "pagination": {
                "count": self.count,
                "limit": self.limit,
                "offset": self.offset,
                "next": self.get_next_link(),
                "previous": self.get_previous_link()
            }
        })
```

**Usage:**
```
GET /api/tasks/?limit=20&offset=40
# Skip 40 records, get next 20
```

**Use Case:**
- "Load More" button
- Custom skip logic
- Data export (batch processing)

### B) CursorPagination (Large Datasets)

Best untuk social feeds, chat history, large datasets.

```python
# apps/core/pagination.py
from rest_framework.pagination import CursorPagination

class StandardCursorPagination(CursorPagination):
    page_size = 20
    ordering = '-created_at'  # Must have ordering!
    cursor_query_param = 'cursor'
    
    def get_paginated_response(self, data):
        return Response({
            "success": True,
            "message": "Data retrieved successfully",
            "data": data,
            "pagination": {
                "next": self.get_next_link(),
                "previous": self.get_previous_link()
            }
        })
```

**Usage:**
```
GET /api/tasks/
# Returns cursor in response

GET /api/tasks/?cursor=cD0yMDIzLTA5LTE1KzEzJTNBMjYlM0ExOC4zMjU4MjE%3D
# Get next page
```

**Benefits:**
- ✅ Performance: O(1) complexity (constant time)
- ✅ Scale: Works dengan 1M+ records
- ✅ Consistent: No duplicate/missing items saat data berubah

**Cons:**
- ❌ Can't jump to specific page (no page 5)
- ❌ Need `ordering` field dengan index

---

## 5️⃣ SENIOR LEVEL - Per-View Pagination

Different endpoints, different pagination.

```python
# apps/core/pagination.py

class SmallPagination(PageNumberPagination):
    """For simple lists"""
    page_size = 5

class MediumPagination(PageNumberPagination):
    """Default pagination"""
    page_size = 20

class LargePagination(PageNumberPagination):
    """For exports, admin"""
    page_size = 100
    max_page_size = 500
```

### Use in Views

```python
# apps/tasks/views.py
from apps.core.pagination import SmallPagination, MediumPagination

class TaskListView(APIView):
    pagination_class = MediumPagination
    
    def get(self, request):
        tasks = Task.objects.filter(user=request.user)
        
        paginator = self.pagination_class()
        paginated_tasks = paginator.paginate_queryset(tasks, request)
        serializer = TaskSerializer(paginated_tasks, many=True)
        
        return paginator.get_paginated_response(serializer.data)


class TaskHistoryView(APIView):
    pagination_class = SmallPagination  # Smaller page size
    
    def get(self, request):
        # ... same pattern
```

---

## 6️⃣ EXPERT LEVEL - Dynamic Pagination

User bisa pilih pagination type via query param.

```python
# apps/core/pagination.py
from rest_framework.pagination import PageNumberPagination, CursorPagination

class DynamicPagination:
    """
    Switch pagination type berdasarkan query param
    
    Usage:
        GET /api/tasks/?pagination=page&page=2
        GET /api/tasks/?pagination=cursor&cursor=abc123
    """
    
    def __init__(self):
        self.paginator = None
    
    def paginate_queryset(self, queryset, request, view=None):
        pagination_type = request.query_params.get('pagination', 'page')
        
        if pagination_type == 'cursor':
            self.paginator = StandardCursorPagination()
        else:
            self.paginator = StandardPagination()
        
        return self.paginator.paginate_queryset(queryset, request, view)
    
    def get_paginated_response(self, data):
        return self.paginator.get_paginated_response(data)
```

---

## 📊 Pagination Performance Comparison

| Type | Dataset | Query Time | Pros | Cons |
|------|---------|-----------|------|------|
| **Page Number** | < 100K | Fast | Simple, jump to page X | Slow for large datasets |
| **Limit Offset** | < 100K | Fast | Flexible skip | Slow dengan large offset |
| **Cursor** | 1M+ | Constant | Scalable, consistent | Can't jump pages |

### Query Complexity

```sql
-- Page Number (OFFSET grows)
SELECT * FROM tasks ORDER BY id LIMIT 10 OFFSET 10000;
-- Slow: Database scans 10,000 rows baru skip

-- Cursor (Use indexed WHERE)
SELECT * FROM tasks WHERE id > 10000 ORDER BY id LIMIT 10;
-- Fast: Database uses index directly
```

---

## 🎯 Best Practices

### 1. Always Set Max Page Size

```python
class StandardPagination(PageNumberPagination):
    page_size = 20
    max_page_size = 100  # Prevent ?page_size=99999999
```

### 2. Index Ordering Fields

```python
# models.py
class Task(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
        ]
```

### 3. Frontend Handling

```javascript
// React example
const [tasks, setTasks] = useState([]);
const [pagination, setPagination] = useState(null);

const fetchTasks = async (page = 1) => {
    const response = await fetch(`/api/tasks/?page=${page}`);
    const data = await response.json();
    
    setTasks(data.data);
    setPagination(data.pagination);
};

// Render pagination controls
{pagination?.next && (
    <button onClick={() => fetchTasks(pagination.current_page + 1)}>
        Next
    </button>
)}
```

### 4. Optimize Queries

```python
# ❌ Bad: N+1 query problem
class TaskSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username')
    # Each task makes separate query for user!

# ✅ Good: select_related
class TaskListView(APIView):
    def get(self, request):
        tasks = Task.objects.select_related('user').filter(user=request.user)
        # Single query dengan JOIN
```

---

## 📋 When to Use Which?

| Scenario | Recommended |
|----------|-------------|
| Admin dashboard, simple list | **PageNumberPagination** |
| "Load More" button | **LimitOffsetPagination** |
| Social feed, infinite scroll | **CursorPagination** |
| Large dataset (1M+ records) | **CursorPagination** |
| Data export | **LimitOffsetPagination** (large page size) |
| Search results | **PageNumberPagination** |

---

## 🚀 Recommended Setup

### For Most Apps (< 100K records)

```python
# config/settings/base.py
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'apps.core.pagination.StandardPagination',
    'PAGE_SIZE': 20
}
```

### For Large Scale Apps (1M+ records)

```python
# Different pagination per feature
class TaskListView(APIView):
    pagination_class = StandardCursorPagination  # For large datasets

class AdminTaskListView(APIView):
    pagination_class = StandardPagination  # Admin can jump pages
```

---

---

## 7️⃣ EXPERT LEVEL - Advanced Pagination Patterns

### A) Keyset Pagination (Faster than Cursor)

Keyset pagination menggunakan WHERE clause alih-alih OFFSET, sangat cepat untuk dataset besar.

```python
# apps/core/pagination.py
from rest_framework.pagination import BasePagination
from rest_framework.response import Response
from base64 import b64encode, b64decode
import json

class KeysetPagination(BasePagination):
    """
    Keyset-based pagination untuk dataset sangat besar (10M+ records)
    
    Prinsip:
    - Gunakan WHERE id > last_id alih-alih OFFSET
    - O(1) complexity, tidak peduli di page berapa
    """
    page_size = 20
    
    def paginate_queryset(self, queryset, request, view=None):
        self.request = request
        self.queryset = queryset
        
        # Decode cursor
        after_cursor = request.query_params.get('after')
        before_cursor = request.query_params.get('before')
        
        if after_cursor:
            # Decode: {"id": 123, "created_at": "2024-01-01"}
            decoded = json.loads(b64decode(after_cursor).decode())
            queryset = queryset.filter(
                id__gt=decoded['id']
            )
        elif before_cursor:
            decoded = json.loads(b64decode(before_cursor).decode())
            queryset = queryset.filter(
                id__lt=decoded['id']
            ).order_by('-id')
        
        # Get one extra to check has_next
        results = list(queryset[:self.page_size + 1])
        
        self.has_next = len(results) > self.page_size
        self.has_prev = bool(after_cursor)
        
        if self.has_next:
            results = results[:self.page_size]
        
        self.results = results
        return results
    
    def _encode_cursor(self, item):
        """Encode cursor dari object"""
        data = {
            'id': item.id,
            'created_at': str(item.created_at)
        }
        return b64encode(json.dumps(data).encode()).decode()
    
    def get_paginated_response(self, data):
        return Response({
            "success": True,
            "data": data,
            "pagination": {
                "has_next": self.has_next,
                "has_prev": self.has_prev,
                "next_cursor": self._encode_cursor(self.results[-1]) if self.has_next and self.results else None,
                "prev_cursor": self._encode_cursor(self.results[0]) if self.has_prev and self.results else None
            }
        })
```

### B) Composite Cursor (Multi-Field Sorting)

Untuk sorting dengan multiple fields (created_at DESC, id DESC).

```python
# apps/core/pagination.py
class CompositeCursorPagination(BasePagination):
    """
    Cursor pagination dengan composite key
    Untuk: ORDER BY created_at DESC, id DESC
    """
    page_size = 20
    ordering = ['-created_at', '-id']
    
    def paginate_queryset(self, queryset, request, view=None):
        self.request = request
        cursor = request.query_params.get('cursor')
        
        if cursor:
            decoded = json.loads(b64decode(cursor).decode())
            # Composite WHERE: created_at < X OR (created_at = X AND id < Y)
            from django.db.models import Q
            queryset = queryset.filter(
                Q(created_at__lt=decoded['created_at']) |
                Q(created_at=decoded['created_at'], id__lt=decoded['id'])
            )
        
        queryset = queryset.order_by('-created_at', '-id')
        results = list(queryset[:self.page_size + 1])
        
        self.has_next = len(results) > self.page_size
        if self.has_next:
            results = results[:self.page_size]
        
        self.results = results
        return results
    
    def _encode_cursor(self, item):
        return b64encode(json.dumps({
            'created_at': item.created_at.isoformat(),
            'id': item.id
        }).encode()).decode()
    
    def get_paginated_response(self, data):
        next_cursor = None
        if self.has_next and self.results:
            next_cursor = self._encode_cursor(self.results[-1])
        
        return Response({
            "success": True,
            "data": data,
            "pagination": {
                "next": next_cursor,
                "has_more": self.has_next
            }
        })
```

### C) Cached Pagination (Redis)

Cache pagination results untuk frequently accessed endpoints.

```python
# apps/core/pagination.py
from django.core.cache import cache
import hashlib

class CachedPagination(PageNumberPagination):
    """
    Cache paginated results di Redis
    
    Use case:
    - Homepage feed (accessed by many users)
    - Leaderboard (same for everyone)
    - Category listing
    """
    page_size = 20
    cache_timeout = 60  # 1 minute
    
    def paginate_queryset(self, queryset, request, view=None):
        # Generate cache key
        cache_key = self._get_cache_key(request, view)
        
        # Try cache first
        cached = cache.get(cache_key)
        if cached:
            self.page = cached['page']
            self.count = cached['count']
            return cached['data']
        
        # If not cached, paginate normally
        results = super().paginate_queryset(queryset, request, view)
        
        # Cache the results
        cache.set(cache_key, {
            'data': results,
            'page': self.page,
            'count': self.page.paginator.count
        }, self.cache_timeout)
        
        return results
    
    def _get_cache_key(self, request, view):
        """Generate unique cache key"""
        params = request.query_params.dict()
        params_str = json.dumps(params, sort_keys=True)
        hash_key = hashlib.md5(params_str.encode()).hexdigest()
        
        view_name = view.__class__.__name__ if view else 'unknown'
        return f"pagination:{view_name}:{hash_key}"
```

### D) Async Pagination (Django 4.1+)

Untuk async views dengan database async.

```python
# apps/core/pagination.py
from asgiref.sync import sync_to_async

class AsyncPagination(PageNumberPagination):
    """
    Async-compatible pagination untuk Django 4.1+ async views
    """
    
    async def apaginate_queryset(self, queryset, request, view=None):
        """Async version of paginate_queryset"""
        self.request = request
        
        page_number = request.query_params.get('page', 1)
        page_size = self.get_page_size(request)
        
        # Async count
        count = await queryset.acount()
        
        # Calculate offset
        offset = (int(page_number) - 1) * page_size
        
        # Async slice
        results = [item async for item in queryset[offset:offset + page_size]]
        
        self._count = count
        self._page_number = int(page_number)
        self._page_size = page_size
        
        return results
    
    def get_paginated_response(self, data):
        return Response({
            "success": True,
            "data": data,
            "pagination": {
                "count": self._count,
                "page": self._page_number,
                "page_size": self._page_size,
                "total_pages": (self._count + self._page_size - 1) // self._page_size
            }
        })


# Usage in async view
class AsyncTaskListView(APIView):
    async def get(self, request):
        queryset = Task.objects.filter(user=request.user)
        
        paginator = AsyncPagination()
        paginated = await paginator.apaginate_queryset(queryset, request)
        
        serializer = TaskSerializer(paginated, many=True)
        return paginator.get_paginated_response(serializer.data)
```

---

## 8️⃣ EXPERT LEVEL - Pagination Caching Strategies

### Strategy 1: Count Cache

Count query bisa slow untuk large tables. Cache it!

```python
# apps/core/pagination.py
class CachedCountPagination(PageNumberPagination):
    """
    Cache COUNT(*) query yang expensive
    """
    page_size = 20
    count_cache_timeout = 300  # 5 minutes
    
    def paginate_queryset(self, queryset, request, view=None):
        self.request = request
        
        # Get count from cache or database
        cache_key = f"count:{queryset.query}"
        count = cache.get(cache_key)
        
        if count is None:
            count = queryset.count()
            cache.set(cache_key, count, self.count_cache_timeout)
        
        # Store for response
        self._cached_count = count
        
        # Paginate
        page_number = request.query_params.get('page', 1)
        page_size = self.get_page_size(request)
        offset = (int(page_number) - 1) * page_size
        
        return list(queryset[offset:offset + page_size])
    
    def get_paginated_response(self, data):
        return Response({
            "success": True,
            "data": data,
            "pagination": {
                "count": self._cached_count,
                # ... rest
            }
        })
```

### Strategy 2: Infinite Scroll Optimization

```python
# apps/tasks/views.py
class InfiniteScrollTasksView(APIView):
    """
    Optimized for mobile infinite scroll
    
    Features:
    - Cursor-based (no duplicates)
    - Preload next batch
    - Include has_more flag
    """
    
    def get(self, request):
        queryset = Task.objects.filter(
            user=request.user
        ).select_related('user').prefetch_related('tags')
        
        cursor = request.query_params.get('cursor')
        limit = int(request.query_params.get('limit', 20))
        
        if cursor:
            # Decode cursor (id of last item)
            last_id = int(b64decode(cursor).decode())
            queryset = queryset.filter(id__lt=last_id)
        
        # Fetch limit + 1 to check has_more
        items = list(queryset.order_by('-id')[:limit + 1])
        has_more = len(items) > limit
        
        if has_more:
            items = items[:limit]
        
        serializer = TaskSerializer(items, many=True)
        
        return Response({
            "success": True,
            "data": serializer.data,
            "pagination": {
                "has_more": has_more,
                "next_cursor": b64encode(str(items[-1].id).encode()).decode() if items else None,
                "count": len(items)
            }
        })
```

---

## 9️⃣ Performance Optimization Deep Dive

### Index Strategy untuk Pagination

```python
# apps/tasks/models.py
class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            # Single column untuk simple ordering
            models.Index(fields=['-created_at']),
            
            # Composite untuk filtered + ordered queries
            # WHERE user_id = X ORDER BY created_at DESC
            models.Index(fields=['user', '-created_at']),
            
            # Untuk cursor pagination
            # WHERE id > X ORDER BY id
            models.Index(fields=['id']),
            
            # Untuk complex filtering
            # WHERE status = X AND user_id = Y ORDER BY created_at DESC
            models.Index(fields=['status', 'user', '-created_at']),
        ]


# Migration untuk covering index (PostgreSQL)
class Migration(migrations.Migration):
    operations = [
        migrations.RunSQL(
            # Covering index: includes all columns needed by query
            # Avoids table lookup
            sql="""
            CREATE INDEX task_list_covering ON tasks_task (
                user_id, created_at DESC
            ) INCLUDE (id, title, status);
            """,
            reverse_sql="DROP INDEX task_list_covering;"
        )
    ]
```

### Query Optimization

```python
# ❌ Bad: Multiple queries
class TaskListView(APIView):
    def get(self, request):
        tasks = Task.objects.filter(user=request.user)  # Query 1
        # Dalam serializer, akses task.user.name = Query per task!

# ✅ Good: Single optimized query
class TaskListView(APIView):
    def get(self, request):
        tasks = Task.objects.filter(
            user=request.user
        ).select_related(
            'user',          # FK relations
            'category'
        ).prefetch_related(
            'tags',          # M2M relations
            'comments',
            Prefetch(
                'attachments',
                queryset=Attachment.objects.only('id', 'filename')
            )
        ).only(              # Only needed fields
            'id', 'title', 'status', 'created_at',
            'user__username', 'category__name'
        ).order_by('-created_at')
        
        # Paginate optimized queryset
        paginator = StandardPagination()
        page = paginator.paginate_queryset(tasks, request)
        serializer = TaskSerializer(page, many=True)
        
        return paginator.get_paginated_response(serializer.data)
```

### Deferred Count (Skip count for infinite scroll)

```python
class NoCoundPagination(CursorPagination):
    """
    Pagination tanpa COUNT query
    Cocok untuk infinite scroll dimana total tidak penting
    """
    page_size = 20
    
    def get_paginated_response(self, data):
        return Response({
            "success": True,
            "data": data,
            "pagination": {
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                # No count - faster!
            }
        })
```

---

## 🔟 Frontend Integration Patterns

### React with React Query

```javascript
// hooks/useTasks.js
import { useInfiniteQuery } from '@tanstack/react-query';

export function useTasks() {
    return useInfiniteQuery({
        queryKey: ['tasks'],
        queryFn: async ({ pageParam = null }) => {
            const url = pageParam 
                ? `/api/tasks/?cursor=${pageParam}`
                : '/api/tasks/';
            
            const res = await fetch(url);
            return res.json();
        },
        getNextPageParam: (lastPage) => {
            return lastPage.pagination.next_cursor;
        },
        getPreviousPageParam: (firstPage) => {
            return firstPage.pagination.prev_cursor;
        }
    });
}

// components/TaskList.jsx
function TaskList() {
    const {
        data,
        fetchNextPage,
        hasNextPage,
        isFetchingNextPage
    } = useTasks();
    
    return (
        <div>
            {data?.pages.map(page =>
                page.data.map(task => (
                    <TaskCard key={task.id} task={task} />
                ))
            )}
            
            {hasNextPage && (
                <button 
                    onClick={() => fetchNextPage()}
                    disabled={isFetchingNextPage}
                >
                    {isFetchingNextPage ? 'Loading...' : 'Load More'}
                </button>
            )}
        </div>
    );
}
```

### Intersection Observer (Infinite Scroll)

```javascript
// hooks/useInfiniteScroll.js
import { useEffect, useRef, useCallback } from 'react';

export function useInfiniteScroll(callback, hasMore) {
    const observer = useRef();
    
    const lastElementRef = useCallback(node => {
        if (observer.current) observer.current.disconnect();
        
        observer.current = new IntersectionObserver(entries => {
            if (entries[0].isIntersecting && hasMore) {
                callback();
            }
        });
        
        if (node) observer.current.observe(node);
    }, [callback, hasMore]);
    
    return lastElementRef;
}

// Usage
function TaskList() {
    const { data, fetchNextPage, hasNextPage } = useTasks();
    const lastTaskRef = useInfiniteScroll(fetchNextPage, hasNextPage);
    
    return (
        <div>
            {data?.pages.map((page, i) =>
                page.data.map((task, j) => {
                    const isLast = i === data.pages.length - 1 && 
                                   j === page.data.length - 1;
                    return (
                        <div 
                            key={task.id} 
                            ref={isLast ? lastTaskRef : null}
                        >
                            <TaskCard task={task} />
                        </div>
                    );
                })
            )}
        </div>
    );
}
```

---

## 📚 Further Reading

- [DRF Pagination Docs](https://www.django-rest-framework.org/api-guide/pagination/)
- [Database Indexing Best Practices](https://use-the-index-luke.com/)
- [Cursor-based Pagination Deep Dive](https://www.sitepoint.com/paginating-real-time-data-cursor-based-pagination/)
- [Slack Engineering: Scaling Pagination](https://slack.engineering/)
- [PostgreSQL Index Types](https://www.postgresql.org/docs/current/indexes-types.html)

---

## 💡 Quick Tips

```python
# Tip 1: Disable pagination untuk specific endpoint
class AllTasksView(APIView):
    pagination_class = None  # Return all data

# Tip 2: Custom page size per request
# GET /api/tasks/?page=2&page_size=50

# Tip 3: Count total without fetching data
queryset.count()  # Fast

# Tip 4: Prefetch related data
Task.objects.prefetch_related('tags')  # For ManyToMany

# Tip 5: Estimated count untuk large tables
# Faster than COUNT(*) untuk estimation
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT reltuples::BIGINT 
        FROM pg_class 
        WHERE relname = 'tasks_task'
    """)
    estimated_count = cursor.fetchone()[0]

# Tip 6: Pagination info di headers (REST convention)
class HeaderPagination(PageNumberPagination):
    def get_paginated_response(self, data):
        response = Response(data)
        response['X-Total-Count'] = self.page.paginator.count
        response['X-Page'] = self.page.number
        response['X-Page-Size'] = self.page_size
        response['Link'] = self._get_link_header()
        return response
```

---

## 📋 Complete Pagination Checklist

### Junior ✅
- [ ] Implement basic PageNumberPagination
- [ ] Custom page size
- [ ] Consistent response schema

### Mid ✅  
- [ ] Choose right pagination type per use case
- [ ] LimitOffsetPagination untuk load more
- [ ] CursorPagination untuk infinite scroll

### Senior ✅
- [ ] Per-view pagination configuration
- [ ] Database index optimization
- [ ] select_related/prefetch_related

### Expert ✅
- [ ] Keyset pagination untuk 1M+ records
- [ ] Composite cursors untuk multi-field ordering
- [ ] Cached pagination dengan Redis
- [ ] Async pagination (Django 4.1+)
- [ ] Count cache strategy
- [ ] Covering indexes
- [ ] Frontend integration (React Query)
- [ ] Infinite scroll dengan Intersection Observer
