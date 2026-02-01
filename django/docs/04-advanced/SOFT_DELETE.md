# 🗑️ SOFT DELETE - Django (Junior → Senior)

Dokumentasi lengkap tentang soft delete di Django - data tidak benar-benar dihapus dari database.

---

## 🎯 Kenapa Soft Delete Penting?

| Hard Delete | Soft Delete |
|-------------|-------------|
| Data hilang permanen | Data bisa di-restore |
| Tidak ada audit trail | Audit trail lengkap |
| FK constraint issues | Relasi tetap intact |
| Tidak cocok untuk HR/Finance | Wajib untuk data sensitif |

**Use Cases:**
- 📋 **HR System** - Data karyawan tidak boleh hilang
- 💰 **Finance** - Transaksi harus ada jejak
- 📝 **Audit** - Compliance requirements
- 🔄 **Recovery** - User bisa undo delete

---

## 1️⃣ JUNIOR LEVEL - Simple is_deleted Field

### Model dengan is_deleted

```python
# apps/core/models.py
from django.db import models
from django.utils import timezone

class SoftDeleteModel(models.Model):
    """
    Abstract model dengan soft delete support
    """
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        abstract = True
    
    def delete(self, using=None, keep_parents=False):
        """Override delete untuk soft delete"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])
    
    def hard_delete(self):
        """Permanently delete dari database"""
        super().delete()
    
    def restore(self):
        """Restore soft-deleted object"""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])
```

### Contoh Penggunaan

```python
# apps/employees/models.py
from apps.core.models import SoftDeleteModel

class Employee(SoftDeleteModel):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    department = models.CharField(max_length=50)
    hired_at = models.DateField()
    
    def __str__(self):
        return self.name


# Usage
employee = Employee.objects.get(id=1)

# Soft delete (is_deleted = True)
employee.delete()

# Restore
employee.restore()

# Permanent delete
employee.hard_delete()
```

### Query Manual

```python
# Get active employees only
active_employees = Employee.objects.filter(is_deleted=False)

# Get deleted employees
deleted_employees = Employee.objects.filter(is_deleted=True)

# Get all (including deleted)
all_employees = Employee.objects.all()
```

**Problem:** Harus selalu ingat menambahkan `.filter(is_deleted=False)`

---

## 2️⃣ MID LEVEL - Custom Manager & QuerySet

### Custom Manager

```python
# apps/core/models.py
from django.db import models
from django.utils import timezone

class SoftDeleteQuerySet(models.QuerySet):
    """QuerySet yang exclude deleted objects by default"""
    
    def delete(self):
        """Bulk soft delete"""
        return self.update(is_deleted=True, deleted_at=timezone.now())
    
    def hard_delete(self):
        """Bulk permanent delete"""
        return super().delete()
    
    def restore(self):
        """Bulk restore"""
        return self.update(is_deleted=False, deleted_at=None)
    
    def alive(self):
        """Get only non-deleted objects"""
        return self.filter(is_deleted=False)
    
    def dead(self):
        """Get only deleted objects"""
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager):
    """Manager yang exclude deleted objects by default"""
    
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).alive()
    
    def all_with_deleted(self):
        """Include deleted objects"""
        return SoftDeleteQuerySet(self.model, using=self._db)
    
    def only_deleted(self):
        """Get only deleted objects"""
        return SoftDeleteQuerySet(self.model, using=self._db).dead()


class SoftDeleteModel(models.Model):
    """Abstract model dengan soft delete"""
    
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='%(class)s_deleted'
    )
    
    # Custom managers
    objects = SoftDeleteManager()
    all_objects = models.Manager()  # Include deleted
    
    class Meta:
        abstract = True
    
    def delete(self, using=None, keep_parents=False, user=None):
        """Soft delete dengan optional user tracking"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save()
    
    def hard_delete(self):
        """Permanent delete"""
        super().delete()
    
    def restore(self):
        """Restore soft-deleted object"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save()
```

### Usage dengan Custom Manager

```python
# apps/employees/models.py
class Employee(SoftDeleteModel):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    
    class Meta:
        ordering = ['name']


# Query active employees (automatic!)
employees = Employee.objects.all()  # Only non-deleted

# Query termasuk deleted
all_employees = Employee.objects.all_with_deleted()

# Query hanya deleted
deleted = Employee.objects.only_deleted()

# Bulk operations
Employee.objects.filter(department='Sales').delete()  # Soft delete all
Employee.objects.only_deleted().restore()  # Restore all deleted
```

---

## 3️⃣ MID-SENIOR LEVEL - Cascade Soft Delete

### Problem: Related Objects

```python
class Department(SoftDeleteModel):
    name = models.CharField(max_length=100)

class Employee(SoftDeleteModel):
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
```

Ketika Department di-soft-delete, Employee tidak ikut soft-delete.

### Solution: Cascade Soft Delete

```python
# apps/core/models.py
class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    objects = SoftDeleteManager()
    all_objects = models.Manager()
    
    class Meta:
        abstract = True
    
    def delete(self, using=None, keep_parents=False, cascade=True, user=None):
        """
        Soft delete dengan cascade ke related objects
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
        
        if cascade:
            self._cascade_soft_delete(user)
    
    def _cascade_soft_delete(self, user=None):
        """
        Soft delete semua related objects
        """
        # Get all related objects
        for related in self._meta.related_objects:
            if hasattr(related.related_model, 'is_deleted'):
                related_name = related.get_accessor_name()
                related_manager = getattr(self, related_name, None)
                
                if related_manager:
                    # Soft delete related objects
                    for obj in related_manager.all():
                        obj.delete(cascade=True, user=user)
    
    def restore(self, cascade=True):
        """
        Restore dengan optional cascade
        """
        self.is_deleted = False
        self.deleted_at = None
        self.save()
        
        if cascade:
            self._cascade_restore()
    
    def _cascade_restore(self):
        """
        Restore semua related objects
        """
        for related in self._meta.related_objects:
            if hasattr(related.related_model, 'is_deleted'):
                related_name = related.get_accessor_name()
                related_manager = getattr(self, related_name, None)
                
                if related_manager:
                    # Use all_objects to get deleted items
                    for obj in related_manager.model.all_objects.filter(
                        **{related.field.name: self}
                    ).dead():
                        obj.restore(cascade=True)
```

### Usage

```python
# Delete department dan cascade ke employees
department = Department.objects.get(id=1)
department.delete(cascade=True)

# Employees di department ini juga ter-soft-delete

# Restore semuanya
department.restore(cascade=True)
```

---

## 4️⃣ SENIOR LEVEL - Complete Implementation

### Full SoftDelete Mixin

```python
# apps/core/mixins/soft_delete.py
from django.db import models
from django.utils import timezone
from django.db.models.signals import pre_delete
import uuid

class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        return self.update(is_deleted=True, deleted_at=timezone.now())
    
    def hard_delete(self):
        return super().delete()
    
    def restore(self):
        return self.update(is_deleted=False, deleted_at=None, deleted_by=None)
    
    def alive(self):
        return self.filter(is_deleted=False)
    
    def dead(self):
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager):
    _queryset_class = SoftDeleteQuerySet
    
    def get_queryset(self):
        return super().get_queryset().alive()
    
    def all_with_deleted(self):
        return super().get_queryset()
    
    def only_deleted(self):
        return super().get_queryset().dead()
    
    def restore(self, *args, **kwargs):
        return self.all_with_deleted().restore(*args, **kwargs)


class SoftDeleteMixin(models.Model):
    """
    Mixin untuk soft delete dengan fitur lengkap
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    deleted_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+'
    )
    
    objects = SoftDeleteManager()
    all_objects = models.Manager()
    
    class Meta:
        abstract = True
    
    def delete(self, using=None, keep_parents=False, user=None, hard=False):
        if hard:
            return super().delete(using=using, keep_parents=keep_parents)
        
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])
        
        # Send signal
        from django.db.models.signals import post_save
        post_save.send(sender=self.__class__, instance=self, soft_deleted=True)
    
    def restore(self, user=None):
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])
        
        # Send signal
        from django.db.models.signals import post_save
        post_save.send(sender=self.__class__, instance=self, restored=True)
    
    @classmethod
    def get_deleted_before(cls, days):
        """Get objects deleted more than X days ago"""
        threshold = timezone.now() - timezone.timedelta(days=days)
        return cls.all_objects.filter(
            is_deleted=True,
            deleted_at__lt=threshold
        )
```

### View dengan Soft Delete

```python
# apps/employees/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

class EmployeeViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeSerializer
    
    def get_queryset(self):
        """By default, return active employees only"""
        if self.action == 'deleted':
            return Employee.objects.only_deleted()
        if self.action == 'all_records':
            return Employee.all_objects.all()
        return Employee.objects.all()
    
    def perform_destroy(self, instance):
        """Soft delete instead of hard delete"""
        instance.delete(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def deleted(self, request):
        """GET /api/employees/deleted/ - List deleted employees"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """POST /api/employees/{id}/restore/ - Restore employee"""
        try:
            employee = Employee.all_objects.get(pk=pk, is_deleted=True)
            employee.restore()
            return Response({
                'success': True,
                'message': 'Employee restored successfully'
            })
        except Employee.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Deleted employee not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['delete'])
    def permanent_delete(self, request, pk=None):
        """DELETE /api/employees/{id}/permanent/ - Hard delete"""
        try:
            employee = Employee.all_objects.get(pk=pk)
            employee.delete(hard=True)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Employee.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


# URLs
# GET    /api/employees/           → List active
# GET    /api/employees/deleted/   → List deleted
# DELETE /api/employees/{id}/      → Soft delete
# POST   /api/employees/{id}/restore/   → Restore
# DELETE /api/employees/{id}/permanent/ → Hard delete
```

### Cleanup Task

```python
# apps/core/tasks.py
from celery import shared_task
from django.apps import apps

@shared_task
def cleanup_old_deleted_records():
    """
    Permanently delete records yang sudah di-soft-delete
    lebih dari 90 hari (data retention policy)
    """
    from django.utils import timezone
    
    threshold = timezone.now() - timezone.timedelta(days=90)
    
    # Get all models with soft delete
    for model in apps.get_models():
        if hasattr(model, 'is_deleted') and hasattr(model, 'deleted_at'):
            count, _ = model.all_objects.filter(
                is_deleted=True,
                deleted_at__lt=threshold
            ).delete()
            
            if count > 0:
                print(f"Permanently deleted {count} {model.__name__} records")
```

---

## 📦 Using django-safedelete (Package)

Jika tidak mau implement sendiri:

```bash
pip install django-safedelete
```

```python
# settings.py
INSTALLED_APPS = [
    'safedelete',
    ...
]

# models.py
from safedelete.models import SafeDeleteModel
from safedelete import SOFT_DELETE_CASCADE

class Employee(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE
    
    name = models.CharField(max_length=100)
    department = models.ForeignKey('Department', on_delete=models.CASCADE)
```

---

## ✅ Checklist Implementasi

| Level | Fitur | Status |
|-------|-------|--------|
| Junior | is_deleted field | ⬜ |
| Junior | Override delete() | ⬜ |
| Mid | Custom Manager | ⬜ |
| Mid | Custom QuerySet | ⬜ |
| Senior | Cascade soft delete | ⬜ |
| Senior | Restore functionality | ⬜ |
| Senior | Cleanup task | ⬜ |
| Senior | Admin integration | ⬜ |

---

## 🔗 Referensi

- [django-safedelete](https://github.com/makinacorpus/django-safedelete)
- [BACKGROUND_JOBS.md](BACKGROUND_JOBS.md) - Untuk cleanup task
