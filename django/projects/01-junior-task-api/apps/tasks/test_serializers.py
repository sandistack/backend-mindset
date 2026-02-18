"""
Tests for Task and Category serializers
"""
import pytest
from datetime import timedelta
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from apps.tasks.serializers import (
    CategorySerializer, 
    TaskSerializer, 
    TaskCreateUpdateSerializer
)
from apps.tasks.factories import UserFactory, TaskFactory, CategoryFactory


@pytest.mark.django_db
class TestCategorySerializer:
    """Test CategorySerializer"""
    
    def test_serialize_category(self):
        """Test serializing a category"""
        user = UserFactory()
        category = CategoryFactory(user=user, name="Work", color="#FF5733")
        
        serializer = CategorySerializer(category)
        data = serializer.data
        
        assert data['id'] == category.id
        assert data['name'] == "Work"
        assert data['color'] == "#FF5733"
        assert 'created_at' in data
    
    def test_deserialize_category(self):
        """Test deserializing category data"""
        user = UserFactory()
        data = {
            'name': 'Personal',
            'color': '#3B82F6'
        }
        
        # Create mock request
        request_mock = type('obj', (object,), {'user': user})
        serializer = CategorySerializer(data=data, context={'request': request_mock})
        assert serializer.is_valid(), serializer.errors
        
        category = serializer.save(user=user)
        
        assert category.name == 'Personal'
        assert category.color == '#3B82F6'
        assert category.user == user
    
    def test_category_name_required(self):
        """Test that category name is required"""
        data = {'color': '#FF5733'}
        
        serializer = CategorySerializer(data=data)
        assert not serializer.is_valid()
        assert 'name' in serializer.errors
    
    def test_category_color_default(self):
        """Test category color has default value"""
        user = UserFactory()
        data = {'name': 'Work'}
        
        # Create mock request
        request_mock = type('obj', (object,), {'user': user})
        serializer = CategorySerializer(data=data, context={'request': request_mock})
        assert serializer.is_valid(), serializer.errors
        
        category = serializer.save(user=user)
        assert category.color == '#3B82F6'  # Default color


@pytest.mark.django_db
class TestTaskSerializer:
    """Test TaskSerializer (read-only)"""
    
    def test_serialize_task(self):
        """Test serializing a task"""
        user = UserFactory()
        category = CategoryFactory(user=user)
        task = TaskFactory(
            user=user,
            category=category,
            title="Test Task",
            priority="high",
            status="in_progress"
        )
        
        serializer = TaskSerializer(task)
        data = serializer.data
        
        assert data['id'] == task.id
        assert data['title'] == "Test Task"
        assert data['priority'] == "high"
        assert data['status'] == "in_progress"
        assert data['category']['id'] == category.id
        assert data['category']['name'] == category.name
        assert 'user' not in data  # User should not be exposed
    
    def test_serialize_task_without_category(self):
        """Test serializing task without category"""
        task = TaskFactory(category=None)
        
        serializer = TaskSerializer(task)
        data = serializer.data
        
        assert data['category'] is None
    
    def test_serialize_task_with_due_date(self):
        """Test serializing task with due date"""
        future_date = timezone.now() + timedelta(days=7)
        task = TaskFactory(due_date=future_date)
        
        serializer = TaskSerializer(task)
        data = serializer.data
        
        assert 'due_date' in data
        assert data['due_date'] is not None


@pytest.mark.django_db
class TestTaskCreateUpdateSerializer:
    """Test TaskCreateUpdateSerializer (write operations)"""
    
    def test_create_task(self):
        """Test creating a task"""
        user = UserFactory()
        category = CategoryFactory(user=user)
        
        data = {
            'title': 'New Task',
            'description': 'Task description',
            'priority': 'high',
            'status': 'pending',
            'category': category.id
        }
        
        serializer = TaskCreateUpdateSerializer(data=data, context={'request': type('obj', (object,), {'user': user})})
        assert serializer.is_valid(), serializer.errors
        
        task = serializer.save(user=user)
        
        assert task.title == 'New Task'
        assert task.description == 'Task description'
        assert task.priority == 'high'
        assert task.status == 'pending'
        assert task.category == category
        assert task.user == user
    
    def test_create_task_without_category(self):
        """Test creating task without category"""
        user = UserFactory()
        
        data = {
            'title': 'No Category Task',
            'description': 'Description',
            'priority': 'medium',
            'status': 'pending'
        }
        
        serializer = TaskCreateUpdateSerializer(data=data, context={'request': type('obj', (object,), {'user': user})})
        assert serializer.is_valid()
        
        task = serializer.save(user=user)
        assert task.category is None
    
    def test_title_required(self):
        """Test that title is required"""
        data = {
            'description': 'Description',
            'priority': 'medium',
            'status': 'pending'
        }
        
        serializer = TaskCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'title' in serializer.errors
    
    def test_priority_default_value(self):
        """Test priority defaults to 'medium'"""
        user = UserFactory()
        data = {
            'title': 'Task',
            'status': 'pending'
        }
        
        serializer = TaskCreateUpdateSerializer(data=data, context={'request': type('obj', (object,), {'user': user})})
        assert serializer.is_valid()
        
        task = serializer.save(user=user)
        assert task.priority == 'medium'
    
    def test_status_default_value(self):
        """Test status defaults to 'pending'"""
        user = UserFactory()
        data = {
            'title': 'Task',
            'priority': 'high'
        }
        
        serializer = TaskCreateUpdateSerializer(data=data, context={'request': type('obj', (object,), {'user': user})})
        assert serializer.is_valid()
        
        task = serializer.save(user=user)
        assert task.status == 'pending'
    
    def test_validate_past_due_date(self):
        """Test validation fails for past due dates"""
        past_date = timezone.now() - timedelta(days=1)
        
        data = {
            'title': 'Task',
            'due_date': past_date.isoformat()
        }
        
        serializer = TaskCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'due_date' in serializer.errors
    
    def test_validate_future_due_date(self):
        """Test validation passes for future due dates"""
        user = UserFactory()
        future_date = timezone.now() + timedelta(days=7)
        
        data = {
            'title': 'Task',
            'due_date': future_date.isoformat()
        }
        
        serializer = TaskCreateUpdateSerializer(data=data, context={'request': type('obj', (object,), {'user': user})})
        assert serializer.is_valid(), serializer.errors
    
    def test_validate_category_ownership(self):
        """Test that category must belong to the user"""
        user1 = UserFactory()
        user2 = UserFactory()
        category = CategoryFactory(user=user2)  # Category owned by user2
        
        data = {
            'title': 'Task',
            'category': category.id
        }
        
        request_mock = type('obj', (object,), {'user': user1})
        serializer = TaskCreateUpdateSerializer(data=data, context={'request': request_mock})
        
        assert not serializer.is_valid()
        assert 'category' in serializer.errors
    
    def test_update_task(self):
        """Test updating a task"""
        user = UserFactory()
        task = TaskFactory(user=user, title="Old Title", priority="low")
        
        data = {
            'title': 'Updated Title',
            'priority': 'high'
        }
        
        serializer = TaskCreateUpdateSerializer(task, data=data, partial=True, context={'request': type('obj', (object,), {'user': user})})
        assert serializer.is_valid()
        
        updated_task = serializer.save()
        
        assert updated_task.title == 'Updated Title'
        assert updated_task.priority == 'high'
    
    def test_invalid_priority_choice(self):
        """Test validation fails for invalid priority"""
        data = {
            'title': 'Task',
            'priority': 'invalid_priority'
        }
        
        serializer = TaskCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'priority' in serializer.errors
    
    def test_invalid_status_choice(self):
        """Test validation fails for invalid status"""
        data = {
            'title': 'Task',
            'status': 'invalid_status'
        }
        
        serializer = TaskCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'status' in serializer.errors
