# 🚀 Step 3: Caching Strategy

**Waktu:** 4-6 jam  
**Prerequisite:** Step 2 selesai

---

## 🎯 Tujuan

- Multi-layer caching strategy
- Cache invalidation patterns
- Query optimization
- Rate limiting

---

## 📋 Caching Layers

```
Request → Rate Limit Cache → View Cache → Query Cache → Database
           (Redis)           (Redis)      (Redis)      (PostgreSQL)
```

---

## 📋 Tasks

### 3.1 Cache Utilities

**Buat `apps/core/cache.py`:**

```python
from django.core.cache import cache
from functools import wraps
import hashlib
import json

def generate_cache_key(*args, **kwargs):
    """Generate consistent cache key from arguments"""
    key_data = json.dumps({'args': args, 'kwargs': kwargs}, sort_keys=True)
    hash_key = hashlib.md5(key_data.encode()).hexdigest()[:16]
    return f"cache_{hash_key}"


def cached(timeout=300, key_prefix=''):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}_{func.__name__}_{generate_cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        
        # Add method to invalidate cache
        def invalidate(*args, **kwargs):
            cache_key = f"{key_prefix}_{func.__name__}_{generate_cache_key(*args, **kwargs)}"
            cache.delete(cache_key)
        
        wrapper.invalidate = invalidate
        return wrapper
    return decorator


class CacheManager:
    """Centralized cache management"""
    
    @staticmethod
    def workspace_key(workspace_id, suffix=''):
        return f"workspace:{workspace_id}:{suffix}" if suffix else f"workspace:{workspace_id}"
    
    @staticmethod
    def document_key(document_id, suffix=''):
        return f"document:{document_id}:{suffix}" if suffix else f"document:{document_id}"
    
    @staticmethod
    def user_key(user_id, suffix=''):
        return f"user:{user_id}:{suffix}" if suffix else f"user:{user_id}"
    
    @staticmethod
    def channel_key(channel_id, suffix=''):
        return f"channel:{channel_id}:{suffix}" if suffix else f"channel:{channel_id}"
    
    # Invalidation
    @classmethod
    def invalidate_workspace(cls, workspace_id):
        """Invalidate all workspace-related caches"""
        pattern = f"workspace:{workspace_id}:*"
        cls._delete_pattern(pattern)
    
    @classmethod
    def invalidate_document(cls, document_id):
        """Invalidate document caches"""
        pattern = f"document:{document_id}:*"
        cls._delete_pattern(pattern)
    
    @staticmethod
    def _delete_pattern(pattern):
        """Delete all keys matching pattern"""
        from django_redis import get_redis_connection
        redis = get_redis_connection("default")
        
        keys = redis.keys(pattern)
        if keys:
            redis.delete(*keys)
```

**Referensi:** [CACHING.md](../../../docs/04-advanced/CACHING.md)

### 3.2 Cached Querysets

**Buat `apps/core/querysets.py`:**

```python
from django.core.cache import cache
from django.db import models

class CachedQuerySetMixin:
    """Mixin for cached querysets"""
    
    cache_timeout = 300  # 5 minutes
    
    def cache_key(self, suffix=''):
        """Generate cache key for this queryset"""
        model_name = self.model.__name__.lower()
        query_hash = hash(str(self.query))
        return f"qs:{model_name}:{query_hash}:{suffix}"
    
    def cached_list(self, timeout=None):
        """Return cached list of objects"""
        timeout = timeout or self.cache_timeout
        cache_key = self.cache_key('list')
        
        result = cache.get(cache_key)
        if result is None:
            result = list(self)
            cache.set(cache_key, result, timeout)
        
        return result
    
    def cached_count(self, timeout=None):
        """Return cached count"""
        timeout = timeout or self.cache_timeout
        cache_key = self.cache_key('count')
        
        result = cache.get(cache_key)
        if result is None:
            result = self.count()
            cache.set(cache_key, result, timeout)
        
        return result
    
    def cached_first(self, timeout=None):
        """Return cached first object"""
        timeout = timeout or self.cache_timeout
        cache_key = self.cache_key('first')
        
        result = cache.get(cache_key)
        if result is None:
            result = self.first()
            cache.set(cache_key, result, timeout)
        
        return result


class CachedManager(models.Manager):
    """Manager that returns cached querysets"""
    
    def get_queryset(self):
        return CachedQuerySet(self.model, using=self._db)


class CachedQuerySet(CachedQuerySetMixin, models.QuerySet):
    pass
```

### 3.3 View-Level Caching

**Buat `apps/core/mixins.py`:**

```python
from django.core.cache import cache
from rest_framework.response import Response

class CachedViewMixin:
    """Mixin for cached API views"""
    
    cache_timeout = 300
    cache_key_prefix = ''
    
    def get_cache_key(self, request):
        """Generate cache key from request"""
        path = request.path
        query_string = request.META.get('QUERY_STRING', '')
        user_id = request.user.id if request.user.is_authenticated else 'anon'
        
        return f"view:{self.cache_key_prefix}:{path}:{query_string}:{user_id}"
    
    def dispatch(self, request, *args, **kwargs):
        # Only cache GET requests
        if request.method != 'GET':
            return super().dispatch(request, *args, **kwargs)
        
        # Check cache
        cache_key = self.get_cache_key(request)
        cached_response = cache.get(cache_key)
        
        if cached_response:
            return Response(cached_response)
        
        # Get fresh response
        response = super().dispatch(request, *args, **kwargs)
        
        # Cache successful responses
        if response.status_code == 200:
            cache.set(cache_key, response.data, self.cache_timeout)
        
        return response
    
    def invalidate_cache(self, request):
        """Manually invalidate cache"""
        cache_key = self.get_cache_key(request)
        cache.delete(cache_key)
```

### 3.4 Apply Caching

**Contoh di `apps/workspaces/views.py`:**

```python
from apps.core.cache import CacheManager, cached
from apps.core.mixins import CachedViewMixin

class WorkspaceDetailView(CachedViewMixin, generics.RetrieveAPIView):
    """Cached workspace detail"""
    cache_timeout = 600  # 10 minutes
    cache_key_prefix = 'workspace'
    
    def get_queryset(self):
        return Workspace.objects.select_related('owner').prefetch_related('members')


class MemberListView(generics.ListAPIView):
    """List workspace members with caching"""
    
    def get_queryset(self):
        workspace_id = self.kwargs['workspace_id']
        cache_key = CacheManager.workspace_key(workspace_id, 'members')
        
        # Try cache first
        members = cache.get(cache_key)
        if members is None:
            members = list(Member.objects.filter(
                workspace_id=workspace_id
            ).select_related('user'))
            cache.set(cache_key, members, 300)
        
        return members
```

### 3.5 Cache Invalidation dengan Signals

**Buat `apps/workspaces/signals.py`:**

```python
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.core.cache import CacheManager
from .models import Workspace, Member

@receiver([post_save, post_delete], sender=Member)
def invalidate_member_cache(sender, instance, **kwargs):
    """Invalidate cache when member changes"""
    CacheManager.invalidate_workspace(instance.workspace_id)


@receiver(post_save, sender=Workspace)
def invalidate_workspace_cache(sender, instance, **kwargs):
    """Invalidate workspace cache on update"""
    CacheManager.invalidate_workspace(instance.id)
```

### 3.6 Rate Limiting

**Buat `apps/core/throttling.py`:**

```python
from rest_framework.throttling import SimpleRateThrottle

class BurstRateThrottle(SimpleRateThrottle):
    """High rate for short bursts"""
    scope = 'burst'
    rate = '60/min'


class SustainedRateThrottle(SimpleRateThrottle):
    """Lower rate for sustained usage"""
    scope = 'sustained'
    rate = '1000/hour'


class MessageRateThrottle(SimpleRateThrottle):
    """Rate limit for sending messages"""
    scope = 'message'
    rate = '30/min'
    
    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            return f"throttle_message_{request.user.id}"
        return None
```

**Di `settings/base.py`:**

```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'apps.core.throttling.BurstRateThrottle',
        'apps.core.throttling.SustainedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'burst': '60/min',
        'sustained': '1000/hour',
        'message': '30/min',
    }
}
```

---

## 📊 Caching Strategy Summary

| Data Type | Cache Time | Invalidation |
|-----------|------------|--------------|
| Workspace info | 10 min | On update |
| Member list | 5 min | On member change |
| Document content | 5 min | On save |
| User profile | 15 min | On update |
| Search results | 1 min | Time-based |
| Channel messages | 2 min | On new message |
| Notifications | No cache | Real-time |

---

## ✅ Checklist

- [ ] Cache utilities & key generation
- [ ] Cached querysets mixin
- [ ] View-level caching mixin
- [ ] Signal-based invalidation
- [ ] Rate limiting
- [ ] Cache for workspace, documents, members
- [ ] Pattern-based cache deletion

---

## 🔗 Referensi

- [CACHING.md](../../../docs/04-advanced/CACHING.md) - Complete guide

---

## ➡️ Next Step

Lanjut ke [04-BACKGROUND_JOBS.md](04-BACKGROUND_JOBS.md) - Celery Advanced Patterns
