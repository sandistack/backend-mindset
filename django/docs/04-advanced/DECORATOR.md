# 🎨 DECORATORS - Python & Django (Junior → Senior)

Dokumentasi lengkap tentang Python Decorators dan penggunaannya di Django.

---

## 🎯 Apa itu Decorator?

**Decorator** = Function yang "wrap" function lain untuk menambahkan functionality.

**Analogy:**
Seperti kamu beli burger, lalu wrap dengan kertas. Burgernya tetap sama, tapi sekarang ada "extra layer" (kertas pembungkus).

```python
# Tanpa decorator
def say_hello():
    print("Hello!")

# Dengan decorator (add logging)
@log_execution
def say_hello():
    print("Hello!")
```

---

## 1️⃣ JUNIOR LEVEL - Basic Decorator

### Simple Decorator

```python
def my_decorator(func):
    """
    Decorator basic
    """
    def wrapper():
        print("Before function")
        func()
        print("After function")
    return wrapper


# Pakai decorator
@my_decorator
def say_hello():
    print("Hello!")


# Call function
say_hello()

# Output:
# Before function
# Hello!
# After function
```

**What happens:**
```python
# @my_decorator adalah shortcut dari:
say_hello = my_decorator(say_hello)
```

### Decorator dengan Arguments

```python
def my_decorator(func):
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        result = func(*args, **kwargs)
        print(f"Result: {result}")
        return result
    return wrapper


@my_decorator
def add(a, b):
    return a + b


add(5, 3)

# Output:
# Calling add with args=(5, 3), kwargs={}
# Result: 8
```

---

## 2️⃣ MID LEVEL - Real World Use Cases

### A) Logging Decorator

```python
import logging
from functools import wraps

logger = logging.getLogger('apps')

def log_execution(func):
    """
    Log setiap kali function dipanggil
    """
    @wraps(func)  # Preserve original function name & docstring
    def wrapper(*args, **kwargs):
        logger.info(f"Executing {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            logger.info(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed: {e}")
            raise
    
    return wrapper


# Usage
@log_execution
def create_task(title):
    return Task.objects.create(title=title)
```

### B) Timing Decorator

```python
import time
from functools import wraps

def measure_time(func):
    """
    Measure execution time
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"{func.__name__} took {duration:.4f} seconds")
        
        return result
    
    return wrapper


# Usage
@measure_time
def slow_function():
    time.sleep(2)
    return "Done"
```

### C) Cache Decorator

```python
from functools import wraps

def cache_result(func):
    """
    Cache function result (simple memoization)
    """
    cache = {}
    
    @wraps(func)
    def wrapper(*args):
        if args in cache:
            print(f"Returning cached result for {args}")
            return cache[args]
        
        result = func(*args)
        cache[args] = result
        return result
    
    return wrapper


# Usage
@cache_result
def expensive_calculation(n):
    print(f"Computing {n}...")
    time.sleep(2)
    return n * n

expensive_calculation(5)  # Takes 2 seconds
expensive_calculation(5)  # Instant (from cache)
```

---

## 3️⃣ MID-SENIOR LEVEL - Django Decorators

### A) Require HTTP Methods

```python
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET", "POST"])
def my_view(request):
    if request.method == "GET":
        return HttpResponse("GET request")
    elif request.method == "POST":
        return HttpResponse("POST request")
```

### B) Login Required

```python
from django.contrib.auth.decorators import login_required

@login_required
def profile_view(request):
    return render(request, 'profile.html')
```

### C) Permission Required

```python
from django.contrib.auth.decorators import permission_required

@permission_required('tasks.delete_task')
def delete_all_tasks(request):
    Task.objects.all().delete()
    return HttpResponse("All tasks deleted")
```

### D) Custom Permission Decorator

```python
from functools import wraps
from django.http import HttpResponseForbidden

def admin_required(func):
    """
    Only admin can access
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden("Login required")
        
        if not request.user.groups.filter(name='Admin').exists():
            return HttpResponseForbidden("Admin access only")
        
        return func(request, *args, **kwargs)
    
    return wrapper


# Usage
@admin_required
def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')
```

---

## 4️⃣ SENIOR LEVEL - Service Layer Decorators

### A) Audit Logging Decorator

```python
# apps/core/decorators.py
import logging
from functools import wraps
from apps.core.utils.audit import log_activity

logger = logging.getLogger('apps')

def log_service_call(feature, action='EXECUTE'):
    """
    Auto-log service calls ke database
    
    Usage:
        @log_service_call(feature='task', action='CREATE')
        def create_task(user, data, request=None):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract user from args/kwargs
            user = kwargs.get('user') or (args[0] if args else None)
            request = kwargs.get('request')
            
            try:
                logger.info(f"[{feature}] {action} started by {user}")
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Log success
                log_activity(
                    user=user,
                    action=action,
                    feature=feature,
                    description=f"{func.__name__} executed successfully",
                    request=request,
                    status='SUCCESS'
                )
                
                return result
                
            except Exception as e:
                logger.error(f"[{feature}] {action} failed: {e}", exc_info=True)
                
                # Log error
                log_activity(
                    user=user,
                    action='ERROR',
                    feature=feature,
                    description=f"{func.__name__} failed: {str(e)}",
                    request=request,
                    status='FAILED'
                )
                
                raise
        
        return wrapper
    return decorator
```

**Usage:**
```python
# apps/tasks/services.py
from apps.core.decorators import log_service_call

class TaskService:
    
    @staticmethod
    @log_service_call(feature='task', action='CREATE')
    def create_task(user, validated_data, request=None):
        # No manual logging needed!
        return Task.objects.create(user=user, **validated_data)
    
    @staticmethod
    @log_service_call(feature='task', action='UPDATE')
    def update_task(task, validated_data, request=None):
        for key, value in validated_data.items():
            setattr(task, key, value)
        task.save()
        return task
```

### B) Transaction Decorator

```python
from django.db import transaction
from functools import wraps

def atomic_service(func):
    """
    Wrap service call dalam database transaction
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        with transaction.atomic():
            return func(*args, **kwargs)
    
    return wrapper


# Usage
@atomic_service
def create_task_with_tags(user, task_data, tag_names):
    # If any fails, all rollback
    task = Task.objects.create(user=user, **task_data)
    
    for tag_name in tag_names:
        tag = Tag.objects.create(name=tag_name)
        task.tags.add(tag)
    
    return task
```

### C) Retry Decorator

```python
import time
from functools import wraps

def retry(max_attempts=3, delay=1):
    """
    Retry function if it fails
    
    Usage:
        @retry(max_attempts=3, delay=2)
        def call_external_api():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    
                    if attempts >= max_attempts:
                        raise
                    
                    print(f"Attempt {attempts} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
        
        return wrapper
    return decorator


# Usage
@retry(max_attempts=3, delay=2)
def send_notification():
    # Call external API yang mungkin fail
    response = requests.post('https://api.example.com/notify')
    response.raise_for_status()
```

---

## 5️⃣ SENIOR LEVEL - Django REST Framework Decorators

### A) Custom API View Decorator

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def task_list(request):
    if request.method == 'GET':
        tasks = Task.objects.filter(user=request.user)
        serializer = TaskSerializer(tasks, many=True)
        return Response({"data": serializer.data})
    
    elif request.method == 'POST':
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({"data": serializer.data}, status=201)
        return Response({"errors": serializer.errors}, status=400)
```

### B) Custom Permission Decorator

```python
from functools import wraps
from rest_framework.response import Response
from rest_framework import status

def admin_only(func):
    """
    DRF decorator: Admin only
    """
    @wraps(func)
    def wrapper(self, request, *args, **kwargs):
        if not request.user.groups.filter(name='Admin').exists():
            return Response(
                {"error": "Admin access only"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return func(self, request, *args, **kwargs)
    
    return wrapper


# Usage in APIView
class AllTasksView(APIView):
    
    @admin_only
    def get(self, request):
        tasks = Task.objects.all()
        return Response({"data": TaskSerializer(tasks, many=True).data})
```

---

## 6️⃣ EXPERT LEVEL - Chaining Multiple Decorators

### Stack Multiple Decorators

```python
@log_execution
@measure_time
@retry(max_attempts=3)
def complex_function():
    # This function has:
    # - Logging
    # - Performance monitoring
    # - Auto-retry on failure
    ...
```

**Order matters!**
```python
# Bottom-up execution
@decorator1  # ← Executes third
@decorator2  # ← Executes second
@decorator3  # ← Executes first
def my_func():
    pass
```

### Custom Decorator with Parameters

```python
def validate_input(**expected_types):
    """
    Validate function arguments types
    
    Usage:
        @validate_input(title=str, priority=str)
        def create_task(title, priority):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate types
            for param_name, expected_type in expected_types.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    
                    if not isinstance(value, expected_type):
                        raise TypeError(
                            f"{param_name} must be {expected_type.__name__}, "
                            f"got {type(value).__name__}"
                        )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Usage
@validate_input(title=str, priority=str)
def create_task(title, priority):
    return Task.objects.create(title=title, priority=priority)

create_task("Task", "HIGH")  # ✅ Works
create_task(123, "HIGH")      # ❌ Raises TypeError
```

---

## 📊 Built-in Django Decorators Cheatsheet

| Decorator | Use Case | Example |
|-----------|----------|---------|
| `@login_required` | Require login | View protection |
| `@permission_required` | Check permission | Admin actions |
| `@require_http_methods` | Limit HTTP methods | GET/POST only |
| `@csrf_exempt` | Disable CSRF | API endpoints |
| `@cache_page(60)` | Cache view | Performance |
| `@transaction.atomic` | Database transaction | Data consistency |
| `@api_view(['GET'])` | DRF function view | REST API |

---

## 🎯 When to Use Decorators?

| Scenario | Use Decorator? |
|----------|---------------|
| Logging all service calls | ✅ Yes (DRY) |
| Authentication check | ✅ Yes (reusable) |
| Performance monitoring | ✅ Yes |
| One-time validation | ❌ No (inline better) |
| Complex business logic | ❌ No (keep in function) |
| Cross-cutting concerns | ✅ Yes (logging, auth, caching) |

---

## 📋 Best Practices

### 1. Always Use `@wraps`

```python
from functools import wraps

def my_decorator(func):
    @wraps(func)  # ← Important! Preserves function metadata
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
```

### 2. Document Decorators

```python
def my_decorator(func):
    """
    What this decorator does
    
    Args:
        func: Function to decorate
    
    Returns:
        Wrapped function
    
    Example:
        @my_decorator
        def my_func():
            pass
    """
    ...
```

### 3. Decorator Naming

```python
# ✅ Good: Clear purpose
@log_execution
@require_authentication
@measure_performance

# ❌ Bad: Unclear
@decorator1
@my_dec
@d
```

### 4. Keep Decorators Simple

```python
# ❌ Bad: Too complex
@complex_decorator_with_many_parameters(a=1, b=2, c=3, d=4, e=5)

# ✅ Good: Simple & focused
@log_execution
@measure_time
```

---

## 💡 Common Patterns

### Pattern 1: Before/After Hook

```python
def before_after(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Before
        print("Before")
        
        result = func(*args, **kwargs)
        
        # After
        print("After")
        
        return result
    return wrapper
```

### Pattern 2: Conditional Execution

```python
def execute_if(condition):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if condition:
                return func(*args, **kwargs)
            else:
                print("Condition not met, skipping execution")
                return None
        return wrapper
    return decorator
```

### Pattern 3: Modify Arguments

```python
def lowercase_args(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Convert all string args to lowercase
        new_args = [arg.lower() if isinstance(arg, str) else arg for arg in args]
        new_kwargs = {k: v.lower() if isinstance(v, str) else v for k, v in kwargs.items()}
        
        return func(*new_args, **new_kwargs)
    return wrapper
```

---

## 📚 Further Reading

- [Python Decorators PEP 318](https://www.python.org/dev/peps/pep-0318/)
- [Django Decorators Docs](https://docs.djangoproject.com/en/4.2/topics/http/decorators/)
- [Real Python - Decorators](https://realpython.com/primer-on-python-decorators/)
