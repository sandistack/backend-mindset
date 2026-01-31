# ⚠️ ERROR HANDLING - Django & DRF (Junior → Senior)

Dokumentasi lengkap tentang error handling di Django REST Framework.

---

## 🎯 Kenapa Error Handling Penting?

| Problem | Tanpa Error Handling | Dengan Error Handling |
|---------|---------------------|---------------------|
| **User Experience** | "500 Internal Server Error" | "Invalid email format" |
| **Debugging** | Gak tahu error dari mana | Clear error trace |
| **Security** | Expose internal details | Hide sensitive info |
| **Monitoring** | Susah track errors | Sentry/Logs terintegrasi |

---

## 1️⃣ JUNIOR LEVEL - Basic Try-Catch

### Simple Try-Except

```python
# apps/tasks/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class TaskDetailView(APIView):
    def get(self, request, pk):
        try:
            task = Task.objects.get(pk=pk, user=request.user)
            serializer = TaskSerializer(task)
            
            return Response({
                "success": True,
                "data": serializer.data
            })
        
        except Task.DoesNotExist:
            return Response({
                "success": False,
                "message": "Task not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({
                "success": False,
                "message": "An error occurred"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

### Common Django Exceptions

```python
from django.core.exceptions import (
    ValidationError,      # Validation failed
    PermissionDenied,     # Permission denied (403)
    ObjectDoesNotExist,   # Object not found (404)
)
from django.http import Http404

# Usage
try:
    task = Task.objects.get(pk=999)
except Task.DoesNotExist:
    # Handle 404
    pass

try:
    if not user.is_admin:
        raise PermissionDenied("Admin only")
except PermissionDenied:
    # Handle 403
    pass
```

---

## 2️⃣ MID LEVEL - Custom Exception Classes

### Create Custom Exceptions

```python
# apps/core/exceptions.py
from rest_framework.exceptions import APIException
from rest_framework import status

class TaskNotFoundException(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Task not found'
    default_code = 'task_not_found'


class TaskPermissionDeniedException(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'You do not have permission to access this task'
    default_code = 'task_permission_denied'


class TaskValidationException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Task validation failed'
    default_code = 'task_validation_error'


class ExternalAPIException(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'External service unavailable'
    default_code = 'external_api_error'
```

### Use Custom Exceptions

```python
# apps/tasks/services.py
from apps.core.exceptions import TaskNotFoundException, TaskPermissionDeniedException

class TaskService:
    
    @staticmethod
    def get_task(task_id, user):
        """
        Get task with permission check
        """
        try:
            task = Task.objects.get(pk=task_id)
        except Task.DoesNotExist:
            raise TaskNotFoundException(f"Task with ID {task_id} not found")
        
        # Permission check
        if task.user != user and not user.groups.filter(name='Admin').exists():
            raise TaskPermissionDeniedException()
        
        return task
    
    @staticmethod
    def update_task(task, user, validated_data):
        """
        Update task with error handling
        """
        # Permission check
        if task.user != user and not user.groups.filter(name='Admin').exists():
            raise TaskPermissionDeniedException()
        
        # Update
        for key, value in validated_data.items():
            setattr(task, key, value)
        
        try:
            task.save()
        except Exception as e:
            logger.error(f"Error saving task: {e}")
            raise TaskValidationException(f"Failed to update task: {str(e)}")
        
        return task
```

### Views (Clean)

```python
# apps/tasks/views.py
from apps.core.exceptions import TaskNotFoundException

class TaskDetailView(APIView):
    def get(self, request, pk):
        # Service raises exception if not found/no permission
        task = TaskService.get_task(pk, request.user)
        
        serializer = TaskSerializer(task)
        return Response({
            "success": True,
            "data": serializer.data
        })
```

---

## 3️⃣ MID-SENIOR LEVEL - Global Exception Handler

### Custom Exception Handler

```python
# apps/core/exception_handler.py
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from django.http import Http404
import logging

logger = logging.getLogger('apps')

def custom_exception_handler(exc, context):
    """
    Global exception handler
    
    Handles:
    - DRF exceptions (ValidationError, etc.)
    - Django exceptions (Http404, PermissionDenied)
    - Custom exceptions
    - Unhandled exceptions
    """
    
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Get request info
    request = context.get('request')
    view = context.get('view')
    
    if response is not None:
        # DRF exception (already handled)
        custom_response = format_error_response(
            success=False,
            message=get_error_message(exc),
            errors=get_error_details(response.data),
            status_code=response.status_code
        )
        
        response.data = custom_response
        
        # Log error
        log_error(exc, request, view, response.status_code)
        
    else:
        # Unhandled exception
        logger.error(
            f"Unhandled exception: {exc}",
            exc_info=True,
            extra={
                'request': request,
                'view': view.__class__.__name__ if view else None
            }
        )
        
        # Don't expose internal errors in production
        from django.conf import settings
        
        if settings.DEBUG:
            error_detail = str(exc)
        else:
            error_detail = "An unexpected error occurred. Please try again later."
        
        custom_response = format_error_response(
            success=False,
            message="Internal server error",
            errors={"detail": error_detail},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
        response = Response(
            custom_response,
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return response


def format_error_response(success, message, errors, status_code):
    """Format consistent error response"""
    return {
        "success": success,
        "message": message,
        "errors": errors,
        "status_code": status_code
    }


def get_error_message(exc):
    """Extract user-friendly error message"""
    if hasattr(exc, 'detail'):
        if isinstance(exc.detail, dict):
            # Validation error
            return "Validation failed"
        elif isinstance(exc.detail, list):
            return exc.detail[0] if exc.detail else "Error occurred"
        else:
            return str(exc.detail)
    
    return str(exc)


def get_error_details(data):
    """Format error details"""
    if isinstance(data, dict):
        return data
    elif isinstance(data, list):
        return {"detail": data}
    else:
        return {"detail": str(data)}


def log_error(exc, request, view, status_code):
    """Log error with context"""
    logger.error(
        f"API Error: {exc}",
        extra={
            'status_code': status_code,
            'path': request.path if request else None,
            'method': request.method if request else None,
            'user': request.user.id if request and request.user.is_authenticated else None,
            'view': view.__class__.__name__ if view else None
        }
    )
```

### Setup Global Handler

```python
# config/settings/base.py
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'apps.core.exception_handler.custom_exception_handler',
}
```

---

## 4️⃣ SENIOR LEVEL - Validation Error Handling

### Serializer Validation

```python
# apps/tasks/serializers.py
from rest_framework import serializers

class TaskSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'status', 'priority']
    
    def validate_title(self, value):
        """Field-level validation"""
        if len(value) < 3:
            raise serializers.ValidationError(
                "Title must be at least 3 characters"
            )
        
        if Task.objects.filter(title__iexact=value, user=self.context['request'].user).exists():
            raise serializers.ValidationError(
                "You already have a task with this title"
            )
        
        return value
    
    def validate(self, attrs):
        """Object-level validation"""
        # Check due_date not in past
        if 'due_date' in attrs:
            from django.utils import timezone
            if attrs['due_date'] < timezone.now():
                raise serializers.ValidationError({
                    "due_date": "Due date cannot be in the past"
                })
        
        # Business logic validation
        if attrs.get('status') == 'DONE' and not attrs.get('description'):
            raise serializers.ValidationError(
                "Completed tasks must have a description"
            )
        
        return attrs
```

### Handle Validation in Views

```python
class TaskCreateView(APIView):
    def post(self, request):
        serializer = TaskSerializer(data=request.data, context={'request': request})
        
        # Validation happens here
        if serializer.is_valid():
            task = serializer.save(user=request.user)
            
            return Response({
                "success": True,
                "message": "Task created successfully",
                "data": TaskSerializer(task).data
            }, status=status.HTTP_201_CREATED)
        
        # Validation errors auto-formatted by global handler
        return Response({
            "success": False,
            "message": "Validation failed",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
```

---

## 5️⃣ SENIOR LEVEL - Service Layer Error Handling

### Comprehensive Service Error Handling

```python
# apps/tasks/services.py
import logging
from django.db import transaction, DatabaseError
from apps.core.utils.audit import log_activity
from apps.core.exceptions import (
    TaskNotFoundException,
    TaskPermissionDeniedException,
    TaskValidationException
)

logger = logging.getLogger('apps')

class TaskService:
    
    @staticmethod
    @transaction.atomic
    def create_task(user, validated_data, request=None):
        """
        Create task with comprehensive error handling
        """
        try:
            logger.info(f"Creating task for user {user.id}: {validated_data.get('title')}")
            
            # Business logic validation
            if validated_data.get('priority') == 'HIGH':
                # Check if user has too many high priority tasks
                high_priority_count = Task.objects.filter(
                    user=user,
                    priority='HIGH',
                    status__in=['TODO', 'IN_PROGRESS']
                ).count()
                
                if high_priority_count >= 5:
                    raise TaskValidationException(
                        "You already have 5 high priority tasks. Complete some before adding more."
                    )
            
            # Create task
            task = Task.objects.create(user=user, **validated_data)
            
            logger.info(f"Task created successfully: ID={task.id}")
            
            # Audit log
            log_activity(
                user=user,
                action='CREATE',
                feature='task',
                description=f"Created task: {task.title}",
                request=request,
                status='SUCCESS'
            )
            
            return task
        
        except TaskValidationException:
            # Re-raise custom exceptions
            raise
        
        except DatabaseError as e:
            logger.error(f"Database error creating task: {e}", exc_info=True)
            
            log_activity(
                user=user,
                action='ERROR',
                feature='task',
                description=f"Database error: {str(e)}",
                request=request,
                status='FAILED'
            )
            
            raise TaskValidationException("Failed to create task. Please try again.")
        
        except Exception as e:
            logger.error(f"Unexpected error creating task: {e}", exc_info=True)
            
            log_activity(
                user=user,
                action='ERROR',
                feature='task',
                description=f"Error: {str(e)}",
                request=request,
                status='FAILED'
            )
            
            raise
    
    @staticmethod
    def delete_task(task, user, request=None):
        """
        Delete task with permission check
        """
        try:
            # Permission check
            if task.user != user and not user.groups.filter(name='Admin').exists():
                raise TaskPermissionDeniedException(
                    "You don't have permission to delete this task"
                )
            
            task_title = task.title
            task_id = task.id
            
            # Delete
            task.delete()
            
            logger.info(f"Task deleted: ID={task_id}, Title={task_title}")
            
            # Audit log
            log_activity(
                user=user,
                action='DELETE',
                feature='task',
                description=f"Deleted task: {task_title}",
                request=request,
                status='SUCCESS'
            )
        
        except TaskPermissionDeniedException:
            raise
        
        except Exception as e:
            logger.error(f"Error deleting task: {e}", exc_info=True)
            
            log_activity(
                user=user,
                action='ERROR',
                feature='task',
                description=f"Error deleting task: {str(e)}",
                request=request,
                status='FAILED'
            )
            
            raise TaskValidationException(f"Failed to delete task: {str(e)}")
```

---

## 6️⃣ EXPERT LEVEL - Context Managers for Error Handling

### Custom Context Manager

```python
# apps/core/context_managers.py
from contextlib import contextmanager
import logging

logger = logging.getLogger('apps')

@contextmanager
def handle_service_errors(operation_name, user=None):
    """
    Context manager untuk handle service errors
    
    Usage:
        with handle_service_errors('create_task', user=request.user):
            task = Task.objects.create(...)
    """
    try:
        logger.info(f"Starting operation: {operation_name}")
        yield
        logger.info(f"Operation completed: {operation_name}")
    
    except ValidationError as e:
        logger.warning(f"Validation error in {operation_name}: {e}")
        raise
    
    except PermissionDenied as e:
        logger.warning(f"Permission denied in {operation_name}: {e}")
        raise
    
    except Exception as e:
        logger.error(
            f"Unexpected error in {operation_name}: {e}",
            exc_info=True,
            extra={'user': user.id if user else None}
        )
        raise


# Usage
def create_task(user, data):
    with handle_service_errors('create_task', user=user):
        task = Task.objects.create(user=user, **data)
        return task
```

---

## 📋 Error Response Examples

### ✅ Validation Error (400)

```json
{
    "success": false,
    "message": "Validation failed",
    "errors": {
        "title": ["This field is required"],
        "priority": ["Invalid choice. Choose from: LOW, MEDIUM, HIGH"]
    },
    "status_code": 400
}
```

### ✅ Not Found (404)

```json
{
    "success": false,
    "message": "Task not found",
    "errors": {
        "detail": "Task with ID 999 does not exist"
    },
    "status_code": 404
}
```

### ✅ Permission Denied (403)

```json
{
    "success": false,
    "message": "Permission denied",
    "errors": {
        "detail": "You don't have permission to delete this task"
    },
    "status_code": 403
}
```

### ✅ Unauthorized (401)

```json
{
    "success": false,
    "message": "Authentication failed",
    "errors": {
        "detail": "Authentication credentials were not provided"
    },
    "status_code": 401
}
```

### ✅ Server Error (500)

```json
{
    "success": false,
    "message": "Internal server error",
    "errors": {
        "detail": "An unexpected error occurred. Please try again later."
    },
    "status_code": 500
}
```

---

## 🎯 Best Practices

### 1. Don't Expose Sensitive Info

```python
# ❌ Bad: Expose internal details
raise Exception(f"Database connection failed: host=db.internal.com, user=admin")

# ✅ Good: Generic message
raise APIException("Service temporarily unavailable")
```

### 2. Log Errors with Context

```python
logger.error(
    "Task creation failed",
    exc_info=True,
    extra={
        'user_id': user.id,
        'task_data': validated_data,
        'request_path': request.path
    }
)
```

### 3. Use Specific Exceptions

```python
# ❌ Bad: Generic exception
raise Exception("Something went wrong")

# ✅ Good: Specific exception
raise TaskNotFoundException(f"Task {task_id} not found")
```

### 4. Clean Up Resources

```python
try:
    file = open('data.txt')
    process_file(file)
except Exception as e:
    logger.error(f"Error: {e}")
finally:
    file.close()  # Always cleanup

# Or use context manager
with open('data.txt') as file:
    process_file(file)  # Auto-cleanup
```

---

## 🔍 Debugging Tips

### Enable Django Debug Toolbar

```bash
pip install django-debug-toolbar
```

```python
# settings/development.py
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1']
```

### Pretty Print Errors in Shell

```python
import traceback

try:
    # Code that might fail
    risky_operation()
except Exception as e:
    traceback.print_exc()  # Full traceback
```

---

## 📊 Quick Reference

| HTTP Status | Exception | Use Case |
|------------|-----------|----------|
| **400** | ValidationError | Invalid input |
| **401** | NotAuthenticated | Missing/invalid auth |
| **403** | PermissionDenied | Insufficient permissions |
| **404** | NotFound / DoesNotExist | Resource not found |
| **409** | Conflict | Duplicate resource |
| **429** | Throttled | Rate limit exceeded |
| **500** | Exception | Server error |
| **503** | ServiceUnavailable | External service down |

---

## 💡 Summary

| Level | Approach |
|-------|----------|
| **Junior** | Basic try-catch di views |
| **Mid** | Custom exception classes |
| **Mid-Senior** | Global exception handler |
| **Senior** | Service layer error handling + audit |
| **Expert** | Context managers + comprehensive logging |

**Golden Rule:** 
- ✅ Handle errors gracefully
- ✅ Log with context
- ✅ Don't expose sensitive info
- ✅ Provide helpful error messages
