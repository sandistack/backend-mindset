# 🚦 RATE LIMITING - Django REST Framework (Junior → Senior)

Dokumentasi lengkap tentang rate limiting/throttling di Django REST Framework.

---

## 🎯 Kenapa Rate Limiting Penting?

| Problem | Solution dengan Rate Limiting |
|---------|------------------------------|
| Brute force attack | Limit login attempts |
| DDoS attack | Limit requests per IP |
| API abuse | Limit requests per user |
| Server overload | Protect resources |
| Cost control | Limit expensive operations |

**Real World Examples:**
- Twitter API: 300 requests/15 min
- GitHub API: 5000 requests/hour
- Google Maps: $200 free/month

---

## 1️⃣ JUNIOR LEVEL - Built-in Throttling

### Global Throttling Setup

```python
# config/settings/base.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',      # Anonymous users
        'user': '1000/hour',     # Authenticated users
    }
}
```

### Throttle Rates Format

```python
'DEFAULT_THROTTLE_RATES': {
    'anon': '100/hour',
    'user': '1000/hour',
    'login': '5/minute',
    'burst': '60/minute',
    'sustained': '1000/day',
}

# Format: 'number/period'
# Periods: second, minute, hour, day
```

### Per-View Throttling

```python
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

class TaskListView(APIView):
    throttle_classes = [UserRateThrottle]
    
    def get(self, request):
        # Limited to 1000/hour per user
        return Response({'tasks': []})
```

---

## 2️⃣ MID LEVEL - Custom Throttle Classes

### Throttle untuk Operasi Spesifik

```python
# apps/core/throttling.py
from rest_framework.throttling import SimpleRateThrottle

class BurstRateThrottle(SimpleRateThrottle):
    """High rate untuk short burst"""
    scope = 'burst'
    rate = '60/minute'


class SustainedRateThrottle(SimpleRateThrottle):
    """Lower rate untuk sustained usage"""
    scope = 'sustained'
    rate = '1000/day'


class LoginRateThrottle(SimpleRateThrottle):
    """Strict rate limit untuk login attempts"""
    scope = 'login'
    rate = '5/minute'
    
    def get_cache_key(self, request, view):
        # Rate limit by IP for login
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request)
        }


class PasswordResetThrottle(SimpleRateThrottle):
    """Limit password reset requests"""
    scope = 'password_reset'
    rate = '3/hour'
    
    def get_cache_key(self, request, view):
        # Rate limit by email
        email = request.data.get('email', '')
        if email:
            return f'throttle_password_reset_{email}'
        return None


class ExpensiveOperationThrottle(SimpleRateThrottle):
    """Limit untuk operasi mahal (export, report)"""
    scope = 'expensive'
    rate = '10/hour'
    
    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            return f'throttle_expensive_{request.user.id}'
        return None
```

### Apply ke Views

```python
# apps/authentication/views.py
from apps.core.throttling import LoginRateThrottle, PasswordResetThrottle

class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]
    
    def post(self, request):
        # Max 5 attempts per minute per IP
        pass


class PasswordResetView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetThrottle]
    
    def post(self, request):
        # Max 3 requests per hour per email
        pass


# apps/reports/views.py
from apps.core.throttling import ExpensiveOperationThrottle

class ExportReportView(APIView):
    throttle_classes = [ExpensiveOperationThrottle]
    
    def post(self, request):
        # Max 10 exports per hour
        pass
```

---

## 3️⃣ MID-SENIOR LEVEL - Dynamic Rate Limiting

### User Role-Based Throttling

```python
# apps/core/throttling.py
from rest_framework.throttling import UserRateThrottle

class RoleBasedThrottle(UserRateThrottle):
    """
    Different rates based on user subscription/role
    """
    
    # Default rates per role
    THROTTLE_RATES = {
        'free': '100/hour',
        'basic': '500/hour',
        'premium': '2000/hour',
        'enterprise': '10000/hour',
        'admin': None,  # No limit
    }
    
    def get_rate(self):
        if not hasattr(self, 'request') or not self.request.user.is_authenticated:
            return '50/hour'  # Anonymous
        
        user = self.request.user
        
        # Admin = no limit
        if user.is_staff:
            return None
        
        # Get user's plan/role
        plan = getattr(user, 'subscription_plan', 'free')
        return self.THROTTLE_RATES.get(plan, '100/hour')
    
    def allow_request(self, request, view):
        self.request = request
        self.rate = self.get_rate()
        
        if self.rate is None:
            return True  # No limit
        
        self.num_requests, self.duration = self.parse_rate(self.rate)
        return super().allow_request(request, view)
    
    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            return f'throttle_role_{request.user.id}'
        return f'throttle_anon_{self.get_ident(request)}'
```

### Endpoint-Specific Rates

```python
# apps/core/throttling.py
class EndpointThrottle(SimpleRateThrottle):
    """
    Different rates per endpoint
    """
    
    ENDPOINT_RATES = {
        'task-list': '100/minute',
        'task-create': '20/minute',
        'export-report': '5/hour',
        'send-email': '10/minute',
        'upload-file': '50/hour',
    }
    
    def get_rate(self):
        view_name = getattr(self, 'view_name', 'default')
        return self.ENDPOINT_RATES.get(view_name, '60/minute')
    
    def allow_request(self, request, view):
        # Get view name from URL
        self.view_name = getattr(view, 'basename', 'default')
        self.rate = self.get_rate()
        self.num_requests, self.duration = self.parse_rate(self.rate)
        
        return super().allow_request(request, view)
    
    def get_cache_key(self, request, view):
        user_id = request.user.id if request.user.is_authenticated else self.get_ident(request)
        return f'throttle_endpoint_{self.view_name}_{user_id}'
```

---

## 4️⃣ SENIOR LEVEL - Advanced Patterns

### Sliding Window Rate Limiter

```python
# apps/core/throttling.py
from django.core.cache import cache
import time

class SlidingWindowThrottle(SimpleRateThrottle):
    """
    More accurate rate limiting using sliding window algorithm
    """
    
    scope = 'sliding'
    rate = '100/minute'
    
    def allow_request(self, request, view):
        self.key = self.get_cache_key(request, view)
        if self.key is None:
            return True
        
        self.rate = self.get_rate()
        self.num_requests, self.duration = self.parse_rate(self.rate)
        
        now = time.time()
        window_start = now - self.duration
        
        # Get current request timestamps
        request_history = cache.get(self.key, [])
        
        # Remove old requests outside window
        request_history = [ts for ts in request_history if ts > window_start]
        
        if len(request_history) >= self.num_requests:
            self.wait = self.duration - (now - request_history[0])
            return False
        
        # Add current request
        request_history.append(now)
        cache.set(self.key, request_history, self.duration)
        
        return True
    
    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            return f'sliding_throttle_{request.user.id}'
        return f'sliding_throttle_{self.get_ident(request)}'


class TokenBucketThrottle(SimpleRateThrottle):
    """
    Token bucket algorithm - allows burst but maintains average rate
    """
    
    scope = 'token_bucket'
    
    # Bucket configuration
    BUCKET_SIZE = 100  # Max tokens
    REFILL_RATE = 10   # Tokens per second
    
    def allow_request(self, request, view):
        self.key = self.get_cache_key(request, view)
        if self.key is None:
            return True
        
        now = time.time()
        bucket = cache.get(self.key, {
            'tokens': self.BUCKET_SIZE,
            'last_refill': now
        })
        
        # Refill tokens
        elapsed = now - bucket['last_refill']
        tokens_to_add = elapsed * self.REFILL_RATE
        bucket['tokens'] = min(self.BUCKET_SIZE, bucket['tokens'] + tokens_to_add)
        bucket['last_refill'] = now
        
        # Try to consume token
        if bucket['tokens'] >= 1:
            bucket['tokens'] -= 1
            cache.set(self.key, bucket, 3600)
            return True
        
        self.wait = (1 - bucket['tokens']) / self.REFILL_RATE
        cache.set(self.key, bucket, 3600)
        return False
    
    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            return f'token_bucket_{request.user.id}'
        return f'token_bucket_{self.get_ident(request)}'
```

### Rate Limit Headers

```python
# apps/core/middleware.py
class RateLimitHeadersMiddleware:
    """
    Add rate limit info to response headers
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Get throttle info from view
        if hasattr(request, 'throttle_info'):
            info = request.throttle_info
            response['X-RateLimit-Limit'] = info.get('limit', '')
            response['X-RateLimit-Remaining'] = info.get('remaining', '')
            response['X-RateLimit-Reset'] = info.get('reset', '')
        
        return response


# Custom throttle dengan header info
class ThrottleWithHeaders(UserRateThrottle):
    def allow_request(self, request, view):
        result = super().allow_request(request, view)
        
        # Store info for middleware
        request.throttle_info = {
            'limit': self.num_requests,
            'remaining': max(0, self.num_requests - len(self.history)),
            'reset': int(self.wait) if hasattr(self, 'wait') else 0
        }
        
        return result
```

### IP Whitelist/Blacklist

```python
# apps/core/throttling.py
class IPBasedThrottle(SimpleRateThrottle):
    """
    Rate limiting dengan IP whitelist/blacklist
    """
    
    WHITELIST = [
        '127.0.0.1',
        '10.0.0.0/8',  # Internal network
    ]
    
    BLACKLIST = [
        '192.168.1.100',
    ]
    
    scope = 'ip_based'
    rate = '100/minute'
    
    def allow_request(self, request, view):
        ip = self.get_ident(request)
        
        # Check blacklist first
        if self._ip_in_list(ip, self.BLACKLIST):
            return False
        
        # Whitelist = no limit
        if self._ip_in_list(ip, self.WHITELIST):
            return True
        
        return super().allow_request(request, view)
    
    def _ip_in_list(self, ip, ip_list):
        import ipaddress
        
        try:
            check_ip = ipaddress.ip_address(ip)
            for item in ip_list:
                if '/' in item:
                    if check_ip in ipaddress.ip_network(item):
                        return True
                else:
                    if ip == item:
                        return True
        except ValueError:
            pass
        
        return False
    
    def get_cache_key(self, request, view):
        return f'throttle_ip_{self.get_ident(request)}'
```

### Distributed Rate Limiting (Redis)

```python
# apps/core/throttling.py
import redis
import time

class DistributedThrottle(SimpleRateThrottle):
    """
    Rate limiting menggunakan Redis untuk distributed systems
    """
    
    scope = 'distributed'
    rate = '1000/minute'
    
    def __init__(self):
        super().__init__()
        self.redis = redis.Redis(host='localhost', port=6379, db=1)
    
    def allow_request(self, request, view):
        self.key = self.get_cache_key(request, view)
        self.rate = self.get_rate()
        self.num_requests, self.duration = self.parse_rate(self.rate)
        
        now = int(time.time())
        window_key = f'{self.key}:{now // self.duration}'
        
        # Atomic increment with expiry
        pipe = self.redis.pipeline()
        pipe.incr(window_key)
        pipe.expire(window_key, self.duration)
        count, _ = pipe.execute()
        
        if count > self.num_requests:
            self.wait = self.duration - (now % self.duration)
            return False
        
        return True
    
    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            return f'distributed_throttle_{request.user.id}'
        return f'distributed_throttle_{self.get_ident(request)}'
```

---

## 📊 Response when Throttled

```python
# Customize throttle response
# apps/core/exceptions.py
from rest_framework.views import exception_handler
from rest_framework.exceptions import Throttled

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    
    if isinstance(exc, Throttled):
        response.data = {
            'success': False,
            'error': {
                'code': 'RATE_LIMITED',
                'message': f'Request was throttled. Try again in {int(exc.wait)} seconds.',
                'retry_after': int(exc.wait)
            }
        }
        response['Retry-After'] = int(exc.wait)
    
    return response


# settings.py
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'apps.core.exceptions.custom_exception_handler',
}
```

---

## ✅ Checklist Implementasi

| Level | Fitur | Status |
|-------|-------|--------|
| Junior | Global throttling | ⬜ |
| Junior | Per-view throttling | ⬜ |
| Mid | Custom throttle classes | ⬜ |
| Mid | Login rate limit | ⬜ |
| Senior | Role-based throttling | ⬜ |
| Senior | Sliding window | ⬜ |
| Senior | Token bucket | ⬜ |
| Senior | Distributed (Redis) | ⬜ |

---

## 🔗 Referensi

- [DRF Throttling](https://www.django-rest-framework.org/api-guide/throttling/)
- [SECURITY.md](../03-authentication/SECURITY.md) - Security best practices
- [CACHING.md](CACHING.md) - Redis setup
