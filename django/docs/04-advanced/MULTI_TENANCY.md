# 🏢 MULTI-TENANCY - Django (Junior → Senior)

Dokumentasi lengkap tentang multi-tenancy di Django - satu aplikasi untuk banyak tenant/perusahaan.

---

## 🎯 Kenapa Multi-Tenancy Penting?

| Single Tenant | Multi-Tenant |
|--------------|--------------|
| 1 app = 1 customer | 1 app = banyak customer |
| Deploy berulang | Deploy sekali |
| Maintenance banyak instance | Maintenance 1 instance |
| Mahal | Cost efficient |

**Use Cases:**
- 🏢 **SaaS HR System** - Banyak perusahaan dalam 1 app
- 📊 **Project Management** - Banyak organization
- 🛒 **E-commerce Platform** - Banyak seller
- 📱 **White-label Apps** - Banyak brand

---

## 📊 Multi-Tenancy Strategies

| Strategy | Isolation | Complexity | Use Case |
|----------|-----------|------------|----------|
| **Shared Database, Shared Schema** | Low | Low | Simple apps |
| **Shared Database, Separate Schema** | Medium | Medium | PostgreSQL based |
| **Separate Database** | High | High | Enterprise, compliance |

---

## 1️⃣ JUNIOR LEVEL - Foreign Key Isolation

### Tenant Model

```python
# apps/tenants/models.py
from django.db import models
import uuid

class Tenant(models.Model):
    """
    Represents a company/organization
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    domain = models.CharField(max_length=255, unique=True, null=True, blank=True)
    
    # Subscription info
    plan = models.CharField(max_length=20, default='free')
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
```

### User dengan Tenant

```python
# apps/authentication/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        related_name='users'
    )
    
    # Role dalam tenant
    role = models.CharField(
        max_length=20,
        choices=[
            ('admin', 'Admin'),
            ('manager', 'Manager'),
            ('staff', 'Staff'),
        ],
        default='staff'
    )
```

### Tenant-Aware Models

```python
# apps/core/models.py
from django.db import models

class TenantModel(models.Model):
    """
    Abstract model that belongs to a tenant
    """
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='%(class)s_set'
    )
    
    class Meta:
        abstract = True


# apps/employees/models.py
from apps.core.models import TenantModel

class Employee(TenantModel):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    department = models.CharField(max_length=50)
    
    class Meta:
        # Unique per tenant, not globally
        unique_together = ['tenant', 'email']


class Department(TenantModel):
    name = models.CharField(max_length=50)
    
    class Meta:
        unique_together = ['tenant', 'name']
```

### Manual Filtering

```python
# apps/employees/views.py
from rest_framework import generics

class EmployeeListView(generics.ListAPIView):
    serializer_class = EmployeeSerializer
    
    def get_queryset(self):
        # Filter by user's tenant
        return Employee.objects.filter(
            tenant=self.request.user.tenant
        )
    
    def perform_create(self, serializer):
        # Auto-assign tenant
        serializer.save(tenant=self.request.user.tenant)
```

**Problem:** Harus selalu ingat filter by tenant di setiap query!

---

## 2️⃣ MID LEVEL - Automatic Tenant Filtering

### Tenant Middleware

```python
# apps/tenants/middleware.py
from django.utils.deprecation import MiddlewareMixin
from apps.tenants.models import Tenant

class TenantMiddleware(MiddlewareMixin):
    """
    Set current tenant based on:
    1. Subdomain (company.example.com)
    2. Header (X-Tenant-ID)
    3. User's tenant
    """
    
    def process_request(self, request):
        request.tenant = None
        
        # Option 1: From subdomain
        host = request.get_host().split(':')[0]
        subdomain = host.split('.')[0]
        
        if subdomain and subdomain != 'www':
            try:
                request.tenant = Tenant.objects.get(slug=subdomain)
                return
            except Tenant.DoesNotExist:
                pass
        
        # Option 2: From header
        tenant_id = request.headers.get('X-Tenant-ID')
        if tenant_id:
            try:
                request.tenant = Tenant.objects.get(id=tenant_id)
                return
            except Tenant.DoesNotExist:
                pass
        
        # Option 3: From authenticated user
        if hasattr(request, 'user') and request.user.is_authenticated:
            request.tenant = request.user.tenant


# settings.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.tenants.middleware.TenantMiddleware',  # After auth
    # ...
]
```

### Custom Manager dengan Auto-Filter

```python
# apps/core/models.py
from django.db import models
from threading import local

_thread_locals = local()

def get_current_tenant():
    """Get tenant from thread local storage"""
    return getattr(_thread_locals, 'tenant', None)

def set_current_tenant(tenant):
    """Set tenant in thread local storage"""
    _thread_locals.tenant = tenant


class TenantManager(models.Manager):
    """
    Manager that auto-filters by current tenant
    """
    
    def get_queryset(self):
        queryset = super().get_queryset()
        tenant = get_current_tenant()
        
        if tenant:
            return queryset.filter(tenant=tenant)
        return queryset
    
    def all_tenants(self):
        """Get objects from all tenants (admin use)"""
        return super().get_queryset()


class TenantModel(models.Model):
    """
    Abstract model with auto tenant filtering
    """
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='%(class)s_set'
    )
    
    objects = TenantManager()
    all_objects = models.Manager()  # For admin
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        # Auto-assign tenant if not set
        if not self.tenant_id:
            self.tenant = get_current_tenant()
        super().save(*args, **kwargs)
```

### Update Middleware untuk Thread Local

```python
# apps/tenants/middleware.py
from apps.core.models import set_current_tenant

class TenantMiddleware(MiddlewareMixin):
    def process_request(self, request):
        tenant = None
        
        # ... (tenant detection logic)
        
        request.tenant = tenant
        set_current_tenant(tenant)  # Store in thread local
    
    def process_response(self, request, response):
        # Clear tenant after request
        set_current_tenant(None)
        return response
```

### Now Queries Auto-Filter!

```python
# apps/employees/views.py
class EmployeeListView(generics.ListAPIView):
    serializer_class = EmployeeSerializer
    
    def get_queryset(self):
        # Auto-filtered by tenant!
        return Employee.objects.all()
    
    def perform_create(self, serializer):
        # Tenant auto-assigned in model.save()
        serializer.save()
```

---

## 3️⃣ MID-SENIOR LEVEL - PostgreSQL Schema Isolation

### django-tenants Package

```bash
pip install django-tenants
```

### Settings

```python
# config/settings/base.py
DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': 'mydb',
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

DATABASE_ROUTERS = ('django_tenants.routers.TenantSyncRouter',)

MIDDLEWARE = [
    'django_tenants.middleware.main.TenantMainMiddleware',
    # ... other middleware
]

# Shared apps (exist in public schema)
SHARED_APPS = [
    'django_tenants',
    'apps.tenants',
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.admin',
]

# Tenant apps (exist in each tenant schema)
TENANT_APPS = [
    'django.contrib.contenttypes',
    'apps.employees',
    'apps.projects',
    'apps.documents',
]

INSTALLED_APPS = list(SHARED_APPS) + [
    app for app in TENANT_APPS if app not in SHARED_APPS
]

TENANT_MODEL = 'tenants.Tenant'
TENANT_DOMAIN_MODEL = 'tenants.Domain'
```

### Tenant Models

```python
# apps/tenants/models.py
from django.db import models
from django_tenants.models import TenantMixin, DomainMixin

class Tenant(TenantMixin):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Schema will be auto-created
    auto_create_schema = True
    
    def __str__(self):
        return self.name


class Domain(DomainMixin):
    pass


# Usage:
# tenant1.example.com -> uses schema 'tenant1'
# tenant2.example.com -> uses schema 'tenant2'
```

### Create Tenant

```python
# Create tenant
from apps.tenants.models import Tenant, Domain

tenant = Tenant(
    schema_name='company_abc',
    name='Company ABC'
)
tenant.save()  # Creates PostgreSQL schema 'company_abc'

# Add domain
domain = Domain(
    domain='abc.example.com',
    tenant=tenant,
    is_primary=True
)
domain.save()
```

### Accessing Different Schemas

```python
from django_tenants.utils import schema_context, tenant_context

# Execute in specific schema
with schema_context('company_abc'):
    employees = Employee.objects.all()  # From company_abc schema

# Execute in public schema
with schema_context('public'):
    tenants = Tenant.objects.all()

# Using tenant object
with tenant_context(tenant):
    # All queries go to tenant's schema
    Employee.objects.create(name='John')
```

---

## 4️⃣ SENIOR LEVEL - Complete Multi-Tenant Architecture

### Tenant-Aware Permissions

```python
# apps/tenants/permissions.py
from rest_framework import permissions

class IsTenantMember(permissions.BasePermission):
    """
    Only allow access to own tenant's data
    """
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.tenant is not None and
            request.user.tenant_id == request.tenant.id
        )


class IsTenantAdmin(permissions.BasePermission):
    """
    Only tenant admins can access
    """
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.tenant_id == request.tenant.id and
            request.user.role == 'admin'
        )


class CanAccessTenant(permissions.BasePermission):
    """
    For super admins who can access any tenant
    """
    
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        
        return (
            request.user.is_authenticated and
            request.user.tenant_id == request.tenant.id
        )
```

### Tenant Switching (Super Admin)

```python
# apps/tenants/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser

class SwitchTenantView(APIView):
    """
    Allow super admin to switch tenant context
    """
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        tenant_id = request.data.get('tenant_id')
        
        try:
            tenant = Tenant.objects.get(id=tenant_id)
            
            # Store in session
            request.session['admin_tenant_id'] = str(tenant.id)
            
            return Response({
                'success': True,
                'tenant': TenantSerializer(tenant).data
            })
        except Tenant.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Tenant not found'
            }, status=404)
```

### Tenant-Aware File Storage

```python
# apps/core/storage.py
from django.core.files.storage import FileSystemStorage
from storages.backends.s3boto3 import S3Boto3Storage
from apps.core.models import get_current_tenant

class TenantFileStorage(FileSystemStorage):
    """
    Store files in tenant-specific directories
    """
    
    def get_available_name(self, name, max_length=None):
        tenant = get_current_tenant()
        if tenant:
            name = f'tenants/{tenant.slug}/{name}'
        return super().get_available_name(name, max_length)


class TenantS3Storage(S3Boto3Storage):
    """
    Store files in tenant-specific S3 prefixes
    """
    
    def _save(self, name, content):
        tenant = get_current_tenant()
        if tenant:
            name = f'tenants/{tenant.slug}/{name}'
        return super()._save(name, content)
```

### Tenant-Aware Celery Tasks

```python
# apps/core/tasks.py
from celery import shared_task
from apps.core.models import set_current_tenant
from apps.tenants.models import Tenant

class TenantTask:
    """
    Base class for tenant-aware tasks
    """
    
    def __call__(self, tenant_id, *args, **kwargs):
        # Set tenant context
        tenant = Tenant.objects.get(id=tenant_id)
        set_current_tenant(tenant)
        
        try:
            return self.run(*args, **kwargs)
        finally:
            set_current_tenant(None)


@shared_task(bind=True, base=TenantTask)
def generate_report(self, report_type):
    """
    Task runs in tenant context
    """
    # Queries auto-filtered by tenant
    employees = Employee.objects.all()
    # ...
```

### Tenant Quotas & Limits

```python
# apps/tenants/models.py
class TenantPlan(models.Model):
    name = models.CharField(max_length=50)
    max_users = models.IntegerField(default=10)
    max_storage_gb = models.IntegerField(default=5)
    max_projects = models.IntegerField(default=10)
    features = models.JSONField(default=dict)


class Tenant(TenantMixin):
    name = models.CharField(max_length=100)
    plan = models.ForeignKey(TenantPlan, on_delete=models.PROTECT)
    
    def can_add_user(self):
        return self.users.count() < self.plan.max_users
    
    def can_add_project(self):
        return self.project_set.count() < self.plan.max_projects
    
    def storage_used_gb(self):
        from django.db.models import Sum
        return (self.file_set.aggregate(Sum('size'))['size__sum'] or 0) / (1024**3)
    
    def can_upload_file(self, size_bytes):
        used = self.storage_used_gb()
        new_size = size_bytes / (1024**3)
        return (used + new_size) <= self.plan.max_storage_gb


# apps/employees/views.py
class EmployeeCreateView(generics.CreateAPIView):
    def perform_create(self, serializer):
        tenant = self.request.tenant
        
        if not tenant.can_add_user():
            raise ValidationError({
                'error': 'User limit reached. Please upgrade your plan.'
            })
        
        serializer.save()
```

### Tenant Data Export

```python
# apps/tenants/services.py
import json
from django.apps import apps

class TenantExportService:
    """
    Export all tenant data (for backup/migration)
    """
    
    def export_tenant(self, tenant):
        from apps.core.models import set_current_tenant
        set_current_tenant(tenant)
        
        data = {'tenant': tenant.slug, 'models': {}}
        
        # Get all tenant models
        for model in apps.get_models():
            if hasattr(model, 'tenant'):
                model_name = model.__name__
                objects = list(model.objects.values())
                data['models'][model_name] = objects
        
        set_current_tenant(None)
        return data
    
    def import_tenant(self, tenant, data):
        """Import data to tenant"""
        from apps.core.models import set_current_tenant
        set_current_tenant(tenant)
        
        for model_name, objects in data['models'].items():
            Model = apps.get_model('app_name', model_name)
            for obj_data in objects:
                Model.objects.create(**obj_data)
        
        set_current_tenant(None)
```

---

## 📊 Architecture Comparison

```
Strategy 1: Shared Schema (FK Isolation)
├── Database: myapp_db
│   └── Tables:
│       ├── tenants (id, name, ...)
│       ├── employees (id, tenant_id, ...)
│       └── projects (id, tenant_id, ...)


Strategy 2: Separate Schema (PostgreSQL)
├── Database: myapp_db
│   ├── Schema: public
│   │   └── Tables: tenants, users
│   ├── Schema: company_a
│   │   └── Tables: employees, projects
│   └── Schema: company_b
│       └── Tables: employees, projects


Strategy 3: Separate Database
├── Database: myapp_shared
│   └── Tables: tenants, billing
├── Database: company_a
│   └── Tables: employees, projects
└── Database: company_b
    └── Tables: employees, projects
```

---

## ✅ Checklist Implementasi

| Level | Fitur | Status |
|-------|-------|--------|
| Junior | Tenant model | ⬜ |
| Junior | FK-based isolation | ⬜ |
| Mid | Tenant middleware | ⬜ |
| Mid | Auto-filtering manager | ⬜ |
| Senior | Schema isolation | ⬜ |
| Senior | Tenant permissions | ⬜ |
| Senior | Quotas & limits | ⬜ |
| Senior | Tenant-aware tasks | ⬜ |

---

## 🔗 Referensi

- [django-tenants](https://github.com/django-tenants/django-tenants)
- [Multi-Tenancy Patterns](https://docs.microsoft.com/en-us/azure/sql-database/saas-tenancy-app-design-patterns)
