"""
Tests for Task and Category models
"""
import pytest
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import IntegrityError
from apps.tasks.models import Task, Category
from apps.tasks.factories import UserFactory, TaskFactory, CategoryFactory


@pytest.mark.django_db
class TestCategoryModel:
    """Test Category model"""
    
    def test_create_category(self):
        """Test creating a category"""
        user = UserFactory()
        category = CategoryFactory(user=user, name="Work", color="#FF5733")
        
        assert category.name == "Work"
        assert category.color == "#FF5733"
        assert category.user == user
        assert str(category) == f"Work ({user.email})"
    
    def test_category_user_cascade_delete(self):
        """Test that deleting a user deletes their categories"""
        user = UserFactory()
        category = CategoryFactory(user=user)
        
        category_id = category.id
        user.delete()
        
        assert not Category.objects.filter(id=category_id).exists()
    
    def test_category_unique_name_per_user(self):
        """Test that category names must be unique per user"""
        user = UserFactory()
        CategoryFactory(user=user, name="Personal")
        
        # Creating same name for same user should raise error
        with pytest.raises(IntegrityError):
            CategoryFactory(user=user, name="Personal")
    
    def test_category_same_name_different_users(self):
        """Test that different users can have categories with same name"""
        user1 = UserFactory()
        user2 = UserFactory()
        
        category1 = CategoryFactory(user=user1, name="Work")
        category2 = CategoryFactory(user=user2, name="Work")
        
        assert category1.name == category2.name
        assert category1.user != category2.user


@pytest.mark.django_db
class TestTaskModel:
    """Test Task model"""
    
    def test_create_task(self):
        """Test creating a task"""
        user = UserFactory()
        task = TaskFactory(
            user=user,
            title="Test Task",
            description="Test Description",
            priority="high",
            status="pending"
        )
        
        assert task.title == "Test Task"
        assert task.description == "Test Description"
        assert task.priority == "high"
        assert task.status == "pending"
        assert task.user == user
        assert not task.is_deleted
        assert str(task) == f"Test Task ({user.email})"
    
    def test_task_with_category(self):
        """Test task with category"""
        user = UserFactory()
        category = CategoryFactory(user=user)
        task = TaskFactory(user=user, category=category)
        
        assert task.category == category
    
    def test_task_without_category(self):
        """Test task without category (optional)"""
        task = TaskFactory(category=None)
        assert task.category is None
    
    def test_task_with_due_date(self):
        """Test task with due date"""
        future_date = timezone.now() + timedelta(days=7)
        task = TaskFactory(due_date=future_date)
        
        assert task.due_date == future_date
    
    def test_mark_complete_action(self):
        """Test marking task as complete"""
        task = TaskFactory(status="in_progress")
        
        assert task.status == "in_progress"
        assert task.completed_at is None
        
        task.mark_complete()
        
        assert task.status == "done"
        assert task.completed_at is not None
        assert isinstance(task.completed_at, datetime)
    
    def test_soft_delete_action(self):
        """Test soft delete functionality"""
        task = TaskFactory()
        
        assert not task.is_deleted
        
        task.soft_delete()
        
        assert task.is_deleted
    
    def test_restore_action(self):
        """Test restore from soft delete"""
        task = TaskFactory(is_deleted=True)
        
        assert task.is_deleted
        
        task.restore()
        
        assert not task.is_deleted
    
    def test_task_manager_excludes_deleted(self):
        """Test that default manager excludes deleted tasks"""
        user = UserFactory()
        active_task = TaskFactory(user=user, is_deleted=False)
        deleted_task = TaskFactory(user=user, is_deleted=True)
        
        # Default manager should only return non-deleted tasks
        all_tasks = Task.objects.all()
        
        assert active_task in all_tasks
        assert deleted_task not in all_tasks
    
    def test_task_manager_all_with_deleted(self):
        """Test accessing all tasks including deleted"""
        user = UserFactory()
        active_task = TaskFactory(user=user, is_deleted=False)
        deleted_task = TaskFactory(user=user, is_deleted=True)
        
        # all_objects should return both
        all_tasks = Task.all_objects.all()
        
        assert active_task in all_tasks
        assert deleted_task in all_tasks
    
    def test_task_user_cascade_delete(self):
        """Test that deleting user deletes their tasks"""
        user = UserFactory()
        task = TaskFactory(user=user)
        
        task_id = task.id
        user.delete()
        
        # Task should be completely deleted (not soft deleted)
        assert not Task.all_objects.filter(id=task_id).exists()
    
    def test_task_category_set_null_on_delete(self):
        """Test that deleting category sets task category to NULL"""
        user = UserFactory()
        category = CategoryFactory(user=user)
        task = TaskFactory(user=user, category=category)
        
        category_id = category.id
        category.delete()
        
        task.refresh_from_db()
        assert task.category is None
    
    def test_task_priority_choices(self):
        """Test task priority choices"""
        task_low = TaskFactory(priority="low")
        task_medium = TaskFactory(priority="medium")
        task_high = TaskFactory(priority="high")
        
        assert task_low.priority == "low"
        assert task_medium.priority == "medium"
        assert task_high.priority == "high"
    
    def test_task_status_choices(self):
        """Test task status choices"""
        task_pending = TaskFactory(status="pending")
        task_in_progress = TaskFactory(status="in_progress")
        task_done = TaskFactory(status="done")
        
        assert task_pending.status == "pending"
        assert task_in_progress.status == "in_progress"
        assert task_done.status == "done"
    
    def test_task_completed_at_set_on_mark_complete(self):
        """Test that completed_at is set when marking complete"""
        task = TaskFactory(status="pending", completed_at=None)
        
        before_time = timezone.now()
        task.mark_complete()
        after_time = timezone.now()
        
        assert task.completed_at >= before_time
        assert task.completed_at <= after_time
