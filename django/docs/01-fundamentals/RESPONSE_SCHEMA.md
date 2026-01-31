# 📦 RESPONSE SCHEMA - Django REST Framework (Junior → Senior)

Dokumentasi lengkap tentang standardisasi response format di Django REST Framework.

---

## 🎯 Kenapa Response Schema Penting?

| Problem | Tanpa Standard | Dengan Standard |
|---------|---------------|----------------|
| **Consistency** | Setiap endpoint beda format | Semua endpoint format sama |
| **Frontend** | Harus handle banyak format | Handle 1 format saja |
| **Error Handling** | Susah tahu error dari mana | Clear error structure |
| **Documentation** | API docs gak jelas | Clear & predictable |

---

## ❌ Bad Response (Inconsistent)

```python
# Endpoint 1: Return object langsung
{"id": 1, "title": "Task"}

# Endpoint 2: Return list langsung
[{"id": 1}, {"id": 2}]

# Endpoint 3: Error gak jelas
{"detail": "Not found"}

# Endpoint 4: Error beda lagi
{"error": "Invalid data"}
```

**Problem:**
- Frontend harus check `if data.data` atau `if data[0]` atau `if data.id`
- Error handling chaos
- Gak tahu response success atau fail tanpa cek status code

---

## ✅ Good Response (Consistent)

Semua endpoint **WAJIB** return format ini:

```json
{
    "success": true/false,
    "message": "Human readable message",
    "data": {...} or [...],
    "errors": {...}  (optional, for validation errors),
    "pagination": {...}  (optional, for list endpoints)
}
```

---

## 1️⃣ JUNIOR LEVEL - Manual Response

### Single Object (Success)

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
                "message": "Task retrieved successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Task.DoesNotExist:
            return Response({
                "success": False,
                "message": "Task not found",
                "errors": {"detail": "Task with this ID does not exist"}
            }, status=status.HTTP_404_NOT_FOUND)
```

### List (Success)

```python
class TaskListView(APIView):
    def get(self, request):
        tasks = Task.objects.filter(user=request.user)
        serializer = TaskSerializer(tasks, many=True)
        
        return Response({
            "success": True,
            "message": "Tasks retrieved successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
```

### Create (Success)

```python
def post(self, request):
    serializer = TaskSerializer(data=request.data)
    
    if serializer.is_valid():
        task = serializer.save(user=request.user)
        
        return Response({
            "success": True,
            "message": "Task created successfully",
            "data": TaskSerializer(task).data
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        "success": False,
        "message": "Validation failed",
        "errors": serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)
```

### Error Response

```python
return Response({
    "success": False,
    "message": "Validation failed",
    "errors": {
        "title": ["This field is required"],
        "due_date": ["Invalid date format"]
    }
}, status=status.HTTP_400_BAD_REQUEST)
```

---

## 2️⃣ MID LEVEL - Response Helper Functions (DRY)

### Create Helper Utils

```python
# apps/core/utils/response.py
from rest_framework.response import Response
from rest_framework import status

def success_response(data=None, message="Success", status_code=status.HTTP_200_OK, **kwargs):
    """
    Standard success response
    
    Usage:
        return success_response(
            data=serializer.data,
            message="Task created successfully"
        )
    """
    response_data = {
        "success": True,
        "message": message,
        "data": data
    }
    
    # Add extra fields (pagination, meta, etc.)
    response_data.update(kwargs)
    
    return Response(response_data, status=status_code)


def error_response(message="Error occurred", errors=None, status_code=status.HTTP_400_BAD_REQUEST):
    """
    Standard error response
    
    Usage:
        return error_response(
            message="Validation failed",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    """
    response_data = {
        "success": False,
        "message": message
    }
    
    if errors:
        response_data["errors"] = errors
    
    return Response(response_data, status=status_code)


def paginated_response(data, message="Data retrieved successfully", pagination_data=None):
    """
    Standard paginated response
    
    Usage:
        return paginated_response(
            data=serializer.data,
            pagination_data={
                "count": 50,
                "current_page": 1,
                "total_pages": 5
            }
        )
    """
    response_data = {
        "success": True,
        "message": message,
        "data": data
    }
    
    if pagination_data:
        response_data["pagination"] = pagination_data
    
    return Response(response_data, status=status.HTTP_200_OK)
```

### Pakai di Views

```python
# apps/tasks/views.py
from apps.core.utils.response import success_response, error_response

class TaskDetailView(APIView):
    def get(self, request, pk):
        try:
            task = Task.objects.get(pk=pk, user=request.user)
            serializer = TaskSerializer(task)
            
            return success_response(
                data=serializer.data,
                message="Task retrieved successfully"
            )
            
        except Task.DoesNotExist:
            return error_response(
                message="Task not found",
                errors={"detail": "Task with this ID does not exist"},
                status_code=status.HTTP_404_NOT_FOUND
            )
    
    def post(self, request):
        serializer = TaskSerializer(data=request.data)
        
        if serializer.is_valid():
            task = serializer.save(user=request.user)
            
            return success_response(
                data=TaskSerializer(task).data,
                message="Task created successfully",
                status_code=status.HTTP_201_CREATED
            )
        
        return error_response(
            message="Validation failed",
            errors=serializer.errors
        )
```

---

## 3️⃣ MID-SENIOR LEVEL - Custom Renderer (Auto Wrap)

Django REST Framework punya `Response` class yang bisa di-customize via **Renderer**.

### Custom JSON Renderer

```python
# apps/core/renderers.py
from rest_framework.renderers import JSONRenderer

class StandardJSONRenderer(JSONRenderer):
    """
    Auto-wrap all responses dengan standard format
    """
    
    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render response data dengan standard format
        """
        response = renderer_context['response']
        
        # Jika sudah punya format standard, return as is
        if isinstance(data, dict) and 'success' in data:
            return super().render(data, accepted_media_type, renderer_context)
        
        # Auto-wrap response
        status_code = response.status_code
        
        if 200 <= status_code < 300:
            # Success response
            wrapped_data = {
                "success": True,
                "message": "Success",
                "data": data
            }
        else:
            # Error response
            wrapped_data = {
                "success": False,
                "message": "Error occurred",
                "errors": data
            }
        
        return super().render(wrapped_data, accepted_media_type, renderer_context)
```

### Setup di Settings

```python
# config/settings/base.py
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'apps.core.renderers.StandardJSONRenderer',
    ],
}
```

### Simplified Views

```python
# Sekarang views bisa return data langsung, auto-wrap
class TaskDetailView(APIView):
    def get(self, request, pk):
        task = get_object_or_404(Task, pk=pk, user=request.user)
        serializer = TaskSerializer(task)
        return Response(serializer.data)  # Auto-wrapped!
```

---

## 4️⃣ SENIOR LEVEL - Global Exception Handler

Handle semua error di satu tempat, consistent response format.

### Custom Exception Handler

```python
# apps/core/exceptions.py
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from django.core.exceptions import PermissionDenied
import logging

logger = logging.getLogger('apps')

def custom_exception_handler(exc, context):
    """
    Custom exception handler untuk consistent error response
    
    Handles:
    - DRF exceptions (ValidationError, etc.)
    - Django exceptions (Http404, PermissionDenied)
    - Unhandled exceptions
    """
    
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Now add the custom format
    if response is not None:
        custom_response = {
            "success": False,
            "message": get_error_message(exc),
            "errors": get_error_details(response.data)
        }
        
        response.data = custom_response
        
    else:
        # Unhandled exception (500)
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        
        custom_response = {
            "success": False,
            "message": "Internal server error",
            "errors": {"detail": "An unexpected error occurred"}
        }
        
        response = Response(custom_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return response


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
```

### Setup di Settings

```python
# config/settings/base.py
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'apps.core.exceptions.custom_exception_handler',
}
```

### Benefits

```python
# Sekarang semua error auto-formatted:

# 1. Validation error
{"title": ["This field is required"]}
# Menjadi:
{
    "success": false,
    "message": "Validation failed",
    "errors": {"title": ["This field is required"]}
}

# 2. 404 error
{"detail": "Not found"}
# Menjadi:
{
    "success": false,
    "message": "Not found",
    "errors": {"detail": "Not found"}
}

# 3. Permission denied
{"detail": "You do not have permission"}
# Menjadi:
{
    "success": false,
    "message": "You do not have permission",
    "errors": {"detail": "You do not have permission"}
}
```

---

## 5️⃣ SENIOR LEVEL - Pagination Response

### Standard Pagination Format

```json
{
    "success": true,
    "message": "Tasks retrieved successfully",
    "data": [...],
    "pagination": {
        "count": 50,
        "current_page": 2,
        "total_pages": 5,
        "page_size": 10,
        "next": true,
        "previous": true,
        "next_url": "http://api.com/tasks?page=3",
        "previous_url": "http://api.com/tasks?page=1"
    }
}
```

### Custom Pagination Class

```python
# apps/core/pagination.py
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class StandardPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            "success": True,
            "message": "Data retrieved successfully",
            "data": data,
            "pagination": {
                "count": self.page.paginator.count,
                "current_page": self.page.number,
                "total_pages": self.page.paginator.num_pages,
                "page_size": self.page_size,
                "next": self.page.has_next(),
                "previous": self.page.has_previous(),
                "next_url": self.get_next_link(),
                "previous_url": self.get_previous_link()
            }
        })
```

### Pakai di Views

```python
# apps/tasks/views.py
from apps.core.pagination import StandardPagination

class TaskListView(APIView):
    pagination_class = StandardPagination
    
    def get(self, request):
        tasks = Task.objects.filter(user=request.user)
        
        paginator = self.pagination_class()
        paginated_tasks = paginator.paginate_queryset(tasks, request)
        
        serializer = TaskSerializer(paginated_tasks, many=True)
        
        return paginator.get_paginated_response(serializer.data)
```

---

## 📋 Complete Response Examples

### ✅ Success Responses

```json
// 1. Single object (GET /tasks/1/)
{
    "success": true,
    "message": "Task retrieved successfully",
    "data": {
        "id": 1,
        "title": "Buy milk",
        "status": "TODO"
    }
}

// 2. List (GET /tasks/)
{
    "success": true,
    "message": "Tasks retrieved successfully",
    "data": [
        {"id": 1, "title": "Task 1"},
        {"id": 2, "title": "Task 2"}
    ]
}

// 3. Create (POST /tasks/)
{
    "success": true,
    "message": "Task created successfully",
    "data": {
        "id": 3,
        "title": "New task"
    }
}

// 4. Update (PUT /tasks/1/)
{
    "success": true,
    "message": "Task updated successfully",
    "data": {
        "id": 1,
        "title": "Updated task"
    }
}

// 5. Delete (DELETE /tasks/1/)
{
    "success": true,
    "message": "Task deleted successfully",
    "data": null
}

// 6. Paginated list
{
    "success": true,
    "message": "Tasks retrieved successfully",
    "data": [...],
    "pagination": {
        "count": 50,
        "current_page": 1,
        "total_pages": 5
    }
}
```

### ❌ Error Responses

```json
// 1. Validation error (400)
{
    "success": false,
    "message": "Validation failed",
    "errors": {
        "title": ["This field is required"],
        "due_date": ["Invalid date format"]
    }
}

// 2. Not found (404)
{
    "success": false,
    "message": "Task not found",
    "errors": {
        "detail": "Task with ID 999 does not exist"
    }
}

// 3. Unauthorized (401)
{
    "success": false,
    "message": "Authentication credentials were not provided",
    "errors": {
        "detail": "Authentication credentials were not provided"
    }
}

// 4. Permission denied (403)
{
    "success": false,
    "message": "You do not have permission to perform this action",
    "errors": {
        "detail": "You do not have permission to perform this action"
    }
}

// 5. Server error (500)
{
    "success": false,
    "message": "Internal server error",
    "errors": {
        "detail": "An unexpected error occurred"
    }
}
```

---

## 🎯 Best Practices

| Practice | ✅ Do | ❌ Don't |
|----------|-------|---------|
| **Consistency** | Semua endpoint format sama | Setiap endpoint beda |
| **Status Code** | Pakai HTTP status yang tepat | Selalu return 200 |
| **Error Messages** | User-friendly messages | Technical stack trace |
| **Data Wrapping** | Always wrap dengan `{success, message, data}` | Return data mentah |
| **Null Handling** | `"data": null` untuk empty | `"data": {}` atau skip field |
| **Pagination** | Include pagination metadata | Return array saja |

---

## 📊 Progression Summary

| Level | Approach |
|-------|----------|
| **Junior** | Manual response di setiap endpoint |
| **Mid** | Helper functions (DRY) |
| **Mid-Senior** | Custom Renderer (auto-wrap) |
| **Senior** | Global Exception Handler + Custom Pagination |

---

## 🚀 Recommended Setup (Senior Level)

```python
# 1. Custom Exception Handler
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'apps.core.exceptions.custom_exception_handler',
}

# 2. Response helpers (manual control when needed)
from apps.core.utils.response import success_response, error_response

# 3. Standard pagination
from apps.core.pagination import StandardPagination

# 4. Consistent di semua endpoints
```

**Result:** Clean, consistent, maintainable API! 🎉
