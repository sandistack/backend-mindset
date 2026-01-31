# 🔄 MIDDLEWARE - Django (Junior → Senior)

Dokumentasi lengkap tentang Django Middleware.

---

## 🎯 Apa itu Middleware?

**Middleware** = Layer yang memproses request **sebelum** masuk view dan response **setelah** keluar view.

```
HTTP Request
    ↓
[Middleware 1] ← Process request
    ↓
[Middleware 2]
    ↓
[View] ← Handle request
    ↓
[Middleware 2] ← Process response
    ↓
[Middleware 1]
    ↓
HTTP Response
```

---

## 🔧 Built-in Django Middleware

```python
# config/settings/base.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',        # Security headers
    'django.contrib.sessions.middleware.SessionMiddleware', # Session handling
    'django.middleware.common.CommonMiddleware',            # Common operations
    'django.middleware.csrf.CsrfViewMiddleware',            # CSRF protection
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # Auth
    'django.contrib.messages.middleware.MessageMiddleware', # Flash messages
    'django.middleware.clickjacking.XFrameOptionsMiddleware',  # Clickjacking
]
```

---

## 1️⃣ JUNIOR LEVEL - Simple Function Middleware

### Basic Middleware

```python
# apps/core/middleware.py

def simple_middleware(get_response):
    """
    Simple middleware function
    """
    
    # One-time configuration (on startup)
    print("Middleware initialized")
    
    def middleware(request):
        # Code executed BEFORE view
        print(f"Request: {request.method} {request.path}")
        
        # Call next middleware/view
        response = get_response(request)
        
        # Code executed AFTER view
        print(f"Response: {response.status_code}")
        
        return response
    
    return middleware
```

### Register Middleware

```python
# config/settings/base.py
MIDDLEWARE = [
    ...
    'apps.core.middleware.simple_middleware',  # ← Add at bottom
]
```

---

## 2️⃣ MID LEVEL - Class-Based Middleware

### Request Logging Middleware

```python
# apps/core/middleware.py
import logging
import time

logger = logging.getLogger('apps')

class RequestLoggingMiddleware:
    """
    Log every HTTP request
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Start timer
        start_time = time.time()
        
        # Log request
        logger.info(
            f"REQUEST: {request.method} {request.path}",
            extra={
                'user': request.user.id if request.user.is_authenticated else None,
                'ip': self.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')
            }
        )
        
        # Process request
        response = self.get_response(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            f"RESPONSE: {response.status_code} | {duration:.3f}s",
            extra={
                'path': request.path,
                'method': request.method,
                'status_code': response.status_code,
                'duration': duration
            }
        )
        
        return response
    
    def get_client_ip(self, request):
        """Extract client IP"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
```

---

## 3️⃣ MID-SENIOR LEVEL - Authentication Middleware

### Custom JWT Middleware

```python
# apps/core/middleware.py
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError

User = get_user_model()

class CustomJWTAuthenticationMiddleware:
    """
    Custom JWT authentication middleware
    Checks token di semua endpoints (alternative ke DRF permission classes)
    """
    
    # Whitelist paths yang gak butuh auth
    WHITELIST = [
        '/api/auth/login/',
        '/api/auth/register/',
        '/admin/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip whitelist
        if any(request.path.startswith(path) for path in self.WHITELIST):
            return self.get_response(request)
        
        # Get token from header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            return JsonResponse({
                'success': False,
                'message': 'Authentication required',
                'errors': {'detail': 'No authentication token provided'}
            }, status=401)
        
        token = auth_header.split(' ')[1]
        
        try:
            # Decode token
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            
            # Get user
            user = User.objects.get(id=user_id)
            
            # Attach user to request
            request.user = user
            request.user.is_authenticated = True
            
        except TokenError as e:
            return JsonResponse({
                'success': False,
                'message': 'Invalid token',
                'errors': {'detail': str(e)}
            }, status=401)
        
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'User not found',
                'errors': {'detail': 'User associated with token does not exist'}
            }, status=401)
        
        return self.get_response(request)
```

---

## 4️⃣ SENIOR LEVEL - Rate Limiting Middleware

### Simple Rate Limiter

```python
# apps/core/middleware.py
from django.core.cache import cache
from django.http import JsonResponse
import hashlib

class RateLimitMiddleware:
    """
    Rate limit requests per IP
    """
    
    # Rate limits per minute
    RATE_LIMITS = {
        'default': 60,      # 60 requests/minute
        '/api/auth/login/': 5,   # 5 login attempts/minute
        '/api/tasks/': 30,       # 30 task operations/minute
    }
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Get client IP
        ip = self.get_client_ip(request)
        
        # Generate cache key
        cache_key = self.get_cache_key(ip, request.path)
        
        # Get rate limit for path
        rate_limit = self.get_rate_limit(request.path)
        
        # Get current count
        current_count = cache.get(cache_key, 0)
        
        # Check rate limit
        if current_count >= rate_limit:
            return JsonResponse({
                'success': False,
                'message': 'Rate limit exceeded',
                'errors': {
                    'detail': f'Too many requests. Limit: {rate_limit}/minute'
                }
            }, status=429)
        
        # Increment counter
        cache.set(cache_key, current_count + 1, 60)  # 60 seconds TTL
        
        # Add rate limit headers
        response = self.get_response(request)
        response['X-RateLimit-Limit'] = str(rate_limit)
        response['X-RateLimit-Remaining'] = str(rate_limit - current_count - 1)
        
        return response
    
    def get_cache_key(self, ip, path):
        """Generate unique cache key"""
        key = f"rate_limit:{ip}:{path}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def get_rate_limit(self, path):
        """Get rate limit for specific path"""
        for pattern, limit in self.RATE_LIMITS.items():
            if pattern in path:
                return limit
        return self.RATE_LIMITS['default']
    
    def get_client_ip(self, request):
        """Extract client IP"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
```

### Setup Cache (Redis)

```python
# config/settings/base.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

---

## 5️⃣ SENIOR LEVEL - CORS Middleware (Custom)

### Custom CORS Middleware

```python
# apps/core/middleware.py

class CustomCORSMiddleware:
    """
    Custom CORS middleware dengan whitelist
    """
    
    ALLOWED_ORIGINS = [
        'http://localhost:3000',
        'http://localhost:8080',
        'https://myapp.com',
    ]
    
    ALLOWED_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    
    ALLOWED_HEADERS = [
        'Content-Type',
        'Authorization',
        'X-Requested-With'
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Get origin
        origin = request.META.get('HTTP_ORIGIN')
        
        # Handle preflight OPTIONS request
        if request.method == 'OPTIONS':
            response = JsonResponse({}, status=200)
        else:
            response = self.get_response(request)
        
        # Add CORS headers if origin is allowed
        if origin in self.ALLOWED_ORIGINS:
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Methods'] = ', '.join(self.ALLOWED_METHODS)
            response['Access-Control-Allow-Headers'] = ', '.join(self.ALLOWED_HEADERS)
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Max-Age'] = '3600'
        
        return response
```

---

## 6️⃣ EXPERT LEVEL - Advanced Middleware Patterns

### A) Process Exception Middleware

```python
class ExceptionHandlerMiddleware:
    """
    Catch all unhandled exceptions
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        return self.get_response(request)
    
    def process_exception(self, request, exception):
        """
        Called when view raises exception
        """
        logger.error(
            f"Unhandled exception: {exception}",
            exc_info=True,
            extra={
                'path': request.path,
                'method': request.method,
                'user': request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
            }
        )
        
        # Return custom error response
        return JsonResponse({
            'success': False,
            'message': 'Internal server error',
            'errors': {'detail': str(exception)}
        }, status=500)
```

### B) Request/Response Modification

```python
class APIVersionMiddleware:
    """
    Add API version to request and response
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Extract API version from header or URL
        api_version = request.META.get('HTTP_API_VERSION', '1.0')
        request.api_version = api_version
        
        # Process request
        response = self.get_response(request)
        
        # Add version to response headers
        response['X-API-Version'] = api_version
        
        return response
```

### C) Database Connection Middleware

```python
from django.db import connection

class QueryCountMiddleware:
    """
    Log number of database queries
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Reset query log
        from django.conf import settings
        if settings.DEBUG:
            from django.db import reset_queries
            reset_queries()
        
        # Process request
        response = self.get_response(request)
        
        # Log query count
        if settings.DEBUG:
            query_count = len(connection.queries)
            logger.info(f"DB Queries: {query_count} | Path: {request.path}")
            
            # Add to response header
            response['X-DB-Query-Count'] = str(query_count)
        
        return response
```

---

## 📊 Middleware Order Matters!

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',        # 1. Security first
    'apps.core.middleware.RateLimitMiddleware',            # 2. Rate limit early
    'django.middleware.common.CommonMiddleware',            # 3. Common ops
    'django.middleware.csrf.CsrfViewMiddleware',            # 4. CSRF check
    'apps.core.middleware.CustomJWTAuthenticationMiddleware', # 5. Auth
    'apps.core.middleware.RequestLoggingMiddleware',       # 6. Log authenticated requests
    'django.contrib.messages.middleware.MessageMiddleware', # 7. Messages
]
```

**Execution Order:**
- **Request:** Top → Bottom
- **Response:** Bottom → Top

---

## 🎯 When to Use Middleware vs Decorator?

| Use Case | Middleware | Decorator |
|----------|-----------|-----------|
| **Apply to ALL requests** | ✅ Yes | ❌ No |
| **Global concerns** (auth, logging, CORS) | ✅ Yes | ❌ No |
| **Specific views only** | ❌ No | ✅ Yes |
| **Modify request/response globally** | ✅ Yes | ❌ No |
| **Business logic** | ❌ No | ✅ Yes |

---

## 🔍 Debugging Middleware

### Debug Middleware Order

```python
class DebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        print(f"✅ {self.__class__.__name__} initialized")
    
    def __call__(self, request):
        print(f"→ {self.__class__.__name__} BEFORE")
        response = self.get_response(request)
        print(f"← {self.__class__.__name__} AFTER")
        return response
```

---

## 💡 Summary

| Level | Implementation |
|-------|---------------|
| **Junior** | Simple function middleware |
| **Mid** | Class-based middleware (logging) |
| **Mid-Senior** | Authentication middleware |
| **Senior** | Rate limiting, CORS |
| **Expert** | Exception handling, request modification |

**Key Points:**
- ✅ Middleware = global concerns
- ✅ Order matters (security first, logging last)
- ✅ Use for cross-cutting concerns
- ❌ Don't use for business logic
