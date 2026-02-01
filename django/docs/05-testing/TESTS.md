# 🧪 TESTING - Django & Django REST Framework (Junior → Senior)

Dokumentasi lengkap tentang testing di Django, dari basic sampai advanced patterns.

---

## 🎯 Kenapa Testing Penting?

| Benefit | Penjelasan |
|---------|------------|
| **Confidence** | Tahu kode jalan dengan benar |
| **Refactoring** | Bebas refactor tanpa takut break |
| **Documentation** | Test = living documentation |
| **Bug Prevention** | Catch bugs sebelum production |
| **Code Quality** | Force kamu nulis code yang testable |

**Quote:**
> "Code without tests is broken by design" - Jacob Kaplan-Moss (Django co-creator)

---

## 📊 Types of Tests

| Type | Scope | Example | Speed |
|------|-------|---------|-------|
| **Unit Test** | Function/Method | Test single function | ⚡⚡⚡ Fast |
| **Integration Test** | Multiple components | Test service + model | ⚡⚡ Medium |
| **API Test** | HTTP endpoints | Test full request/response | ⚡ Slow |
| **E2E Test** | Entire system | Test dengan browser | 🐢 Very slow |

**Testing Pyramid:**
```
        /\
       /E2E\         ← Few (10%)
      /------\
     /  API   \      ← Some (20%)
    /----------\
   /Integration\     ← More (30%)
  /--------------\
 /   Unit Tests   \  ← Most (40%)
/------------------\
```

---

## 1️⃣ JUNIOR LEVEL - Basic Unit Tests

### Django's TestCase

```python
# apps/tasks/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.tasks.models import Task

User = get_user_model()

class TaskModelTest(TestCase):
    """
    Test Task model
    """
    
    def setUp(self):
        """
        Setup run before each test
        """
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
    
    def test_create_task(self):
        """Test creating a task"""
        task = Task.objects.create(
            user=self.user,
            title='Test Task',
            description='Test description',
            status='TODO'
        )
        
        self.assertEqual(task.title, 'Test Task')
        self.assertEqual(task.status, 'TODO')
        self.assertEqual(task.user, self.user)
    
    def test_task_str_method(self):
        """Test __str__ method"""
        task = Task.objects.create(
            user=self.user,
            title='Test Task'
        )
        
        self.assertEqual(str(task), f"Test Task ({self.user.email})")
    
    def test_task_default_status(self):
        """Test default status is TODO"""
        task = Task.objects.create(
            user=self.user,
            title='Test Task'
        )
        
        self.assertEqual(task.status, 'TODO')
```

### Run Tests

```bash
# Run all tests
python manage.py test

# Run specific app
python manage.py test apps.tasks

# Run specific test class
python manage.py test apps.tasks.tests.TaskModelTest

# Run specific test method
python manage.py test apps.tasks.tests.TaskModelTest.test_create_task

# Verbose output
python manage.py test --verbosity=2

# Keep test database (faster for multiple runs)
python manage.py test --keepdb
```

---

## 2️⃣ MID LEVEL - API Tests (APITestCase)

### Test API Endpoints

```python
# apps/tasks/tests.py
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class TaskAPITest(APITestCase):
    """
    Test Task API endpoints
    """
    
    def setUp(self):
        """Setup user & auth"""
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        
        # Authenticate
        self.client.force_authenticate(user=self.user)
    
    def test_create_task(self):
        """Test POST /api/tasks/"""
        url = reverse('task-list-create')
        data = {
            'title': 'New Task',
            'description': 'Task description',
            'status': 'TODO',
            'priority': 'HIGH'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['data']['title'], 'New Task')
        
        # Verify database
        self.assertEqual(Task.objects.count(), 1)
        task = Task.objects.first()
        self.assertEqual(task.title, 'New Task')
        self.assertEqual(task.user, self.user)
    
    def test_list_tasks(self):
        """Test GET /api/tasks/"""
        # Create test data
        Task.objects.create(user=self.user, title='Task 1')
        Task.objects.create(user=self.user, title='Task 2')
        
        url = reverse('task-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(len(response.data['data']), 2)
    
    def test_get_task_detail(self):
        """Test GET /api/tasks/{id}/"""
        task = Task.objects.create(user=self.user, title='Test Task')
        
        url = reverse('task-detail', kwargs={'pk': task.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['id'], task.id)
        self.assertEqual(response.data['data']['title'], 'Test Task')
    
    def test_update_task(self):
        """Test PUT /api/tasks/{id}/"""
        task = Task.objects.create(user=self.user, title='Old Title')
        
        url = reverse('task-detail', kwargs={'pk': task.id})
        data = {'title': 'New Title', 'status': 'DONE'}
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify database
        task.refresh_from_db()
        self.assertEqual(task.title, 'New Title')
        self.assertEqual(task.status, 'DONE')
    
    def test_delete_task(self):
        """Test DELETE /api/tasks/{id}/"""
        task = Task.objects.create(user=self.user, title='To Delete')
        
        url = reverse('task-detail', kwargs={'pk': task.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Task.objects.count(), 0)
    
    def test_create_task_validation_error(self):
        """Test validation: title required"""
        url = reverse('task-list-create')
        data = {'description': 'No title'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['success'], False)
        self.assertIn('title', response.data['errors'])
    
    def test_unauthorized_access(self):
        """Test access without authentication"""
        self.client.force_authenticate(user=None)  # Logout
        
        url = reverse('task-list-create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_user_can_only_see_own_tasks(self):
        """Test permission: user can't see other's tasks"""
        # Create another user
        other_user = User.objects.create_user(
            email='other@example.com',
            username='otheruser',
            password='pass123'
        )
        
        # Create tasks
        Task.objects.create(user=self.user, title='My Task')
        Task.objects.create(user=other_user, title='Other Task')
        
        url = reverse('task-list-create')
        response = self.client.get(url)
        
        # Should only see own task
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['title'], 'My Task')
```

---

## 3️⃣ MID-SENIOR LEVEL - Test Service Layer

```python
# apps/tasks/tests.py
from django.test import TestCase
from apps.tasks.services import TaskService
from apps.tasks.models import Task

class TaskServiceTest(TestCase):
    """
    Test TaskService business logic
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='pass123'
        )
    
    def test_create_task_service(self):
        """Test TaskService.create_task()"""
        validated_data = {
            'title': 'Service Task',
            'description': 'Test',
            'status': 'TODO'
        }
        
        task = TaskService.create_task(self.user, validated_data)
        
        self.assertEqual(task.title, 'Service Task')
        self.assertEqual(task.user, self.user)
        self.assertEqual(Task.objects.count(), 1)
    
    def test_update_task_service(self):
        """Test TaskService.update_task()"""
        task = Task.objects.create(user=self.user, title='Old')
        
        validated_data = {'title': 'Updated', 'status': 'DONE'}
        
        updated_task = TaskService.update_task(task, validated_data)
        
        self.assertEqual(updated_task.title, 'Updated')
        self.assertEqual(updated_task.status, 'DONE')
    
    def test_delete_task_service(self):
        """Test TaskService.delete_task()"""
        task = Task.objects.create(user=self.user, title='To Delete')
        
        TaskService.delete_task(task)
        
        self.assertEqual(Task.objects.count(), 0)
    
    def test_get_user_tasks(self):
        """Test filtering tasks by user"""
        other_user = User.objects.create_user(
            email='other@example.com',
            username='other',
            password='pass'
        )
        
        Task.objects.create(user=self.user, title='My Task')
        Task.objects.create(user=other_user, title='Other Task')
        
        my_tasks = TaskService.get_user_tasks(self.user)
        
        self.assertEqual(my_tasks.count(), 1)
        self.assertEqual(my_tasks.first().title, 'My Task')
```

---

## 4️⃣ SENIOR LEVEL - Test Fixtures & Factories

### Using Fixtures (JSON)

```python
# apps/tasks/fixtures/test_data.json
[
    {
        "model": "authentication.user",
        "pk": 1,
        "fields": {
            "email": "test@example.com",
            "username": "testuser",
            "password": "pbkdf2_sha256$..."
        }
    },
    {
        "model": "tasks.task",
        "pk": 1,
        "fields": {
            "user": 1,
            "title": "Test Task",
            "status": "TODO"
        }
    }
]
```

```python
# Test with fixtures
class TaskTest(TestCase):
    fixtures = ['test_data.json']
    
    def test_with_fixture_data(self):
        task = Task.objects.get(pk=1)
        self.assertEqual(task.title, 'Test Task')
```

### Factory Pattern (Better Approach)

```bash
pip install factory-boy
```

```python
# apps/tasks/factories.py
import factory
from django.contrib.auth import get_user_model
from apps.tasks.models import Task

User = get_user_model()

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    username = factory.Sequence(lambda n: f'user{n}')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')


class TaskFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Task
    
    user = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: f'Task {n}')
    description = factory.Faker('text', max_nb_chars=200)
    status = 'TODO'
    priority = 'MEDIUM'
```

```python
# Use factories in tests
from apps.tasks.factories import UserFactory, TaskFactory

class TaskTest(TestCase):
    def test_with_factory(self):
        # Create single object
        user = UserFactory()
        task = TaskFactory(user=user, title='Custom Title')
        
        self.assertEqual(task.user, user)
        self.assertEqual(task.title, 'Custom Title')
    
    def test_create_multiple(self):
        # Create multiple objects
        tasks = TaskFactory.create_batch(10)
        
        self.assertEqual(Task.objects.count(), 10)
    
    def test_with_custom_attributes(self):
        task = TaskFactory(
            title='High Priority Task',
            priority='HIGH',
            status='IN_PROGRESS'
        )
        
        self.assertEqual(task.priority, 'HIGH')
        self.assertEqual(task.status, 'IN_PROGRESS')
```

---

## 5️⃣ SENIOR LEVEL - Mock External Dependencies

### Mock Email Sending

```python
from unittest.mock import patch, MagicMock

class EmailTest(TestCase):
    
    @patch('django.core.mail.send_mail')
    def test_send_notification_email(self, mock_send_mail):
        """Test email sending without actually sending"""
        
        # Call function that sends email
        send_task_notification(task_id=1)
        
        # Assert send_mail was called
        mock_send_mail.assert_called_once()
        
        # Check arguments
        args, kwargs = mock_send_mail.call_args
        self.assertIn('Task Notification', args[0])  # Subject
```

### Mock External API

```python
import requests
from unittest.mock import patch

class ExternalAPITest(TestCase):
    
    @patch('requests.get')
    def test_fetch_external_data(self, mock_get):
        """Test calling external API"""
        
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': 'test'}
        mock_get.return_value = mock_response
        
        # Call function
        result = fetch_external_data()
        
        # Assert
        self.assertEqual(result['data'], 'test')
        mock_get.assert_called_once()
```

---

## 6️⃣ EXPERT LEVEL - Test Coverage & CI/CD

### Install Coverage Tool

```bash
pip install coverage
```

### Run Tests with Coverage

```bash
# Run tests dengan coverage
coverage run --source='apps' manage.py test

# Generate report
coverage report

# Generate HTML report
coverage html
# Open htmlcov/index.html di browser
```

### Coverage Report Example

```
Name                                 Stmts   Miss  Cover
--------------------------------------------------------
apps/tasks/models.py                    25      0   100%
apps/tasks/services.py                  45      3    93%
apps/tasks/views.py                     32      5    84%
apps/tasks/serializers.py              18      0   100%
--------------------------------------------------------
TOTAL                                  120      8    93%
```

### Setup in CI/CD (GitHub Actions)

```yaml
# .github/workflows/django-tests.yml
name: Django Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install coverage
    
    - name: Run tests
      run: |
        coverage run manage.py test
        coverage report --fail-under=80
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

---

## 📋 Best Practices

### 1. AAA Pattern (Arrange, Act, Assert)

```python
def test_create_task(self):
    # Arrange - Setup data
    user = UserFactory()
    data = {'title': 'Test Task'}
    
    # Act - Perform action
    task = TaskService.create_task(user, data)
    
    # Assert - Verify result
    self.assertEqual(task.title, 'Test Task')
    self.assertEqual(Task.objects.count(), 1)
```

### 2. One Assertion Per Test (When Possible)

```python
# ❌ Bad: Multiple unrelated assertions
def test_task(self):
    task = TaskFactory()
    self.assertEqual(task.status, 'TODO')
    self.assertTrue(task.is_active)
    self.assertIsNotNone(task.created_at)

# ✅ Good: Separate tests
def test_task_default_status(self):
    task = TaskFactory()
    self.assertEqual(task.status, 'TODO')

def test_task_is_active_by_default(self):
    task = TaskFactory()
    self.assertTrue(task.is_active)
```

### 3. Test Edge Cases

```python
def test_task_title_max_length(self):
    """Test title dengan 255 characters (max length)"""
    long_title = 'A' * 255
    task = TaskFactory(title=long_title)
    self.assertEqual(len(task.title), 255)

def test_task_title_empty_string(self):
    """Test validation: title tidak boleh empty"""
    with self.assertRaises(ValidationError):
        task = Task.objects.create(user=self.user, title='')
        task.full_clean()
```

### 4. Use setUp and tearDown

```python
class TaskTest(TestCase):
    def setUp(self):
        """Run before each test"""
        self.user = UserFactory()
        self.task = TaskFactory(user=self.user)
    
    def tearDown(self):
        """Run after each test (cleanup)"""
        Task.objects.all().delete()
    
    def test_something(self):
        # self.user and self.task available
        ...
```

---

## 🎯 Testing Checklist

- [ ] Unit tests untuk models
- [ ] Unit tests untuk services (business logic)
- [ ] Unit tests untuk serializers
- [ ] API tests untuk endpoints (CRUD)
- [ ] Test authentication & authorization
- [ ] Test validation errors
- [ ] Test edge cases
- [ ] Test permissions
- [ ] Code coverage > 80%
- [ ] CI/CD integration

---

## 7️⃣ EXPERT LEVEL - Pytest-Django (Modern Approach)

### Install Pytest

```bash
pip install pytest pytest-django pytest-cov pytest-xdist pytest-mock
```

### Configuration

```ini
# pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.test
python_files = tests.py test_*.py *_tests.py
addopts = -v --tb=short --strict-markers
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

```python
# conftest.py (Root of project)
import pytest
from django.contrib.auth import get_user_model
from apps.tasks.factories import TaskFactory, UserFactory

User = get_user_model()


# ===== FIXTURES =====

@pytest.fixture
def user(db):
    """Create a test user"""
    return UserFactory()


@pytest.fixture
def authenticated_client(client, user):
    """Client with logged in user"""
    client.force_login(user)
    return client


@pytest.fixture
def api_client():
    """DRF API client"""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_api_client(api_client, user):
    """API client with authentication"""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def task(db, user):
    """Create a test task"""
    return TaskFactory(user=user)


@pytest.fixture
def tasks(db, user):
    """Create multiple test tasks"""
    return TaskFactory.create_batch(10, user=user)


# ===== DATABASE FIXTURES =====

@pytest.fixture(scope='session')
def django_db_setup():
    """
    Custom database setup for test session.
    Runs once per test session.
    """
    pass


@pytest.fixture
def sample_data(db, user):
    """Create full sample data for integration tests"""
    from apps.tasks.models import Task, Category
    
    category = Category.objects.create(name='Work', user=user)
    tasks = [
        Task.objects.create(
            user=user,
            title=f'Task {i}',
            category=category,
            status='TODO' if i % 2 == 0 else 'DONE'
        )
        for i in range(20)
    ]
    
    return {
        'user': user,
        'category': category,
        'tasks': tasks
    }
```

### Pytest Test Examples

```python
# apps/tasks/tests/test_models_pytest.py
import pytest
from apps.tasks.models import Task
from apps.tasks.factories import TaskFactory


class TestTaskModel:
    """Tests for Task model using pytest"""
    
    @pytest.mark.django_db
    def test_create_task(self, user):
        """Test creating a task"""
        task = Task.objects.create(
            user=user,
            title='Test Task',
            status='TODO'
        )
        assert task.id is not None
        assert task.title == 'Test Task'
    
    @pytest.mark.django_db
    def test_task_str_representation(self, task):
        """Test __str__ method"""
        assert str(task) == task.title
    
    @pytest.mark.django_db
    def test_task_default_status(self, user):
        """Test default status is TODO"""
        task = TaskFactory(user=user)
        assert task.status == 'TODO'
    
    @pytest.mark.django_db
    @pytest.mark.parametrize("status,expected", [
        ('TODO', False),
        ('IN_PROGRESS', False),
        ('DONE', True),
    ])
    def test_task_is_completed(self, user, status, expected):
        """Parametrized test for is_completed property"""
        task = TaskFactory(user=user, status=status)
        assert task.is_completed == expected
```

### Parametrized Tests

```python
# apps/tasks/tests/test_services_pytest.py
import pytest
from apps.tasks.services import TaskService
from apps.tasks.factories import TaskFactory


class TestTaskService:
    
    @pytest.mark.django_db
    @pytest.mark.parametrize("input_data,expected_error", [
        ({}, "title"),  # Missing title
        ({"title": ""}, "title"),  # Empty title
        ({"title": "A" * 300}, "title"),  # Too long
    ])
    def test_create_task_validation(self, user, input_data, expected_error):
        """Test various validation scenarios"""
        with pytest.raises(ValueError) as exc_info:
            TaskService.create_task(user, input_data)
        
        assert expected_error in str(exc_info.value)
    
    @pytest.mark.django_db
    @pytest.mark.parametrize("old_status,new_status,should_notify", [
        ('TODO', 'IN_PROGRESS', False),
        ('TODO', 'DONE', True),
        ('IN_PROGRESS', 'DONE', True),
        ('DONE', 'TODO', False),
    ])
    def test_status_change_notification(
        self, user, old_status, new_status, should_notify, mocker
    ):
        """Test notification logic on status change"""
        mock_notify = mocker.patch('apps.tasks.services.send_notification')
        
        task = TaskFactory(user=user, status=old_status)
        TaskService.update_status(task, new_status)
        
        if should_notify:
            mock_notify.assert_called_once()
        else:
            mock_notify.assert_not_called()
```

---

## 8️⃣ EXPERT LEVEL - Advanced Mocking Patterns

### Mock dengan pytest-mock

```python
# apps/tasks/tests/test_external_services.py
import pytest
from unittest.mock import MagicMock, AsyncMock


class TestExternalAPIIntegration:
    
    @pytest.mark.django_db
    def test_sync_with_external_api(self, mocker, user):
        """Mock external API call"""
        # Mock requests.get
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'tasks': [
                {'id': '123', 'title': 'External Task'}
            ]
        }
        mocker.patch('requests.get', return_value=mock_response)
        
        # Call service
        from apps.tasks.services import TaskSyncService
        result = TaskSyncService.sync_from_external(user)
        
        assert result['imported'] == 1
    
    @pytest.mark.django_db
    def test_external_api_failure(self, mocker, user):
        """Test handling of API failures"""
        import requests
        mocker.patch(
            'requests.get',
            side_effect=requests.RequestException("Connection failed")
        )
        
        from apps.tasks.services import TaskSyncService
        with pytest.raises(Exception) as exc_info:
            TaskSyncService.sync_from_external(user)
        
        assert "sync failed" in str(exc_info.value).lower()
    
    @pytest.mark.django_db
    @pytest.mark.asyncio
    async def test_async_external_call(self, mocker, user):
        """Mock async HTTP call"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={'data': 'test'})
        
        mocker.patch('aiohttp.ClientSession.get', return_value=mock_response)
        
        from apps.tasks.services import AsyncTaskService
        result = await AsyncTaskService.fetch_external_data()
        
        assert result['data'] == 'test'


class TestEmailNotifications:
    
    @pytest.mark.django_db
    def test_send_task_completion_email(self, mocker, user):
        """Mock email sending"""
        mock_send = mocker.patch('django.core.mail.send_mail')
        
        from apps.tasks.services import NotificationService
        task = TaskFactory(user=user, status='DONE')
        NotificationService.send_completion_email(task)
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        
        # Verify email content
        assert 'completed' in call_args[0][0].lower()  # Subject
        assert user.email in call_args[0][3]  # Recipients
    
    @pytest.mark.django_db
    def test_email_with_attachment(self, mocker, user):
        """Mock EmailMessage with attachment"""
        mock_email_class = mocker.patch('django.core.mail.EmailMessage')
        mock_email_instance = MagicMock()
        mock_email_class.return_value = mock_email_instance
        
        from apps.tasks.services import ReportService
        ReportService.send_weekly_report(user)
        
        mock_email_instance.attach.assert_called_once()
        mock_email_instance.send.assert_called_once()
```

### Mock Database Queries

```python
# apps/tasks/tests/test_query_optimization.py
import pytest
from django.test.utils import CaptureQueriesContext
from django.db import connection


class TestQueryOptimization:
    
    @pytest.mark.django_db
    def test_task_list_query_count(self, authenticated_api_client, tasks):
        """Ensure list view doesn't have N+1 queries"""
        with CaptureQueriesContext(connection) as context:
            response = authenticated_api_client.get('/api/tasks/')
        
        # Should be: 1 auth + 1 list + 1 count = 3 queries max
        assert len(context.captured_queries) <= 3
    
    @pytest.mark.django_db
    def test_prefetch_related_works(self, authenticated_api_client, user):
        """Verify prefetch_related is working"""
        # Create tasks with related data
        from apps.tasks.factories import TaskFactory, TagFactory
        tags = TagFactory.create_batch(3)
        task = TaskFactory(user=user)
        task.tags.set(tags)
        
        with CaptureQueriesContext(connection) as context:
            response = authenticated_api_client.get(f'/api/tasks/{task.id}/')
        
        # Without prefetch: 1 + 1 per tag = 4 queries
        # With prefetch: 1 (task) + 1 (tags) = 2 queries
        assert len(context.captured_queries) <= 3
```

---

## 9️⃣ EXPERT LEVEL - Integration & E2E Testing

### Full Integration Test

```python
# apps/tasks/tests/test_integration.py
import pytest
from rest_framework import status


@pytest.mark.integration
class TestTaskWorkflow:
    """Integration tests for complete task workflow"""
    
    @pytest.mark.django_db(transaction=True)
    def test_complete_task_lifecycle(self, authenticated_api_client, user):
        """Test full CRUD lifecycle of a task"""
        
        # 1. CREATE
        create_response = authenticated_api_client.post('/api/tasks/', {
            'title': 'Integration Test Task',
            'description': 'Testing full workflow',
            'priority': 'HIGH'
        }, format='json')
        
        assert create_response.status_code == status.HTTP_201_CREATED
        task_id = create_response.data['data']['id']
        
        # 2. READ
        get_response = authenticated_api_client.get(f'/api/tasks/{task_id}/')
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.data['data']['title'] == 'Integration Test Task'
        
        # 3. UPDATE
        update_response = authenticated_api_client.patch(
            f'/api/tasks/{task_id}/',
            {'status': 'IN_PROGRESS'},
            format='json'
        )
        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.data['data']['status'] == 'IN_PROGRESS'
        
        # 4. COMPLETE
        complete_response = authenticated_api_client.patch(
            f'/api/tasks/{task_id}/',
            {'status': 'DONE'},
            format='json'
        )
        assert complete_response.status_code == status.HTTP_200_OK
        
        # 5. DELETE
        delete_response = authenticated_api_client.delete(f'/api/tasks/{task_id}/')
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT
        
        # 6. VERIFY DELETED
        verify_response = authenticated_api_client.get(f'/api/tasks/{task_id}/')
        assert verify_response.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.django_db(transaction=True)
    def test_task_with_subtasks_cascade(self, authenticated_api_client, user):
        """Test that deleting task deletes subtasks"""
        from apps.tasks.models import Task, Subtask
        
        # Create task with subtasks
        create_response = authenticated_api_client.post('/api/tasks/', {
            'title': 'Parent Task',
            'subtasks': [
                {'title': 'Subtask 1'},
                {'title': 'Subtask 2'}
            ]
        }, format='json')
        
        task_id = create_response.data['data']['id']
        
        # Verify subtasks created
        assert Subtask.objects.filter(task_id=task_id).count() == 2
        
        # Delete parent
        authenticated_api_client.delete(f'/api/tasks/{task_id}/')
        
        # Verify cascade delete
        assert Subtask.objects.filter(task_id=task_id).count() == 0
```

### Database Transaction Tests

```python
# apps/tasks/tests/test_transactions.py
import pytest
from django.db import transaction


@pytest.mark.django_db(transaction=True)
class TestDatabaseTransactions:
    
    def test_atomic_task_creation(self, user):
        """Test that task creation is atomic"""
        from apps.tasks.services import TaskService
        from apps.tasks.models import Task, TaskHistory
        
        initial_count = Task.objects.count()
        
        # This should fail and rollback
        try:
            with transaction.atomic():
                TaskService.create_task(user, {'title': 'Test'})
                raise Exception("Simulated failure")
        except Exception:
            pass
        
        # Count should be unchanged
        assert Task.objects.count() == initial_count
    
    def test_bulk_operation_atomicity(self, user, tasks):
        """Test bulk operations are atomic"""
        from apps.tasks.services import TaskBulkService
        
        task_ids = [t.id for t in tasks]
        
        # Mock failure in the middle
        with pytest.raises(Exception):
            TaskBulkService.bulk_update_status(
                task_ids, 
                'DONE',
                fail_at_index=5  # Simulate failure
            )
        
        # All tasks should be unchanged
        from apps.tasks.models import Task
        assert Task.objects.filter(id__in=task_ids, status='DONE').count() == 0
```

---

## 🔟 EXPERT LEVEL - Performance Testing

### Load Testing with Locust

```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between


class TaskAPIUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login before tests"""
        response = self.client.post('/api/auth/login/', json={
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        self.token = response.json()['data']['access']
        self.client.headers = {'Authorization': f'Bearer {self.token}'}
    
    @task(3)
    def list_tasks(self):
        """Most common operation"""
        self.client.get('/api/tasks/')
    
    @task(2)
    def view_task(self):
        """View single task"""
        self.client.get('/api/tasks/1/')
    
    @task(1)
    def create_task(self):
        """Create new task"""
        self.client.post('/api/tasks/', json={
            'title': 'Load Test Task',
            'status': 'TODO'
        })


# Run: locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

### Response Time Testing

```python
# apps/tasks/tests/test_performance.py
import pytest
import time


@pytest.mark.slow
class TestPerformance:
    
    @pytest.mark.django_db
    def test_list_response_time(self, authenticated_api_client, user):
        """List endpoint should respond within 200ms"""
        from apps.tasks.factories import TaskFactory
        
        # Create 100 tasks
        TaskFactory.create_batch(100, user=user)
        
        start = time.time()
        response = authenticated_api_client.get('/api/tasks/')
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.2, f"Response took {elapsed:.2f}s, expected < 0.2s"
    
    @pytest.mark.django_db
    def test_search_response_time(self, authenticated_api_client, user):
        """Search should be fast even with many records"""
        from apps.tasks.factories import TaskFactory
        
        # Create 1000 tasks
        TaskFactory.create_batch(1000, user=user)
        
        start = time.time()
        response = authenticated_api_client.get('/api/tasks/?search=test')
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.5, f"Search took {elapsed:.2f}s, expected < 0.5s"


@pytest.mark.slow
class TestMemoryUsage:
    
    @pytest.mark.django_db
    def test_large_export_memory(self, user):
        """Export shouldn't consume too much memory"""
        import tracemalloc
        from apps.tasks.factories import TaskFactory
        from apps.tasks.services import ExportService
        
        # Create large dataset
        TaskFactory.create_batch(10000, user=user)
        
        tracemalloc.start()
        
        # Export tasks (should use streaming)
        ExportService.export_tasks_csv(user)
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Peak memory should be < 100MB
        assert peak < 100 * 1024 * 1024, f"Peak memory: {peak / 1024 / 1024:.2f}MB"
```

---

## 1️⃣1️⃣ Test Organization & Best Practices

### Test Directory Structure

```
apps/tasks/
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # App-specific fixtures
│   ├── factories.py         # Factory Boy factories
│   │
│   ├── unit/                # Unit tests
│   │   ├── test_models.py
│   │   ├── test_services.py
│   │   └── test_serializers.py
│   │
│   ├── api/                 # API tests
│   │   ├── test_tasks_crud.py
│   │   ├── test_tasks_filter.py
│   │   └── test_tasks_permissions.py
│   │
│   ├── integration/         # Integration tests
│   │   ├── test_workflows.py
│   │   └── test_external_services.py
│   │
│   └── performance/         # Performance tests
│       └── test_response_times.py
```

### Fixtures Hierarchy

```python
# conftest.py (Root - shared fixtures)
@pytest.fixture(scope='session')
def django_db_setup():
    """Session-wide database setup"""
    pass

@pytest.fixture
def user(db):
    return UserFactory()


# apps/tasks/tests/conftest.py (App-specific)
@pytest.fixture
def task(db, user):
    return TaskFactory(user=user)

@pytest.fixture
def task_with_subtasks(db, user):
    task = TaskFactory(user=user)
    SubtaskFactory.create_batch(5, task=task)
    return task


# apps/tasks/tests/api/conftest.py (API-specific)
@pytest.fixture
def create_task_payload():
    return {
        'title': 'Test Task',
        'description': 'Description',
        'priority': 'MEDIUM'
    }
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps --cov-report=html

# Run specific markers
pytest -m "not slow"      # Skip slow tests
pytest -m unit            # Only unit tests
pytest -m integration     # Only integration tests

# Parallel execution
pytest -n auto            # Use all CPU cores

# Stop on first failure
pytest -x

# Re-run failed tests
pytest --lf               # Last failed
pytest --ff               # Failed first

# Verbose output
pytest -v                 # Verbose
pytest -vv                # More verbose

# Watch mode (requires pytest-watch)
ptw                       # Re-run on file changes

# Generate JUnit XML (for CI)
pytest --junitxml=test-results.xml
```

---

## 📊 When to Use Which?

| Scenario | Test Type |
|----------|-----------|
| Model methods | Unit test (TestCase) |
| Business logic | Unit test (TestCase) |
| API endpoints | API test (APITestCase) |
| Authentication flow | API test (APITestCase) |
| Permissions | API test (APITestCase) |
| External API | Mock + Unit test |
| Full workflows | Integration test |
| Response times | Performance test |
| Memory usage | Performance test |

---

## 💡 Common Commands

```bash
# Django test runner
python manage.py test

# Pytest (recommended)
pytest

# With coverage
pytest --cov=apps --cov-report=term-missing

# Parallel
pytest -n auto

# Specific test
pytest apps/tasks/tests/test_services.py::TestTaskService::test_create

# Stop on first failure
pytest -x --pdb  # Drop into debugger on failure
```

---

## 📋 Complete Testing Checklist

### Junior ✅
- [ ] Unit tests for models
- [ ] Basic API tests (CRUD)
- [ ] Test validation errors

### Mid ✅
- [ ] Service layer tests
- [ ] Factory Boy for test data
- [ ] Test authentication/permissions
- [ ] Code coverage > 70%

### Senior ✅
- [ ] Mock external dependencies
- [ ] Database transaction tests
- [ ] Query optimization tests
- [ ] Integration tests
- [ ] Code coverage > 80%

### Expert ✅
- [ ] pytest-django setup
- [ ] Parametrized tests
- [ ] Fixtures hierarchy
- [ ] Async tests
- [ ] Performance tests
- [ ] Memory profiling tests
- [ ] Load testing (Locust)
- [ ] CI/CD integration with coverage gates
- [ ] Mutation testing (optional)
- [ ] Code coverage > 90%

---

## 📚 Further Reading

- [Django Testing Docs](https://docs.djangoproject.com/en/4.2/topics/testing/)
- [DRF Testing Guide](https://www.django-rest-framework.org/api-guide/testing/)
- [pytest-django Documentation](https://pytest-django.readthedocs.io/)
- [Factory Boy Documentation](https://factoryboy.readthedocs.io/)
- [Coverage.py Guide](https://coverage.readthedocs.io/)
- [Locust Load Testing](https://locust.io/)
