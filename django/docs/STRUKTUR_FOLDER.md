# 📁 STRUKTUR FOLDER - Django Project Structure

Best practices untuk mengorganisir project Django dari small hingga large scale.

---

## 🎯 Overview

```
Django menggunakan konsep "apps" untuk modularisasi.
Setiap app bertanggung jawab untuk satu domain/fitur tertentu.
```

---

## 1️⃣ SMALL PROJECT (Monolith Simple)

Untuk project kecil dengan 1-3 apps:

```
my_project/
├── manage.py
├── requirements.txt
├── .env
├── .gitignore
├── README.md
│
├── config/                     # Project configuration
│   ├── __init__.py
│   ├── settings.py             # Single settings file
│   ├── urls.py                 # Root URL configuration
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/                       # All Django apps
│   ├── __init__.py
│   ├── users/                  # User management
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── serializers.py      # DRF serializers
│   │   └── tests.py
│   │
│   └── core/                   # Shared utilities
│       ├── __init__.py
│       ├── models.py           # Base models
│       └── utils.py
│
├── static/                     # Static files
│   ├── css/
│   ├── js/
│   └── images/
│
├── templates/                  # HTML templates (jika ada)
│   └── base.html
│
└── media/                      # User uploaded files
```

---

## 2️⃣ MEDIUM PROJECT (Standard)

Untuk project dengan 4-10 apps:

```
my_project/
├── manage.py
├── requirements/               # Split requirements
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── .env.example
├── .gitignore
├── README.md
├── Makefile                    # Common commands
├── docker-compose.yml
├── Dockerfile
│
├── config/                     # Project configuration
│   ├── __init__.py
│   ├── settings/               # Split settings
│   │   ├── __init__.py
│   │   ├── base.py             # Common settings
│   │   ├── development.py
│   │   ├── production.py
│   │   └── test.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/
│   ├── __init__.py
│   │
│   ├── authentication/         # Auth & registration
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── serializers.py
│   │   ├── services.py         # Business logic
│   │   ├── permissions.py      # Custom permissions
│   │   ├── signals.py          # Django signals
│   │   ├── tasks.py            # Celery tasks
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   ├── test_models.py
│   │   │   ├── test_views.py
│   │   │   └── test_services.py
│   │   └── migrations/
│   │
│   ├── users/
│   │   ├── ... (same structure)
│   │
│   ├── products/
│   │   ├── ... (same structure)
│   │
│   ├── orders/
│   │   ├── ... (same structure)
│   │
│   └── core/                   # Shared components
│       ├── __init__.py
│       ├── models.py           # Abstract base models
│       ├── permissions.py      # Shared permissions
│       ├── pagination.py       # Custom pagination
│       ├── exceptions.py       # Custom exceptions
│       ├── middleware.py       # Custom middleware
│       └── utils/
│           ├── __init__.py
│           ├── helpers.py
│           └── validators.py
│
├── static/
├── templates/
├── media/
├── logs/
│
└── docs/                       # Documentation
    ├── api/
    └── guides/
```

---

## 3️⃣ LARGE PROJECT (Enterprise)

Untuk project dengan 10+ apps dan tim besar:

```
my_project/
├── manage.py
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   ├── production.txt
│   └── test.txt
├── .env.example
├── .gitignore
├── README.md
├── Makefile
├── docker-compose.yml
├── docker-compose.prod.yml
├── Dockerfile
├── pytest.ini
├── setup.cfg                   # Linting config
├── pyproject.toml
│
├── config/
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── production.py
│   │   ├── staging.py
│   │   └── test.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── celery.py               # Celery configuration
│
├── apps/
│   │
│   ├── accounts/               # Domain: User accounts
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── constants.py        # App constants
│   │   ├── models/             # Split models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   └── profile.py
│   │   ├── api/                # API layer
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── urls.py
│   │   │   │   ├── views.py
│   │   │   │   └── serializers.py
│   │   │   └── v2/             # API versioning
│   │   │       └── ...
│   │   ├── services/           # Business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── user_service.py
│   │   │   └── auth_service.py
│   │   ├── selectors/          # Query layer (read)
│   │   │   ├── __init__.py
│   │   │   └── user_selectors.py
│   │   ├── repositories/       # Data access layer
│   │   │   ├── __init__.py
│   │   │   └── user_repository.py
│   │   ├── permissions.py
│   │   ├── signals.py
│   │   ├── tasks.py
│   │   ├── exceptions.py
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   ├── factories.py    # Test factories
│   │   │   ├── fixtures.py     # Test fixtures
│   │   │   ├── unit/
│   │   │   │   ├── test_models.py
│   │   │   │   └── test_services.py
│   │   │   └── integration/
│   │   │       └── test_api.py
│   │   └── migrations/
│   │
│   ├── products/
│   │   └── ... (same structure)
│   │
│   ├── orders/
│   │   └── ... (same structure)
│   │
│   ├── payments/
│   │   └── ... (same structure)
│   │
│   ├── notifications/
│   │   └── ... (same structure)
│   │
│   └── core/                   # Shared core
│       ├── __init__.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── base.py         # TimeStampedModel, etc.
│       │   └── mixins.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── pagination.py
│       │   ├── permissions.py
│       │   ├── throttling.py
│       │   └── exceptions.py
│       ├── services/
│       │   ├── __init__.py
│       │   └── base.py
│       ├── middleware/
│       │   ├── __init__.py
│       │   ├── logging.py
│       │   └── audit.py
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── helpers.py
│       │   ├── validators.py
│       │   └── decorators.py
│       └── management/
│           └── commands/
│               └── custom_command.py
│
├── static/
├── templates/
├── media/
├── logs/
│
├── scripts/                    # Utility scripts
│   ├── deploy.sh
│   └── backup.sh
│
├── docs/
│   ├── api/
│   ├── architecture/
│   └── deployment/
│
└── .github/                    # CI/CD
    └── workflows/
        ├── ci.yml
        └── deploy.yml
```

---

## 4️⃣ APP INTERNAL STRUCTURE

### Standard App Structure

```
my_app/
├── __init__.py
├── admin.py                    # Django admin config
├── apps.py                     # App configuration
├── models.py                   # Database models
├── views.py                    # Views/ViewSets
├── urls.py                     # URL patterns
├── serializers.py              # DRF serializers
├── services.py                 # Business logic
├── permissions.py              # Custom permissions
├── signals.py                  # Django signals
├── tasks.py                    # Celery tasks
├── exceptions.py               # Custom exceptions
├── constants.py                # Constants & enums
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_views.py
│   └── test_services.py
└── migrations/
    └── __init__.py
```

### Advanced App Structure (Domain-Driven)

```
my_app/
├── __init__.py
├── admin.py
├── apps.py
│
├── models/                     # Split large models
│   ├── __init__.py             # Export all models
│   ├── base.py
│   ├── product.py
│   └── category.py
│
├── api/                        # API layer
│   ├── __init__.py
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   └── filters.py
│   └── v2/
│       └── ...
│
├── services/                   # Business logic (write)
│   ├── __init__.py
│   ├── product_service.py
│   └── inventory_service.py
│
├── selectors/                  # Query logic (read)
│   ├── __init__.py
│   └── product_selectors.py
│
├── repositories/               # Data access
│   ├── __init__.py
│   └── product_repository.py
│
├── domain/                     # Domain entities (optional)
│   ├── __init__.py
│   ├── entities.py
│   └── value_objects.py
│
├── events/                     # Domain events
│   ├── __init__.py
│   └── product_events.py
│
├── tasks.py
├── signals.py
├── permissions.py
├── exceptions.py
├── constants.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── factories.py            # Factory Boy
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
└── migrations/
```

---

## 5️⃣ CORE APP PATTERNS

### Base Models

```python
# apps/core/models/base.py
from django.db import models
import uuid


class TimeStampedModel(models.Model):
    """Abstract base model with timestamps."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """Abstract base model with UUID primary key."""
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """Abstract base model with soft delete."""
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def soft_delete(self):
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])


class BaseModel(UUIDModel, TimeStampedModel, SoftDeleteModel):
    """Complete base model dengan semua features."""

    class Meta:
        abstract = True
```

### Base Service

```python
# apps/core/services/base.py
from typing import TypeVar, Generic, List, Optional
from django.db.models import Model

T = TypeVar('T', bound=Model)


class BaseService(Generic[T]):
    """Base service dengan common operations."""
    
    model: T = None
    
    def get_by_id(self, id: str) -> Optional[T]:
        try:
            return self.model.objects.get(id=id, is_deleted=False)
        except self.model.DoesNotExist:
            return None
    
    def get_all(self) -> List[T]:
        return self.model.objects.filter(is_deleted=False)
    
    def create(self, **data) -> T:
        return self.model.objects.create(**data)
    
    def update(self, instance: T, **data) -> T:
        for key, value in data.items():
            setattr(instance, key, value)
        instance.save()
        return instance
    
    def delete(self, instance: T) -> None:
        instance.soft_delete()
```

---

## 6️⃣ CONFIGURATION FILES

### settings/__init__.py

```python
# config/settings/__init__.py
import os

environment = os.environ.get('DJANGO_ENV', 'development')

if environment == 'production':
    from .production import *
elif environment == 'staging':
    from .staging import *
elif environment == 'test':
    from .test import *
else:
    from .development import *
```

### Makefile

```makefile
# Makefile
.PHONY: help install run test migrate shell

help:
	@echo "Available commands:"
	@echo "  install    - Install dependencies"
	@echo "  run        - Run development server"
	@echo "  test       - Run tests"
	@echo "  migrate    - Run migrations"
	@echo "  shell      - Open Django shell"

install:
	pip install -r requirements/development.txt

run:
	python manage.py runserver

test:
	pytest

migrate:
	python manage.py migrate

shell:
	python manage.py shell_plus

lint:
	flake8 apps/
	black apps/ --check

format:
	black apps/
	isort apps/
```

---

## 📊 Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| App name | lowercase, singular | `user`, `product`, `order` |
| Model | PascalCase, singular | `User`, `Product`, `OrderItem` |
| View | PascalCase + suffix | `UserViewSet`, `ProductListView` |
| Serializer | Model + Serializer | `UserSerializer`, `ProductSerializer` |
| Service | Model + Service | `UserService`, `OrderService` |
| URL pattern | kebab-case | `user-profile`, `order-items` |
| Test file | test_ prefix | `test_models.py`, `test_views.py` |

---

## 💡 Best Practices

### ✅ DO

- Satu app = satu domain/fitur
- Gunakan `core` app untuk shared code
- Split settings berdasarkan environment
- Pisahkan business logic ke services
- Gunakan abstract base models
- Consistent naming conventions

### ❌ DON'T

- Jangan buat app terlalu besar (max 10-15 models)
- Jangan circular imports antar apps
- Jangan hardcode settings
- Jangan business logic di views
- Jangan skip migrations
- Jangan campur API versions

---

## 🔗 Related Docs

- [MODELS.md](01-basics/MODELS.md) - Django models
- [VIEWS.md](02-drf/VIEWS.md) - Views & ViewSets
- [SERVICES.md](03-advanced/SERVICES.md) - Service layer pattern
