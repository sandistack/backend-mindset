# ⚡ CACHING - Django (Junior → Senior)

Dokumentasi lengkap tentang caching di Django untuk performance optimization.

---

## 🎯 Kenapa Caching?

**Without Cache:**
```
Request → Database Query (500ms) → Response
```

**With Cache:**
```
Request → Cache Hit (5ms) → Response
```

**Benefits:**
- ✅ Faster response time (100x faster)
- ✅ Reduced database load
- ✅ Better scalability
- ✅ Cost savings (fewer DB queries)

---

## 1️⃣ JUNIOR LEVEL - In-Memory Cache (Development)

### Setup (Default)

```python
# config/settings/development.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}
```

### Basic Usage

```python
from django.core.cache import cache

# Set cache
cache.set('my_key', 'my_value', timeout=300)  # 5 minutes

# Get cache
value = cache.get('my_key')

if value is None:
    # Cache miss, fetch from DB
    value = expensive_operation()
    cache.set('my_key', value, timeout=300)

print(value)

# Delete cache
cache.delete('my_key')

# Clear all cache
cache.clear()
```

---

## 2️⃣ MID LEVEL - Redis Cache (Production)

### Install Redis

```bash
# Install Redis server
# Ubuntu:
sudo apt install redis-server

# Mac:
brew install redis

# Start Redis
redis-server

# Install Python client
pip install redis django-redis
```

### Configure Redis

```python
# config/settings/production.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
        },
        'KEY_PREFIX': 'task_api',
        'TIMEOUT': 300,  # Default 5 minutes
    }
}

# Session storage in Redis (optional)
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

### Cache with Redis

```python
from django.core.cache import cache

# Cache user data
def get_user_profile(user_id):
    cache_key = f'user_profile:{user_id}'
    
    # Try cache first
    profile = cache.get(cache_key)
    
    if profile is None:
        # Cache miss, fetch from DB
        profile = User.objects.select_related('profile').get(id=user_id)
        
        # Store in cache for 1 hour
        cache.set(cache_key, profile, timeout=3600)
    
    return profile
```

---

## 3️⃣ MID-SENIOR LEVEL - View Caching

### Per-View Cache

```python
from django.views.decorators.cache import cache_page

# Cache entire view for 5 minutes
@cache_page(60 * 5)
def task_list(request):
    tasks = Task.objects.all()
    return render(request, 'tasks.html', {'tasks': tasks})


# DRF APIView
from django.utils.decorators import method_decorator

class TaskListView(APIView):
    
    @method_decorator(cache_page(60 * 5))
    def get(self, request):
        tasks = Task.objects.all()
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)
```

### Vary Cache by User

```python
from django.views.decorators.vary import vary_on_headers

# Cache per user (different cache for each user)
@cache_page(60 * 5)
@vary_on_headers('Authorization')  # Vary by JWT token
def my_tasks(request):
    tasks = Task.objects.filter(user=request.user)
    return Response(TaskSerializer(tasks, many=True).data)
```

---

## 4️⃣ SENIOR LEVEL - Query Caching

### Cache Expensive Queries

```python
# apps/tasks/services.py
from django.core.cache import cache

class TaskService:
    
    @staticmethod
    def get_task_statistics(user):
        """
        Expensive aggregation query
        """
        cache_key = f'task_stats:{user.id}'
        
        # Try cache
        stats = cache.get(cache_key)
        
        if stats is None:
            # Expensive query
            from django.db.models import Count, Q
            
            stats = Task.objects.filter(user=user).aggregate(
                total=Count('id'),
                todo=Count('id', filter=Q(status='TODO')),
                in_progress=Count('id', filter=Q(status='IN_PROGRESS')),
                done=Count('id', filter=Q(status='DONE')),
            )
            
            # Cache for 10 minutes
            cache.set(cache_key, stats, timeout=600)
        
        return stats
```

### Invalidate Cache on Update

```python
class TaskService:
    
    @staticmethod
    def create_task(user, validated_data):
        # Create task
        task = Task.objects.create(user=user, **validated_data)
        
        # Invalidate user's task stats cache
        cache_key = f'task_stats:{user.id}'
        cache.delete(cache_key)
        
        return task
    
    @staticmethod
    def update_task(task, validated_data):
        # Update task
        for key, value in validated_data.items():
            setattr(task, key, value)
        task.save()
        
        # Invalidate cache
        cache_key = f'task_stats:{task.user.id}'
        cache.delete(cache_key)
        
        return task
```

---

## 5️⃣ SENIOR LEVEL - Template Fragment Caching

### Cache Expensive Template Parts

```django
{% load cache %}

<!-- Cache this section for 10 minutes -->
{% cache 600 sidebar request.user.id %}
    <div class="sidebar">
        {% for task in tasks %}
            <div>{{ task.title }}</div>
        {% endfor %}
    </div>
{% endcache %}

<!-- Cache with dynamic key -->
{% cache 300 task_detail task.id task.updated_at %}
    <div class="task-detail">
        <h1>{{ task.title }}</h1>
        <p>{{ task.description }}</p>
    </div>
{% endcache %}
```

---

## 6️⃣ EXPERT LEVEL - Cache Patterns

### A) Cache-Aside Pattern

```python
def get_task(task_id):
    """
    1. Check cache
    2. If miss, fetch from DB
    3. Store in cache
    """
    cache_key = f'task:{task_id}'
    
    # 1. Check cache
    task = cache.get(cache_key)
    
    if task is None:
        # 2. Cache miss, fetch from DB
        task = Task.objects.select_related('user').get(id=task_id)
        
        # 3. Store in cache
        cache.set(cache_key, task, timeout=3600)
    
    return task
```

### B) Write-Through Cache

```python
def update_task(task_id, data):
    """
    1. Update database
    2. Update cache immediately
    """
    cache_key = f'task:{task_id}'
    
    # 1. Update DB
    task = Task.objects.get(id=task_id)
    for key, value in data.items():
        setattr(task, key, value)
    task.save()
    
    # 2. Update cache
    cache.set(cache_key, task, timeout=3600)
    
    return task
```

### C) Cache with TTL (Time To Live)

```python
def get_trending_tasks():
    """
    Cache with short TTL for frequently changing data
    """
    cache_key = 'trending_tasks'
    
    tasks = cache.get(cache_key)
    
    if tasks is None:
        # Expensive query
        tasks = Task.objects.annotate(
            comment_count=Count('comments')
        ).order_by('-comment_count')[:10]
        
        # Cache for 1 minute (short TTL)
        cache.set(cache_key, tasks, timeout=60)
    
    return tasks
```

### D) Cache Warming (Pre-populate)

```python
# management/commands/warm_cache.py
from django.core.management.base import BaseCommand
from django.core.cache import cache

class Command(BaseCommand):
    help = 'Warm up cache with frequently accessed data'
    
    def handle(self, *args, **options):
        # Pre-populate cache
        users = User.objects.all()
        
        for user in users:
            # Warm task statistics
            stats = Task.objects.filter(user=user).aggregate(
                total=Count('id'),
                todo=Count('id', filter=Q(status='TODO')),
            )
            
            cache_key = f'task_stats:{user.id}'
            cache.set(cache_key, stats, timeout=3600)
        
        self.stdout.write(self.style.SUCCESS('Cache warmed successfully'))


# Run: python manage.py warm_cache
```

---

## 7️⃣ EXPERT LEVEL - Cache Decorators

### Custom Cache Decorator

```python
# apps/core/decorators.py
from django.core.cache import cache
from functools import wraps
import hashlib
import json

def cache_result(timeout=300, key_prefix=''):
    """
    Decorator to cache function result
    
    Usage:
        @cache_result(timeout=600, key_prefix='task')
        def expensive_function(user_id):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function args
            key_data = {
                'func': func.__name__,
                'args': args,
                'kwargs': kwargs
            }
            
            key_str = json.dumps(key_data, sort_keys=True)
            key_hash = hashlib.md5(key_str.encode()).hexdigest()
            
            cache_key = f'{key_prefix}:{key_hash}'
            
            # Try cache
            result = cache.get(cache_key)
            
            if result is None:
                # Cache miss, execute function
                result = func(*args, **kwargs)
                
                # Store in cache
                cache.set(cache_key, result, timeout=timeout)
            
            return result
        
        return wrapper
    return decorator


# Usage
@cache_result(timeout=600, key_prefix='user_tasks')
def get_user_tasks(user_id, status=None):
    tasks = Task.objects.filter(user_id=user_id)
    
    if status:
        tasks = tasks.filter(status=status)
    
    return list(tasks.values())
```

---

## 8️⃣ EXPERT LEVEL - Cache Invalidation Strategies

### Pattern 1: Time-Based (TTL)

```python
# Cache expires after X seconds
cache.set('key', value, timeout=300)  # 5 minutes
```

### Pattern 2: Event-Based

```python
# Invalidate on create/update/delete
from django.db.models.signals import post_save, post_delete

@receiver(post_save, sender=Task)
def invalidate_task_cache(sender, instance, **kwargs):
    # Invalidate task cache
    cache_key = f'task:{instance.id}'
    cache.delete(cache_key)
    
    # Invalidate user's task list cache
    cache_key = f'user_tasks:{instance.user.id}'
    cache.delete(cache_key)


@receiver(post_delete, sender=Task)
def invalidate_on_delete(sender, instance, **kwargs):
    cache_key = f'task:{instance.id}'
    cache.delete(cache_key)
```

### Pattern 3: Versioning

```python
def get_task_with_version(task_id):
    """
    Cache with version number
    """
    task = Task.objects.get(id=task_id)
    
    # Include updated_at in cache key
    cache_key = f'task:{task_id}:{task.updated_at.timestamp()}'
    
    cached = cache.get(cache_key)
    
    if cached is None:
        # Process task
        cached = process_task(task)
        cache.set(cache_key, cached, timeout=3600)
    
    return cached
```

---

## 📊 Cache Backend Comparison

| Backend | Speed | Persistence | Scalability | Use Case |
|---------|-------|------------|-------------|----------|
| **LocMem** | ⚡⚡⚡ Fast | ❌ No | ⭐ Single server | Development |
| **Redis** | ⚡⚡ Very Fast | ✅ Optional | ⭐⭐⭐ Excellent | Production |
| **Memcached** | ⚡⚡ Very Fast | ❌ No | ⭐⭐ Good | Production |
| **Database** | 🐢 Slow | ✅ Yes | ⭐ Poor | Legacy |
| **Filesystem** | 🐢 Slow | ✅ Yes | ⭐ Poor | Not recommended |

---

## 🎯 Best Practices

### 1. What to Cache

```python
# ✅ Good candidates
- Expensive DB queries
- API responses (GET requests)
- Computed/aggregated data
- Frequently accessed data
- Static content

# ❌ Bad candidates
- User-specific sensitive data (be careful!)
- Frequently changing data
- Large objects (> 1MB)
- Real-time data
```

### 2. Cache Key Naming

```python
# ✅ Good: Descriptive, hierarchical
'user:123:profile'
'task:456:detail'
'stats:user:123:tasks'

# ❌ Bad: Unclear, collision-prone
'u123'
'task'
'data'
```

### 3. Set Appropriate TTL

```python
# Frequently changing data: Short TTL
cache.set('trending_tasks', data, timeout=60)  # 1 minute

# Rarely changing data: Long TTL
cache.set('user_profile', data, timeout=3600)  # 1 hour

# Static data: Very long TTL
cache.set('site_config', data, timeout=86400)  # 1 day
```

### 4. Always Handle Cache Misses

```python
# ✅ Good: Handle None
value = cache.get('key')
if value is None:
    value = fetch_from_db()
    cache.set('key', value, timeout=300)

# ❌ Bad: Assume cache always hits
value = cache.get('key')
process(value)  # Error if None!
```

---

## 🔍 Monitoring & Debugging

### Cache Statistics

```python
# Redis CLI
redis-cli

# Check cache size
INFO memory

# List all keys
KEYS task_api:*

# Get key value
GET task_api:task:123

# Delete key
DEL task_api:task:123

# Flush all
FLUSHDB
```

### Django Cache Panel (Debug)

```bash
pip install django-debug-toolbar
```

```python
# Shows cache hits/misses in browser
INSTALLED_APPS += ['debug_toolbar']
```

---

## 💡 Summary

| Level | Technique |
|-------|-----------|
| **Junior** | Basic cache.get/set with LocMem |
| **Mid** | Redis cache in production |
| **Mid-Senior** | View caching, vary_on_headers |
| **Senior** | Query caching, cache invalidation |
| **Expert** | Custom decorators, cache patterns |

**Key Points:**
- ✅ Use Redis in production
- ✅ Cache expensive operations
- ✅ Set appropriate TTL
- ✅ Invalidate on updates
- ✅ Handle cache misses
- ✅ Monitor cache hit rate

**Common Pattern:**
```python
# 1. Check cache
cached = cache.get(key)

# 2. If miss, fetch & cache
if cached is None:
    cached = expensive_operation()
    cache.set(key, cached, timeout=300)

# 3. Return result
return cached
```
