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

## 📊 When to Use Which?

| Scenario | Test Type |
|----------|-----------|
| Model methods | Unit test (TestCase) |
| Business logic | Unit test (TestCase) |
| API endpoints | API test (APITestCase) |
| Authentication flow | API test (APITestCase) |
| Permissions | API test (APITestCase) |
| External API | Mock + Unit test |

---

## 💡 Common Commands

```bash
# Run all tests
python manage.py test

# Run with coverage
coverage run manage.py test
coverage report

# Run specific tests
python manage.py test apps.tasks.tests.TaskAPITest.test_create_task

# Keep database (faster)
python manage.py test --keepdb

# Parallel execution
python manage.py test --parallel

# Stop on first failure
python manage.py test --failfast
```

---

## 📚 Further Reading

- [Django Testing Docs](https://docs.djangoproject.com/en/4.2/topics/testing/)
- [DRF Testing Guide](https://www.django-rest-framework.org/api-guide/testing/)
- [Factory Boy Documentation](https://factoryboy.readthedocs.io/)
- [Coverage.py Guide](https://coverage.readthedocs.io/)
