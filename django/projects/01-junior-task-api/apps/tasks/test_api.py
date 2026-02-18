"""
Integration tests for Task and Category API endpoints
"""
import pytest
from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from apps.tasks.models import Task, Category
from apps.tasks.factories import UserFactory, TaskFactory, CategoryFactory


@pytest.mark.django_db
class TestCategoryAPI:
    """Test Category API endpoints"""
    
    def test_list_categories_authenticated(self, authenticated_client, user):
        """Test listing categories for authenticated user"""
        # Create categories for the user
        CategoryFactory.create_batch(3, user=user)
        # Create category for another user (shouldn't be listed)
        other_user = UserFactory()
        CategoryFactory(user=other_user)
        
        url = reverse('tasks:category-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 3
    
    def test_list_categories_unauthenticated(self, api_client):
        """Test that unauthenticated users cannot list categories"""
        url = reverse('tasks:category-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_category(self, authenticated_client):
        """Test creating a category"""
        url = reverse('tasks:category-list')
        data = {
            'name': 'Work',
            'color': '#FF5733'
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['data']['name'] == 'Work'
        assert response.data['data']['color'] == '#FF5733'
    
    def test_create_category_unauthenticated(self, api_client):
        """Test that unauthenticated users cannot create categories"""
        url = reverse('tasks:category-list')
        data = {'name': 'Work'}
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_retrieve_category(self, authenticated_client, user):
        """Test retrieving a single category"""
        category = CategoryFactory(user=user)
        
        url = reverse('tasks:category-detail', kwargs={'pk': category.pk})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['id'] == category.id
        assert response.data['data']['name'] == category.name
    
    def test_retrieve_other_user_category(self, authenticated_client):
        """Test that users cannot retrieve other users' categories"""
        other_user = UserFactory()
        category = CategoryFactory(user=other_user)
        
        url = reverse('tasks:category-detail', kwargs={'pk': category.pk})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_category(self, authenticated_client, user):
        """Test updating a category"""
        category = CategoryFactory(user=user, name="Old Name")
        
        url = reverse('tasks:category-detail', kwargs={'pk': category.pk})
        data = {'name': 'New Name', 'color': '#00FF00'}
        
        response = authenticated_client.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['name'] == 'New Name'
        assert response.data['data']['color'] == '#00FF00'
    
    def test_partial_update_category(self, authenticated_client, user):
        """Test partially updating a category"""
        category = CategoryFactory(user=user, name="Old Name", color="#FF0000")
        
        url = reverse('tasks:category-detail', kwargs={'pk': category.pk})
        data = {'name': 'Updated Name'}
        
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['name'] == 'Updated Name'
        assert response.data['data']['color'] == '#FF0000'  # Unchanged
    
    def test_delete_category(self, authenticated_client, user):
        """Test deleting a category"""
        category = CategoryFactory(user=user)
        category_id = category.id
        
        url = reverse('tasks:category-detail', kwargs={'pk': category.pk})
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert not Category.objects.filter(id=category_id).exists()
    
    def test_delete_other_user_category(self, authenticated_client):
        """Test that users cannot delete other users' categories"""
        other_user = UserFactory()
        category = CategoryFactory(user=other_user)
        
        url = reverse('tasks:category-detail', kwargs={'pk': category.pk})
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Category.objects.filter(id=category.id).exists()


@pytest.mark.django_db
class TestTaskAPI:
    """Test Task API endpoints"""
    
    def test_list_tasks_authenticated(self, authenticated_client, user):
        """Test listing tasks for authenticated user"""
        # Create tasks for the user
        TaskFactory.create_batch(3, user=user)
        # Create task for another user (shouldn't be listed)
        other_user = UserFactory()
        TaskFactory(user=other_user)
        
        url = reverse('tasks:task-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 3
    
    def test_list_tasks_unauthenticated(self, api_client):
        """Test that unauthenticated users cannot list tasks"""
        url = reverse('tasks:task-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_task(self, authenticated_client, user):
        """Test creating a task"""
        category = CategoryFactory(user=user)
        url = reverse('tasks:task-list')
        
        data = {
            'title': 'New Task',
            'description': 'Task description',
            'priority': 'high',
            'status': 'pending',
            'category': category.id
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['data']['title'] == 'New Task'
        assert response.data['data']['priority'] == 'high'
        assert response.data['data']['category']['id'] == category.id
    
    def test_create_task_without_category(self, authenticated_client):
        """Test creating task without category"""
        url = reverse('tasks:task-list')
        data = {
            'title': 'No Category Task',
            'description': 'Description'
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['data']['category'] is None
    
    def test_create_task_with_other_user_category(self, authenticated_client):
        """Test that users cannot use other users' categories"""
        other_user = UserFactory()
        category = CategoryFactory(user=other_user)
        
        url = reverse('tasks:task-list')
        data = {
            'title': 'Task',
            'category': category.id
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'category' in response.data
    
    def test_retrieve_task(self, authenticated_client, user):
        """Test retrieving a single task"""
        task = TaskFactory(user=user)
        
        url = reverse('tasks:task-detail', kwargs={'pk': task.pk})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['id'] == task.id
        assert response.data['data']['title'] == task.title
    
    def test_retrieve_other_user_task(self, authenticated_client):
        """Test that users cannot retrieve other users' tasks"""
        other_user = UserFactory()
        task = TaskFactory(user=other_user)
        
        url = reverse('tasks:task-detail', kwargs={'pk': task.pk})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_task(self, authenticated_client, user):
        """Test updating a task"""
        task = TaskFactory(user=user, title="Old Title")
        
        url = reverse('tasks:task-detail', kwargs={'pk': task.pk})
        data = {
            'title': 'Updated Title',
            'description': 'Updated description',
            'priority': 'high',
            'status': 'in_progress'
        }
        
        response = authenticated_client.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['title'] == 'Updated Title'
        assert response.data['data']['priority'] == 'high'
    
    def test_partial_update_task(self, authenticated_client, user):
        """Test partially updating a task"""
        task = TaskFactory(user=user, title="Old Title", priority="low")
        
        url = reverse('tasks:task-detail', kwargs={'pk': task.pk})
        data = {'title': 'Updated Title'}
        
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['title'] == 'Updated Title'
        assert response.data['data']['priority'] == 'low'  # Unchanged
    
    def test_delete_task_soft_delete(self, authenticated_client, user):
        """Test deleting a task (soft delete)"""
        task = TaskFactory(user=user)
        task_id = task.id
        
        url = reverse('tasks:task-detail', kwargs={'pk': task.pk})
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Task should be soft deleted
        task_deleted = Task.all_objects.get(id=task_id)
        assert task_deleted.is_deleted
        
        # Should not appear in default queryset
        assert not Task.objects.filter(id=task_id).exists()
    
    def test_complete_task_action(self, authenticated_client, user):
        """Test marking task as complete"""
        task = TaskFactory(user=user, status="in_progress")
        
        url = reverse('tasks:task-complete', kwargs={'pk': task.pk})
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['status'] == 'done'
        assert response.data['data']['completed_at'] is not None
        
        task.refresh_from_db()
        assert task.status == 'done'
        assert task.completed_at is not None
    
    def test_restore_task_action(self, authenticated_client, user):
        """Test restoring a soft-deleted task"""
        task = TaskFactory(user=user, is_deleted=True)
        
        url = reverse('tasks:task-restore', kwargs={'pk': task.pk})
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        task.refresh_from_db()
        assert not task.is_deleted


@pytest.mark.django_db
class TestTaskFiltering:
    """Test task filtering, search, and ordering"""
    
    def test_filter_by_category(self, authenticated_client, user):
        """Test filtering tasks by category"""
        category1 = CategoryFactory(user=user, name="Work")
        category2 = CategoryFactory(user=user, name="Personal")
        
        TaskFactory(user=user, category=category1)
        TaskFactory(user=user, category=category1)
        TaskFactory(user=user, category=category2)
        
        url = reverse('tasks:task-list')
        response = authenticated_client.get(url, {'category': category1.id})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 2
    
    def test_filter_by_priority(self, authenticated_client, user):
        """Test filtering tasks by priority"""
        TaskFactory(user=user, priority="high")
        TaskFactory(user=user, priority="high")
        TaskFactory(user=user, priority="low")
        
        url = reverse('tasks:task-list')
        response = authenticated_client.get(url, {'priority': 'high'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 2
    
    def test_filter_by_status(self, authenticated_client, user):
        """Test filtering tasks by status"""
        TaskFactory(user=user, status="pending")
        TaskFactory(user=user, status="in_progress")
        TaskFactory(user=user, status="done")
        
        url = reverse('tasks:task-list')
        response = authenticated_client.get(url, {'status': 'pending'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 1
    
    def test_filter_is_completed(self, authenticated_client, user):
        """Test filtering completed tasks"""
        TaskFactory(user=user, status="done", completed_at=timezone.now())
        TaskFactory(user=user, status="pending")
        
        url = reverse('tasks:task-list')
        response = authenticated_client.get(url, {'is_completed': 'true'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 1
        assert response.data['data'][0]['status'] == 'done'
    
    def test_filter_is_overdue(self, authenticated_client, user):
        """Test filtering overdue tasks"""
        past_date = timezone.now() - timedelta(days=1)
        future_date = timezone.now() + timedelta(days=7)
        
        TaskFactory(user=user, due_date=past_date, status="pending")
        TaskFactory(user=user, due_date=future_date, status="pending")
        TaskFactory(user=user, due_date=None)
        
        url = reverse('tasks:task-list')
        response = authenticated_client.get(url, {'is_overdue': 'true'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 1
    
    def test_filter_has_category(self, authenticated_client, user):
        """Test filtering tasks with/without category"""
        category = CategoryFactory(user=user)
        TaskFactory(user=user, category=category)
        TaskFactory(user=user, category=None)
        
        url = reverse('tasks:task-list')
        response = authenticated_client.get(url, {'has_category': 'true'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 1
    
    def test_search_by_title(self, authenticated_client, user):
        """Test searching tasks by title"""
        TaskFactory(user=user, title="Django Project")
        TaskFactory(user=user, title="React Project")
        TaskFactory(user=user, title="Meeting Notes")
        
        url = reverse('tasks:task-list')
        response = authenticated_client.get(url, {'search': 'Project'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 2
    
    def test_search_by_description(self, authenticated_client, user):
        """Test searching tasks by description"""
        TaskFactory(user=user, description="Python development task")
        TaskFactory(user=user, description="JavaScript coding")
        
        url = reverse('tasks:task-list')
        response = authenticated_client.get(url, {'search': 'Python'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 1
    
    def test_ordering_by_created_at(self, authenticated_client, user):
        """Test ordering tasks by creation date"""
        task1 = TaskFactory(user=user)
        task2 = TaskFactory(user=user)
        task3 = TaskFactory(user=user)
        
        url = reverse('tasks:task-list')
        response = authenticated_client.get(url, {'ordering': '-created_at'})
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['data']
        assert results[0]['id'] == task3.id
        assert results[2]['id'] == task1.id
    
    def test_ordering_by_priority(self, authenticated_client, user):
        """Test ordering tasks by priority"""
        TaskFactory(user=user, priority="low", title="Low Priority")
        TaskFactory(user=user, priority="high", title="High Priority")
        TaskFactory(user=user, priority="medium", title="Medium Priority")
        
        url = reverse('tasks:task-list')
        response = authenticated_client.get(url, {'ordering': 'priority'})
        
        assert response.status_code == status.HTTP_200_OK
        # Ordering should work alphabetically: high, low, medium


@pytest.mark.django_db
class TestPagination:
    """Test pagination"""
    
    def test_pagination_default_page_size(self, authenticated_client, user):
        """Test default pagination (10 items per page)"""
        TaskFactory.create_batch(15, user=user)
        
        url = reverse('tasks:task-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 10
        assert response.data['pagination']['count'] == 15
        assert response.data['pagination']['total_pages'] == 2
        assert response.data['pagination']['page'] == 1
        assert response.data['pagination']['page_size'] == 10
    
    def test_pagination_custom_page_size(self, authenticated_client, user):
        """Test custom page size"""
        TaskFactory.create_batch(15, user=user)
        
        url = reverse('tasks:task-list')
        response = authenticated_client.get(url, {'page_size': 5})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 5
        assert response.data['pagination']['page_size'] == 5
        assert response.data['pagination']['total_pages'] == 3
    
    def test_pagination_second_page(self, authenticated_client, user):
        """Test accessing second page"""
        TaskFactory.create_batch(15, user=user)
        
        url = reverse('tasks:task-list')
        response = authenticated_client.get(url, {'page': 2})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 5
        assert response.data['pagination']['page'] == 2
        assert response.data['pagination']['has_previous']
        assert not response.data['pagination']['has_next']
