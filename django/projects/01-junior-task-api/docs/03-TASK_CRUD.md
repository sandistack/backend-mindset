# 📝 Step 3: Task CRUD API

**Waktu:** 4-6 jam  
**Prerequisite:** Step 2 selesai (Authentication berfungsi)

---

## 🎯 Tujuan

- Membuat Task & Category models
- Implementasi full CRUD operations
- Owner-based permissions
- Soft delete pattern

---

## 📋 Tasks

### 3.1 Task & Category Models

**Di `apps/tasks/models.py`:**

#### Category Model
```
Fields:
- id (auto)
- name (CharField, max_length=100)
- color (CharField, max_length=7, default="#3B82F6")  # hex color
- user (ForeignKey to User)
- created_at (DateTimeField, auto_now_add)

Meta:
- unique_together = ['name', 'user']  # User tidak boleh punya category dengan nama sama
```

#### Task Model
```
Fields:
- id (auto)
- user (ForeignKey to User, related_name='tasks')
- category (ForeignKey to Category, null=True, blank=True)
- title (CharField, max_length=255)
- description (TextField, blank=True)
- priority (CharField, choices=['low', 'medium', 'high'], default='medium')
- status (CharField, choices=['pending', 'in_progress', 'done'], default='pending')
- due_date (DateTimeField, null=True, blank=True)
- completed_at (DateTimeField, null=True, blank=True)
- is_deleted (BooleanField, default=False)  # Soft delete
- created_at (DateTimeField, auto_now_add)
- updated_at (DateTimeField, auto_now)

Methods:
- mark_complete(): Set status='done', completed_at=now
- soft_delete(): Set is_deleted=True
- restore(): Set is_deleted=False
```

**Manager untuk Soft Delete:**

Buat custom manager untuk exclude deleted tasks by default:

```python
class TaskManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class Task(models.Model):
    # ... fields ...
    
    objects = TaskManager()  # Default: exclude deleted
    all_objects = models.Manager()  # Include deleted
```

---

### 3.2 Task Serializers

**Di `apps/tasks/serializers.py`:**

#### CategorySerializer
- Fields: id, name, color, created_at
- Validate name tidak duplicate per user

#### TaskSerializer (untuk Read)
- Fields: id, title, description, priority, status, due_date, completed_at, category, created_at, updated_at
- Nested CategorySerializer untuk category
- Read-only: id, created_at, updated_at, completed_at

#### TaskCreateUpdateSerializer (untuk Write)
- Fields: title, description, priority, status, due_date, category
- Validate due_date tidak boleh di masa lalu (untuk create)
- Category harus milik user yang sama

**Referensi:** [SERIALIZERS.md](../../../docs/02-database/SERIALIZERS.md)

---

### 3.3 Custom Permissions

**Di `apps/core/permissions.py`:**

Buat permission class:

```python
class IsOwner(BasePermission):
    """
    Object-level permission: hanya owner yang bisa akses
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
```

---

### 3.4 Task Views

**Di `apps/tasks/views.py`:**

Gunakan ViewSets untuk CRUD yang clean:

#### CategoryViewSet (ModelViewSet)
- queryset: Filter by current user
- serializer_class: CategorySerializer
- permission_classes: [IsAuthenticated, IsOwner]
- Override `perform_create()` untuk set user otomatis

#### TaskViewSet (ModelViewSet)
- queryset: Filter by current user (dan is_deleted=False)
- Gunakan serializer berbeda untuk read vs write
- permission_classes: [IsAuthenticated, IsOwner]

Custom Actions:
```python
@action(detail=True, methods=['post'])
def complete(self, request, pk=None):
    """Mark task as complete"""
    task = self.get_object()
    task.mark_complete()
    return Response(TaskSerializer(task).data)

@action(detail=True, methods=['post'])
def restore(self, request, pk=None):
    """Restore soft-deleted task"""
    # Perlu override get_queryset untuk include deleted
    task = Task.all_objects.get(pk=pk, user=request.user)
    task.restore()
    return Response(TaskSerializer(task).data)
```

**Override destroy() untuk soft delete:**
```python
def destroy(self, request, *args, **kwargs):
    task = self.get_object()
    task.soft_delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
```

---

### 3.5 URLs dengan Router

**Di `apps/tasks/urls.py`:**

```python
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('tasks', TaskViewSet, basename='task')
router.register('categories', CategoryViewSet, basename='category')

urlpatterns = router.urls
```

**Di `config/urls.py`:**

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.authentication.urls')),
    path('api/', include('apps.tasks.urls')),
]
```

---

## 📊 API Endpoints yang Dihasilkan

```
Tasks:
GET    /api/tasks/              # List user's tasks
POST   /api/tasks/              # Create task
GET    /api/tasks/{id}/         # Get task detail
PUT    /api/tasks/{id}/         # Full update
PATCH  /api/tasks/{id}/         # Partial update
DELETE /api/tasks/{id}/         # Soft delete
POST   /api/tasks/{id}/complete/  # Mark complete
POST   /api/tasks/{id}/restore/   # Restore deleted

Categories:
GET    /api/categories/         # List user's categories
POST   /api/categories/         # Create category
GET    /api/categories/{id}/    # Get category detail
PUT    /api/categories/{id}/    # Update
DELETE /api/categories/{id}/    # Delete
```

---

## ✅ Checklist

- [ ] Category model & migrations
- [ ] Task model dengan soft delete
- [ ] Custom TaskManager untuk exclude deleted
- [ ] TaskSerializer read/write terpisah
- [ ] CategorySerializer dengan validation
- [ ] IsOwner permission class
- [ ] TaskViewSet dengan semua CRUD
- [ ] CategoryViewSet dengan CRUD
- [ ] Custom action: complete
- [ ] Custom action: restore
- [ ] Soft delete berfungsi
- [ ] User hanya lihat task/category sendiri

---

## 🧪 Testing Manual

```bash
# Create category
curl -X POST http://localhost:8000/api/categories/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Work", "color": "#EF4444"}'

# Create task
curl -X POST http://localhost:8000/api/tasks/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Complete project", "priority": "high", "category": 1}'

# List tasks
curl http://localhost:8000/api/tasks/ \
  -H "Authorization: Bearer <token>"

# Complete task
curl -X POST http://localhost:8000/api/tasks/1/complete/ \
  -H "Authorization: Bearer <token>"

# Delete task (soft)
curl -X DELETE http://localhost:8000/api/tasks/1/ \
  -H "Authorization: Bearer <token>"
```

---

## 🔗 Referensi

- [SERIALIZERS.md](../../../docs/02-database/SERIALIZERS.md) - Nested serializers
- [ARCHITECTURE.md](../../../docs/01-fundamentals/ARCHITECTURE.md) - ViewSet patterns
- [RESPONSE_SCHEMA.md](../../../docs/01-fundamentals/RESPONSE_SCHEMA.md) - Response format

---

## ➡️ Next Step

Lanjut ke [04-FILTERING_PAGINATION.md](04-FILTERING_PAGINATION.md) - Filter, Search & Pagination
