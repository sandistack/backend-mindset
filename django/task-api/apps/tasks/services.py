"""
Task business logic

Maintainable: Centralized task operations
Testable: Isolated business logic
Scalable: Easy to add new features
"""

from .models import Task
from apps.core.utils import log_activity
from django.db.models import Q
import logging

logger = logging.getLogger('apps')


class TaskService:
    """
    Service untuk handle task operations
    
    Single Responsibility: Task-related logic only
    Predictable: Consistent behavior across operations
    """
    
    @staticmethod
    def create_task(user, validated_data, request=None):
        """
        Create new task
        
        Args:
            user: User instance (task owner)
            validated_data: Dict dari TaskSerializer
            request: HTTP request object (optional)
        
        Returns:
            Task instance
        
        Maintainable: Single place for task creation
        Secure: User assigned from request, not from input
        """
        try:
            logger.info(f"Creating task for user {user.username}: {validated_data.get('title')}")
            
            # Create task
            task = Task.objects.create(
                user=user,
                **validated_data
            )
            
            logger.info(f"Task created successfully: ID={task.id}, Title={task.title}")
            
            # Log to audit trail
            log_activity(
                user=user,
                action='CREATE',
                feature='task',
                description=f"Created task: {task.title}",
                request=request,
                status='SUCCESS'
            )
            
            return task
            
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}", exc_info=True)
            
            # Log error
            log_activity(
                user=user,
                action='ERROR',
                feature='task',
                description=f"Error creating task: {str(e)}",
                request=request,
                status='FAILED'
            )
            
            raise
    
    @staticmethod
    def update_task(task, validated_data, request=None):
        """
        Update existing task
        
        Args:
            task: Task instance to update
            validated_data: Dict dari TaskSerializer
            request: HTTP request object (optional)
        
        Returns:
            Updated Task instance
        
        Maintainable: Centralized update logic
        Predictable: Always log changes
        """
        try:
            user = request.user if request else task.user
            
            logger.info(f"Updating task ID={task.id} by user {user.username}")
            
            # Track changes for audit
            changes = []
            for key, value in validated_data.items():
                old_value = getattr(task, key)
                if old_value != value:
                    changes.append(f"{key}: {old_value} → {value}")
                    setattr(task, key, value)
            
            task.save()
            
            logger.info(f"Task updated successfully: ID={task.id}")
            
            # Log changes
            change_description = ', '.join(changes) if changes else 'No changes'
            log_activity(
                user=user,
                action='UPDATE',
                feature='task',
                description=f"Updated task '{task.title}': {change_description}",
                request=request,
                status='SUCCESS'
            )
            
            return task
            
        except Exception as e:
            logger.error(f"Error updating task ID={task.id}: {str(e)}", exc_info=True)
            
            log_activity(
                user=user,
                action='ERROR',
                feature='task',
                description=f"Error updating task: {str(e)}",
                request=request,
                status='FAILED'
            )
            
            raise
    
    @staticmethod
    def delete_task(task, request=None):
        """
        Delete task
        
        Args:
            task: Task instance to delete
            request: HTTP request object (optional)
        
        Secure: Log before deletion (can't log after!)
        Maintainable: Single deletion logic
        """
        try:
            user = request.user if request else task.user
            task_id = task.id
            task_title = task.title
            
            logger.info(f"Deleting task ID={task_id} by user {user.username}")
            
            # Log BEFORE deletion
            log_activity(
                user=user,
                action='DELETE',
                feature='task',
                description=f"Deleted task: {task_title}",
                request=request,
                status='SUCCESS'
            )
            
            # Delete task
            task.delete()
            
            logger.info(f"Task deleted successfully: ID={task_id}")
            
        except Exception as e:
            logger.error(f"Error deleting task ID={task.id}: {str(e)}", exc_info=True)
            
            log_activity(
                user=user,
                action='ERROR',
                feature='task',
                description=f"Error deleting task: {str(e)}",
                request=request,
                status='FAILED'
            )
            
            raise
    
    @staticmethod
    def get_user_tasks(user, filters=None):
        """
        Get tasks for a user with optional filters
        
        Args:
            user: User instance
            filters: Dict with filter params (status, priority, search)
        
        Returns:
            QuerySet of Tasks
        
        Scalable: Efficient database queries
        Maintainable: Centralized filtering logic
        """
        queryset = Task.objects.filter(user=user)
        
        if not filters:
            return queryset
        
        # Filter by status
        if filters.get('status'):
            queryset = queryset.filter(status=filters['status'])
        
        # Filter by priority
        if filters.get('priority'):
            queryset = queryset.filter(priority=filters['priority'])
        
        # Search in title and description
        if filters.get('search'):
            search_term = filters['search']
            queryset = queryset.filter(
                Q(title__icontains=search_term) |
                Q(description__icontains=search_term)
            )
        
        return queryset
    
    @staticmethod
    def can_user_edit_task(user, task):
        """
        Check if user can edit task
        
        Args:
            user: User instance
            task: Task instance
        
        Returns:
            Boolean
        
        Secure: Centralized permission logic
        Testable: Easy to test permissions
        """
        # Owner or superuser can edit
        return task.user == user or user.is_superuser
    
    @staticmethod
    def can_user_delete_task(user, task):
        """
        Check if user can delete task
        
        Args:
            user: User instance
            task: Task instance
        
        Returns:
            Boolean
        
        Secure: Centralized permission logic
        """
        # Owner or superuser can delete
        return task.user == user or user.is_superuser
