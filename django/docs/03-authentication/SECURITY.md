# 🔒 SECURITY - Django & DRF (Junior → Senior)

Dokumentasi lengkap tentang security best practices di Django.

---

## 🎯 OWASP Top 10 Web Security Risks

| Risk | Django Protection |
|------|------------------|
| **Injection (SQL, XSS)** | ORM, Template escaping |
| **Broken Auth** | Built-in auth system |
| **Sensitive Data Exposure** | HTTPS, hashing |
| **XML External Entities** | N/A (JSON API) |
| **Broken Access Control** | Permissions, decorators |
| **Security Misconfiguration** | Settings best practices |
| **XSS** | Template auto-escaping |
| **Insecure Deserialization** | Validation |
| **Using Components with Known Vulnerabilities** | `pip-audit` |
| **Insufficient Logging** | Audit logs |

---

## 1️⃣ JUNIOR LEVEL - Basic Security

### 1. SQL Injection Prevention

```python
# ❌ NEVER DO THIS (SQL Injection vulnerable)
Task.objects.raw(f"SELECT * FROM tasks WHERE id = {user_input}")

# ✅ ALWAYS USE ORM (Safe)
Task.objects.filter(id=user_input)

# ✅ If you must use raw SQL, use parameters
Task.objects.raw("SELECT * FROM tasks WHERE id = %s", [user_input])
```

### 2. XSS (Cross-Site Scripting) Prevention

```python
# Django templates auto-escape by default
# {{ user_input }}  → Escaped automatically

# If you need HTML (be careful!)
from django.utils.html import escape

safe_input = escape(user_input)
```

```python
# DRF automatically escapes JSON
# No additional work needed
return Response({"title": user_input})  # Safe
```

### 3. CSRF Protection

```python
# Django auto-enables CSRF protection
# config/settings/base.py
MIDDLEWARE = [
    ...
    'django.middleware.csrf.CsrfViewMiddleware',  # ← Enabled by default
]

# For AJAX requests, include CSRF token
# In HTML:
# {% csrf_token %}

# In JavaScript:
// Get CSRF token from cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Include in fetch
fetch('/api/tasks/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify({title: 'Task'})
});
```

---

## 2️⃣ MID LEVEL - Authentication & Authorization

### 1. Password Hashing (Auto by Django)

```python
from django.contrib.auth.models import User

# ❌ NEVER store plain passwords
user.password = 'plaintext'  # BAD!

# ✅ Always hash passwords
user = User.objects.create_user(
    username='john',
    password='securepassword123'  # Auto-hashed
)

# Check password
user.check_password('securepassword123')  # True
```

### 2. Password Validation

```python
# config/settings/base.py
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,  # Minimum 8 characters
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
```

### 3. Secure Token Generation

```python
# ❌ Bad: Weak token
import random
token = str(random.randint(100000, 999999))  # Predictable

# ✅ Good: Cryptographically secure
import secrets

# Generate secure random token
token = secrets.token_urlsafe(32)  # 32 bytes = 256 bits

# Generate secure random number
otp = secrets.randbelow(1000000)  # 6-digit OTP
```

---

## 3️⃣ MID-SENIOR LEVEL - HTTPS & Headers

### 1. Force HTTPS (Production)

```python
# config/settings/production.py

# Force HTTPS
SECURE_SSL_REDIRECT = True

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Secure cookies
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Prevent MIME sniffing
SECURE_CONTENT_TYPE_NOSNIFF = True

# XSS protection (browser)
SECURE_BROWSER_XSS_FILTER = True
```

### 2. Security Headers

```python
# config/settings/base.py

# X-Frame-Options (prevent clickjacking)
X_FRAME_OPTIONS = 'DENY'

# Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")

# Referrer Policy
SECURE_REFERRER_POLICY = 'same-origin'
```

Install django-csp:
```bash
pip install django-csp
```

```python
MIDDLEWARE = [
    ...
    'csp.middleware.CSPMiddleware',
]
```

---

## 4️⃣ SENIOR LEVEL - Input Validation & Sanitization

### 1. Validate All User Input

```python
# apps/tasks/serializers.py
class TaskSerializer(serializers.ModelSerializer):
    
    def validate_title(self, value):
        # Sanitize: remove leading/trailing whitespace
        value = value.strip()
        
        # Length validation
        if len(value) < 3:
            raise serializers.ValidationError("Title too short")
        
        if len(value) > 255:
            raise serializers.ValidationError("Title too long")
        
        # Check for malicious input
        dangerous_chars = ['<script>', '<?php', 'javascript:']
        for char in dangerous_chars:
            if char in value.lower():
                raise serializers.ValidationError("Invalid input")
        
        return value
    
    def validate_email(self, value):
        # Normalize email
        value = value.lower().strip()
        
        # Validate format
        from django.core.validators import validate_email
        validate_email(value)
        
        return value
```

### 2. File Upload Security

```python
# apps/core/validators.py
from django.core.exceptions import ValidationError
import magic  # pip install python-magic

def validate_file_extension(value):
    """Validate file extension"""
    import os
    ext = os.path.splitext(value.name)[1].lower()
    
    valid_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
    
    if ext not in valid_extensions:
        raise ValidationError(f'Unsupported file extension: {ext}')


def validate_file_size(value):
    """Validate file size (max 5MB)"""
    max_size = 5 * 1024 * 1024  # 5MB
    
    if value.size > max_size:
        raise ValidationError(f'File too large. Max size: 5MB')


def validate_file_content(value):
    """Validate actual file content (MIME type)"""
    # Read file content
    file_content = value.read()
    value.seek(0)  # Reset file pointer
    
    # Detect MIME type
    mime = magic.from_buffer(file_content, mime=True)
    
    allowed_mimes = ['image/jpeg', 'image/png', 'application/pdf']
    
    if mime not in allowed_mimes:
        raise ValidationError(f'Invalid file type: {mime}')


# Use in model
class Document(models.Model):
    file = models.FileField(
        upload_to='documents/',
        validators=[
            validate_file_extension,
            validate_file_size,
            validate_file_content
        ]
    )
```

### 3. Prevent Path Traversal

```python
import os
from django.conf import settings

def safe_join(base_path, user_input):
    """
    Safely join paths to prevent path traversal
    
    Prevents: ../../etc/passwd
    """
    # Normalize path
    full_path = os.path.normpath(os.path.join(base_path, user_input))
    
    # Ensure result is within base_path
    if not full_path.startswith(base_path):
        raise ValueError("Invalid path")
    
    return full_path


# Usage
def serve_user_file(request, filename):
    base = settings.MEDIA_ROOT
    safe_path = safe_join(base, filename)
    
    # Serve file
    ...
```

---

## 5️⃣ SENIOR LEVEL - Rate Limiting

### 1. django-ratelimit

```bash
pip install django-ratelimit
```

```python
# apps/authentication/views.py
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

class LoginView(APIView):
    
    @method_decorator(ratelimit(key='ip', rate='5/m', method='POST'))
    def post(self, request):
        """
        Rate limit: 5 login attempts per minute per IP
        """
        # Login logic
        ...


# Function-based view
@ratelimit(key='user', rate='10/m')
def api_endpoint(request):
    ...
```

### 2. Custom Rate Limit Middleware

```python
# apps/core/middleware.py
from django.core.cache import cache
from django.http import JsonResponse

class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Get IP
        ip = self.get_client_ip(request)
        
        # Cache key
        cache_key = f"rate_limit:{ip}"
        
        # Get request count
        count = cache.get(cache_key, 0)
        
        # Check limit
        if count >= 100:  # 100 requests/minute
            return JsonResponse({
                'error': 'Rate limit exceeded'
            }, status=429)
        
        # Increment
        cache.set(cache_key, count + 1, 60)
        
        return self.get_response(request)
```

---

## 6️⃣ EXPERT LEVEL - Advanced Security

### 1. API Key Authentication

```python
# apps/core/authentication.py
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model

User = get_user_model()

class APIKeyAuthentication(BaseAuthentication):
    """
    Custom API Key authentication
    """
    
    def authenticate(self, request):
        api_key = request.META.get('HTTP_X_API_KEY')
        
        if not api_key:
            return None
        
        try:
            # Validate API key (hash comparison)
            import hashlib
            hashed_key = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Check against stored keys
            # (In real app, store in database)
            user = User.objects.get(api_key_hash=hashed_key)
            
            return (user, None)
        
        except User.DoesNotExist:
            raise AuthenticationFailed('Invalid API key')
```

### 2. Audit Logging

```python
# Log all sensitive operations
from apps.core.utils.audit import log_activity

def delete_task(request, pk):
    task = Task.objects.get(pk=pk)
    
    # Log before delete
    log_activity(
        user=request.user,
        action='DELETE',
        feature='task',
        description=f"Deleted task: {task.title}",
        request=request,
        status='SUCCESS'
    )
    
    task.delete()
```

### 3. Secrets Management

```bash
# .env (Never commit to git!)
SECRET_KEY=your-secret-key
DB_PASSWORD=your-db-password
API_KEY=your-api-key
```

```python
# config/settings/base.py
from decouple import config

SECRET_KEY = config('SECRET_KEY')
DB_PASSWORD = config('DB_PASSWORD')

# For production, use AWS Secrets Manager or HashiCorp Vault
```

### 4. Dependency Scanning

```bash
# Check for vulnerabilities
pip install pip-audit
pip-audit

# Or use Safety
pip install safety
safety check
```

---

## 🔍 Security Checklist

### Development
- [ ] Use ORM (prevent SQL injection)
- [ ] Validate all user input
- [ ] Hash passwords (never store plain)
- [ ] Use CSRF protection
- [ ] Escape output (prevent XSS)
- [ ] Use `.env` for secrets
- [ ] Rate limit endpoints
- [ ] Validate file uploads

### Production
- [ ] DEBUG = False
- [ ] Force HTTPS (SECURE_SSL_REDIRECT)
- [ ] Secure cookies (SESSION_COOKIE_SECURE)
- [ ] HSTS headers
- [ ] Security headers (CSP, X-Frame-Options)
- [ ] Database backups
- [ ] Monitoring & alerts
- [ ] Dependency scanning
- [ ] Regular security audits

---

## 🚨 Common Vulnerabilities & Fixes

### 1. Mass Assignment

```python
# ❌ Bad: Accept all fields from user
serializer = TaskSerializer(data=request.data)
task = serializer.save()  # User can set is_admin=True!

# ✅ Good: Whitelist fields
class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['title', 'description', 'status']  # Only these fields
        read_only_fields = ['id', 'user', 'created_at']
```

### 2. IDOR (Insecure Direct Object Reference)

```python
# ❌ Bad: No permission check
def get_task(request, pk):
    task = Task.objects.get(pk=pk)  # Any user can access any task!
    return Response(TaskSerializer(task).data)

# ✅ Good: Check ownership
def get_task(request, pk):
    task = Task.objects.get(pk=pk, user=request.user)
    return Response(TaskSerializer(task).data)
```

### 3. Information Disclosure

```python
# ❌ Bad: Expose internal errors
try:
    ...
except Exception as e:
    return Response({'error': str(e)}, status=500)  # Shows stack trace!

# ✅ Good: Generic error message
try:
    ...
except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)  # Log internally
    return Response({'error': 'Internal server error'}, status=500)
```

---

## 💡 Summary

| Level | Focus |
|-------|-------|
| **Junior** | SQL injection, XSS, CSRF basics |
| **Mid** | Password hashing, validation |
| **Mid-Senior** | HTTPS, security headers |
| **Senior** | Input sanitization, rate limiting |
| **Expert** | API keys, secrets management, auditing |

**Golden Rules:**
- ✅ Never trust user input
- ✅ Always validate & sanitize
- ✅ Use HTTPS in production
- ✅ Keep dependencies updated
- ✅ Log security events
- ✅ Principle of least privilege
