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

## 📚 Further Reading

- [DRF Pagination Docs](https://www.django-rest-framework.org/api-guide/pagination/)
- [Database Indexing Best Practices](https://use-the-index-luke.com/)
- [Cursor-based Pagination Deep Dive](https://www.sitepoint.com/paginating-real-time-data-cursor-based-pagination/)

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
```
