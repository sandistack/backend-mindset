# 🧪 Step 5: Testing

**Waktu:** 4-6 jam  
**Prerequisite:** Step 1-4 selesai

---

## 🎯 Tujuan

- Setup testing environment
- Unit tests untuk models
- Unit tests untuk serializers
- Integration tests untuk API endpoints
- Test coverage reporting

---

## 📋 Tasks

### 5.1 Setup Testing

**Install dependencies:**

```bash
pip install pytest pytest-django pytest-cov factory-boy faker
```

**Buat `pytest.ini` di root:**

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.development
python_files = tests.py test_*.py *_tests.py
addopts = -v --tb=short
```

**Buat `conftest.py` di root:**

```python
import pytest
from rest_framework.test import APIClient
from apps.authentication.models import User

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user(db):
    return User.objects.create_user(
        email='test@example.com',
        name='Test User',
        password='TestPass123!'
    )

@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client
```

---

### 5.2 Factories

**Buat `apps/tasks/factories.py`:**

```python
import factory
from factory.django import DjangoModelFactory
from faker import Faker
from .models import Task, Category
from apps.authentication.models import User

fake = Faker()

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
    
    email = factory.LazyAttribute(lambda _: fake.email())
    name = factory.LazyAttribute(lambda _: fake.name())
    password = factory.PostGenerationMethodCall('set_password', 'TestPass123!')

class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category
    
    name = factory.LazyAttribute(lambda _: fake.word())
    color = '#3B82F6'
    user = factory.SubFactory(UserFactory)

class TaskFactory(DjangoModelFactory):
    class Meta:
        model = Task
    
    title = factory.LazyAttribute(lambda _: fake.sentence(nb_words=4))
    description = factory.LazyAttribute(lambda _: fake.paragraph())
    priority = 'medium'
    status = 'pending'
    user = factory.SubFactory(UserFactory)
    category = factory.SubFactory(CategoryFactory)
```

**Referensi:** [TESTS.md](../../../docs/05-testing/TESTS.md)

---

### 5.3 Model Tests

**Buat `apps/tasks/tests/test_models.py`:**

Tests yang harus dibuat:

```python
class TestTaskModel:
    def test_create_task(self):
        """Task bisa dibuat dengan fields yang benar"""
        pass
    
    def test_task_str(self):
        """__str__ return title"""
        pass
    
    def test_mark_complete(self):
        """mark_complete() set status dan completed_at"""
        pass
    
    def test_soft_delete(self):
        """soft_delete() set is_deleted=True"""
        pass
    
    def test_restore(self):
        """restore() set is_deleted=False"""
        pass
    
    def test_default_manager_excludes_deleted(self):
        """Task.objects tidak include deleted tasks"""
        pass
    
    def test_all_objects_includes_deleted(self):
        """Task.all_objects include deleted tasks"""
        pass


class TestCategoryModel:
    def test_create_category(self):
        """Category bisa dibuat"""
        pass
    
    def test_unique_name_per_user(self):
        """Nama category harus unique per user"""
        pass
    
    def test_same_name_different_users_allowed(self):
        """User berbeda boleh punya category dengan nama sama"""
        pass
```

---

### 5.4 Serializer Tests

**Buat `apps/tasks/tests/test_serializers.py`:**

```python
class TestTaskSerializer:
    def test_serialize_task(self):
        """Serialize task dengan semua fields"""
        pass
    
    def test_nested_category(self):
        """Category di-serialize sebagai nested object"""
        pass


class TestTaskCreateSerializer:
    def test_valid_data(self):
        """Serializer valid dengan data lengkap"""
        pass
    
    def test_title_required(self):
        """Title harus diisi"""
        pass
    
    def test_due_date_not_in_past(self):
        """due_date tidak boleh di masa lalu"""
        pass
    
    def test_category_must_belong_to_user(self):
        """Category harus milik user yang sama"""
        pass
```

---

### 5.5 API Integration Tests

**Buat `apps/tasks/tests/test_api.py`:**

```python
import pytest
from rest_framework import status
from django.urls import reverse

@pytest.mark.django_db
class TestTaskAPI:
    
    def test_list_tasks_unauthenticated(self, api_client):
        """Unauthenticated user tidak bisa akses"""
        url = reverse('task-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_tasks_authenticated(self, authenticated_client, user):
        """Authenticated user bisa list tasks"""
        # Create tasks
        TaskFactory.create_batch(5, user=user)
        
        url = reverse('task-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 5
    
    def test_list_only_own_tasks(self, authenticated_client, user):
        """User hanya lihat task miliknya"""
        # Create own tasks
        TaskFactory.create_batch(3, user=user)
        # Create other user's tasks
        other_user = UserFactory()
        TaskFactory.create_batch(2, user=other_user)
        
        url = reverse('task-list')
        response = authenticated_client.get(url)
        
        assert len(response.data['data']) == 3
    
    def test_create_task(self, authenticated_client, user):
        """Bisa create task"""
        category = CategoryFactory(user=user)
        url = reverse('task-list')
        data = {
            'title': 'New Task',
            'description': 'Description',
            'priority': 'high',
            'category': category.id
        }
        
        response = authenticated_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'New Task'
    
    def test_update_task(self, authenticated_client, user):
        """Bisa update own task"""
        task = TaskFactory(user=user)
        url = reverse('task-detail', kwargs={'pk': task.id})
        data = {'title': 'Updated Title'}
        
        response = authenticated_client.patch(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Updated Title'
    
    def test_cannot_update_other_user_task(self, authenticated_client):
        """Tidak bisa update task user lain"""
        other_user = UserFactory()
        task = TaskFactory(user=other_user)
        url = reverse('task-detail', kwargs={'pk': task.id})
        
        response = authenticated_client.patch(url, {'title': 'Hacked'})
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_task_soft(self, authenticated_client, user):
        """Delete adalah soft delete"""
        task = TaskFactory(user=user)
        url = reverse('task-detail', kwargs={'pk': task.id})
        
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        task.refresh_from_db()
        assert task.is_deleted == True
    
    def test_complete_task(self, authenticated_client, user):
        """Bisa mark task complete"""
        task = TaskFactory(user=user, status='pending')
        url = reverse('task-complete', kwargs={'pk': task.id})
        
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'done'
    
    def test_filter_by_status(self, authenticated_client, user):
        """Filter by status berfungsi"""
        TaskFactory.create_batch(3, user=user, status='pending')
        TaskFactory.create_batch(2, user=user, status='done')
        
        url = reverse('task-list') + '?status=pending'
        response = authenticated_client.get(url)
        
        assert len(response.data['data']) == 3
    
    def test_search_tasks(self, authenticated_client, user):
        """Search berfungsi"""
        TaskFactory(user=user, title='Meeting with client')
        TaskFactory(user=user, title='Buy groceries')
        
        url = reverse('task-list') + '?search=meeting'
        response = authenticated_client.get(url)
        
        assert len(response.data['data']) == 1
    
    def test_pagination(self, authenticated_client, user):
        """Pagination berfungsi"""
        TaskFactory.create_batch(25, user=user)
        
        url = reverse('task-list') + '?page_size=10'
        response = authenticated_client.get(url)
        
        assert len(response.data['data']) == 10
        assert response.data['pagination']['total_pages'] == 3
```

---

### 5.6 Auth Tests

**Buat `apps/authentication/tests/test_api.py`:**

```python
@pytest.mark.django_db
class TestAuthAPI:
    
    def test_register_success(self, api_client):
        """Register dengan data valid"""
        pass
    
    def test_register_duplicate_email(self, api_client, user):
        """Register gagal jika email sudah ada"""
        pass
    
    def test_register_weak_password(self, api_client):
        """Register gagal jika password lemah"""
        pass
    
    def test_login_success(self, api_client, user):
        """Login dengan credentials valid"""
        pass
    
    def test_login_wrong_password(self, api_client, user):
        """Login gagal dengan password salah"""
        pass
    
    def test_login_returns_tokens(self, api_client, user):
        """Login return access dan refresh token"""
        pass
    
    def test_token_refresh(self, api_client, user):
        """Token refresh berfungsi"""
        pass
    
    def test_logout_blacklists_token(self, authenticated_client):
        """Logout blacklist refresh token"""
        pass
```

---

### 5.7 Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps --cov-report=html

# Run specific file
pytest apps/tasks/tests/test_api.py

# Run specific test
pytest apps/tasks/tests/test_api.py::TestTaskAPI::test_list_tasks_authenticated

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

---

## ✅ Checklist

- [ ] pytest.ini configured
- [ ] conftest.py dengan fixtures
- [ ] Factories untuk User, Task, Category
- [ ] Model tests lengkap
- [ ] Serializer tests lengkap
- [ ] API integration tests lengkap
- [ ] Auth API tests
- [ ] Coverage minimal 80%
- [ ] Semua tests passing

---

## 🎯 Target Coverage

```
apps/authentication/models.py     90%+
apps/authentication/views.py      85%+
apps/tasks/models.py              90%+
apps/tasks/views.py               85%+
apps/tasks/serializers.py         85%+
apps/tasks/filters.py             80%+
```

---

## 🔗 Referensi

- [TESTS.md](../../../docs/05-testing/TESTS.md) - Complete testing guide

---

## 🎉 Project Complete!

Selamat! Kamu sudah menyelesaikan Project 01: Task Management API.

**Yang sudah dipelajari:**
- ✅ Django project structure
- ✅ Custom User model
- ✅ JWT Authentication
- ✅ REST API with ViewSets
- ✅ Filtering & Pagination
- ✅ Testing with pytest

**Next Step:** Lanjut ke [Project 02: E-Commerce API](../../02-mid-ecommerce-api/README.md)
