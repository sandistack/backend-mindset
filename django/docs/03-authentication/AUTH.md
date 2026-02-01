# 🔐 Authentication - JWT & Token Authentication

## Kenapa Penting?

Authentication adalah gerbang utama API. Tanpa auth yang benar:
- ❌ Data user bisa diakses siapa saja
- ❌ Tidak bisa track siapa yang melakukan apa
- ❌ Vulnerable terhadap serangan

---

## 📚 Daftar Isi

1. [Session vs Token Authentication](#1️⃣-session-vs-token-authentication)
2. [JWT Basics](#2️⃣-jwt-basics)
3. [SimpleJWT Setup](#3️⃣-simplejwt-setup)
4. [Custom User Model](#4️⃣-custom-user-model)
5. [Login & Registration](#5️⃣-login--registration)
6. [Token Refresh Strategy](#6️⃣-token-refresh-strategy)
7. [Token Blacklisting](#7️⃣-token-blacklisting)
8. [Custom Claims](#8️⃣-custom-claims)
9. [OAuth2 & Social Auth](#9️⃣-oauth2--social-auth)
10. [Multi-Device Management](#🔟-multi-device-management)

---

## 1️⃣ Session vs Token Authentication

### Session-Based (Traditional Web)

```
Client -> Login -> Server creates session -> Store in DB
Client <- Session ID in cookie
Client -> Request + Cookie -> Server validates session in DB
```

**Pros:** Simple, built-in Django support
**Cons:** Stateful, not scalable, CSRF issues

### Token-Based (Modern API)

```
Client -> Login -> Server generates JWT
Client <- JWT token
Client -> Request + Bearer token -> Server validates JWT (stateless)
```

**Pros:** Stateless, scalable, mobile-friendly
**Cons:** Token management, can't invalidate easily

---

## 2️⃣ JWT Basics

### JWT Structure

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.   <- Header
eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6..   <- Payload
SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c  <- Signature
```

### Header
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

### Payload (Claims)
```json
{
  "user_id": 123,
  "email": "user@example.com",
  "exp": 1699999999,
  "iat": 1699996399,
  "jti": "unique-token-id"
}
```

### Token Types

| Token | Lifetime | Purpose |
|-------|----------|---------|
| **Access Token** | 5-60 minutes | API authentication |
| **Refresh Token** | 7-30 days | Get new access token |

---

## 3️⃣ SimpleJWT Setup

### Installation

```bash
pip install djangorestframework-simplejwt
```

### Configuration

```python
# config/settings/base.py
INSTALLED_APPS = [
    # ...
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',  # Optional
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# JWT Settings
from datetime import timedelta

SIMPLE_JWT = {
    # Token Lifetimes
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    
    # Algorithm
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    
    # Token Settings
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    # Token Classes
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    
    # Sliding Token (Optional)
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=15),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=7),
}
```

### URLs

```python
# apps/authentication/urls.py
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
    TokenBlacklistView,
)

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('logout/', TokenBlacklistView.as_view(), name='token_blacklist'),
]
```

---

## 4️⃣ Custom User Model

### JUNIOR: Basic Custom User

```python
# apps/authentication/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user dengan email sebagai username"""
    
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True)
    is_verified = models.BooleanField(default=False)
    
    # Use email instead of username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
    
    def __str__(self):
        return self.email
```

```python
# config/settings/base.py
AUTH_USER_MODEL = 'authentication.User'
```

### MID: Custom User Manager

```python
# apps/authentication/models.py
from django.contrib.auth.models import AbstractUser, BaseUserManager


class UserManager(BaseUserManager):
    """Custom manager untuk User model"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        
        return self.create_user(email, password, **extra_fields)
    
    def active(self):
        """Get active users only"""
        return self.filter(is_active=True)
    
    def verified(self):
        """Get verified users only"""
        return self.filter(is_verified=True, is_active=True)


class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True)
    is_verified = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    objects = UserManager()
```

---

## 5️⃣ Login & Registration

### Registration Serializer

```python
# apps/authentication/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password_confirm', 'phone']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password": "Password fields didn't match."
            })
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'phone', 'avatar', 'is_verified']
        read_only_fields = ['id', 'is_verified']
```

### Registration View

```python
# apps/authentication/views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, UserSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens for immediate login
        refresh = RefreshToken.for_user(user)
        
        return Response({
            "success": True,
            "message": "Registration successful",
            "data": {
                "user": UserSerializer(user).data,
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                }
            }
        }, status=status.HTTP_201_CREATED)
```

### Custom Login View (dengan response schema)

```python
# apps/authentication/views.py
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add user info to response
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'username': self.user.username,
            'is_verified': self.user.is_verified,
        }
        
        return data


class CustomLoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        # Wrap in standard response schema
        return Response({
            "success": True,
            "message": "Login successful",
            "data": response.data
        })
```

### Current User View

```python
# apps/authentication/views.py
class MeView(APIView):
    """Get current authenticated user"""
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response({
            "success": True,
            "message": "User retrieved successfully",
            "data": serializer.data
        })
    
    def patch(self, request):
        """Update current user profile"""
        serializer = UserSerializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            "success": True,
            "message": "Profile updated successfully",
            "data": serializer.data
        })
```

---

## 6️⃣ Token Refresh Strategy

### JUNIOR: Basic Refresh

```python
# Frontend: Store both tokens
localStorage.setItem('access_token', data.access);
localStorage.setItem('refresh_token', data.refresh);

# When access token expires (401), call refresh endpoint
POST /api/auth/refresh/
{
    "refresh": "<refresh_token>"
}
```

### MID: Automatic Token Refresh (Frontend)

```javascript
// utils/api.js
import axios from 'axios';

const api = axios.create({
    baseURL: '/api',
});

// Request interceptor: Add token to headers
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Response interceptor: Handle 401 and refresh
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;
        
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;
            
            try {
                const refreshToken = localStorage.getItem('refresh_token');
                const response = await axios.post('/api/auth/refresh/', {
                    refresh: refreshToken
                });
                
                const { access } = response.data;
                localStorage.setItem('access_token', access);
                
                // Retry original request with new token
                originalRequest.headers.Authorization = `Bearer ${access}`;
                return api(originalRequest);
            } catch (refreshError) {
                // Refresh failed, logout user
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                window.location.href = '/login';
                return Promise.reject(refreshError);
            }
        }
        
        return Promise.reject(error);
    }
);

export default api;
```

### SENIOR: Sliding Token Pattern

```python
# config/settings/base.py
SIMPLE_JWT = {
    # Use sliding tokens
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.SlidingToken',),
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=15),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=7),
}
```

```python
# apps/authentication/urls.py
from rest_framework_simplejwt.views import TokenObtainSlidingView, TokenRefreshSlidingView

urlpatterns = [
    path('login/', TokenObtainSlidingView.as_view(), name='token_obtain_sliding'),
    path('refresh/', TokenRefreshSlidingView.as_view(), name='token_refresh_sliding'),
]
```

---

## 7️⃣ Token Blacklisting

### Setup

```python
# config/settings/base.py
INSTALLED_APPS = [
    # ...
    'rest_framework_simplejwt.token_blacklist',
]

SIMPLE_JWT = {
    # ...
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
```

```bash
python manage.py migrate
```

### Logout View

```python
# apps/authentication/views.py
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError


class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({
                    "success": False,
                    "message": "Refresh token is required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response({
                "success": True,
                "message": "Logout successful"
            })
        
        except TokenError:
            return Response({
                "success": False,
                "message": "Invalid token"
            }, status=status.HTTP_400_BAD_REQUEST)


class LogoutAllDevicesView(APIView):
    """Logout from all devices by blacklisting all tokens"""
    
    def post(self, request):
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
        
        # Blacklist all outstanding tokens for this user
        tokens = OutstandingToken.objects.filter(user=request.user)
        for token in tokens:
            BlacklistedToken.objects.get_or_create(token=token)
        
        return Response({
            "success": True,
            "message": "Logged out from all devices"
        })
```

### Cleanup Expired Tokens (Management Command)

```python
# apps/authentication/management/commands/cleanup_tokens.py
from django.core.management.base import BaseCommand
from rest_framework_simplejwt.token_blacklist.management.commands import flushexpiredtokens


class Command(BaseCommand):
    help = 'Cleanup expired tokens from blacklist'
    
    def handle(self, *args, **options):
        # Use SimpleJWT's built-in command
        flushexpiredtokens.Command().handle(*args, **options)
        self.stdout.write(self.style.SUCCESS('Expired tokens cleaned up'))
```

```bash
# Run manually or via cron
python manage.py flushexpiredtokens
```

---

## 8️⃣ Custom Claims

### Add Custom Data to Token

```python
# apps/authentication/serializers.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['email'] = user.email
        token['username'] = user.username
        token['is_verified'] = user.is_verified
        
        # Add roles/permissions
        token['roles'] = list(user.groups.values_list('name', flat=True))
        token['permissions'] = list(user.get_all_permissions())
        
        return token
```

### Role-Based Custom Token

```python
# apps/authentication/serializers.py
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Determine role
        if user.is_superuser:
            role = 'admin'
        elif user.is_staff:
            role = 'staff'
        elif hasattr(user, 'company') and user.company:
            role = 'company_admin'
        else:
            role = 'user'
        
        token['role'] = role
        token['email'] = user.email
        
        # Company info for multi-tenant
        if hasattr(user, 'company') and user.company:
            token['company_id'] = user.company.id
            token['company_name'] = user.company.name
        
        return token


# Custom view
class CustomLoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
```

### Decode Token in Views

```python
# apps/core/utils.py
import jwt
from django.conf import settings


def decode_token(token):
    """Decode JWT token to get payload"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=['HS256']
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# Usage in view
class SomeView(APIView):
    def get(self, request):
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.split(' ')[1] if ' ' in auth_header else None
        
        if token:
            payload = decode_token(token)
            role = payload.get('role')
            company_id = payload.get('company_id')
```

---

## 9️⃣ OAuth2 & Social Auth

### Setup django-allauth

```bash
pip install django-allauth dj-rest-auth[with_social]
```

```python
# config/settings/base.py
INSTALLED_APPS = [
    # ...
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',
    'dj_rest_auth',
    'dj_rest_auth.registration',
]

SITE_ID = 1

# Allauth settings
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'optional'

# Social auth settings
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'APP': {
            'client_id': config('GOOGLE_CLIENT_ID'),
            'secret': config('GOOGLE_CLIENT_SECRET'),
        }
    },
    'github': {
        'SCOPE': ['user:email'],
        'APP': {
            'client_id': config('GITHUB_CLIENT_ID'),
            'secret': config('GITHUB_CLIENT_SECRET'),
        }
    },
}
```

### Social Auth URLs

```python
# apps/authentication/urls.py
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = "http://localhost:3000/auth/google/callback"
    client_class = OAuth2Client


class GitHubLogin(SocialLoginView):
    adapter_class = GitHubOAuth2Adapter
    callback_url = "http://localhost:3000/auth/github/callback"
    client_class = OAuth2Client


urlpatterns = [
    # ...
    path('social/google/', GoogleLogin.as_view(), name='google_login'),
    path('social/github/', GitHubLogin.as_view(), name='github_login'),
]
```

### Frontend OAuth Flow

```javascript
// 1. Redirect to Google
const googleAuthUrl = `https://accounts.google.com/o/oauth2/v2/auth?
    client_id=${GOOGLE_CLIENT_ID}&
    redirect_uri=${CALLBACK_URL}&
    response_type=code&
    scope=openid%20email%20profile`;

window.location.href = googleAuthUrl;

// 2. After redirect, exchange code for tokens
const response = await fetch('/api/auth/social/google/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code: authorizationCode })
});

const { access, refresh, user } = await response.json();
```

---

## 🔟 Multi-Device Management

### Device Model

```python
# apps/authentication/models.py
class UserDevice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    device_id = models.CharField(max_length=255, unique=True)
    device_name = models.CharField(max_length=255)
    device_type = models.CharField(max_length=50)  # mobile, desktop, tablet
    last_login = models.DateTimeField(auto_now=True)
    last_ip = models.GenericIPAddressField(null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_devices'
        ordering = ['-last_login']


class RefreshTokenDevice(models.Model):
    """Link refresh tokens to devices"""
    token = models.OneToOneField(
        'token_blacklist.OutstandingToken',
        on_delete=models.CASCADE
    )
    device = models.ForeignKey(
        UserDevice, 
        on_delete=models.CASCADE,
        related_name='refresh_tokens'
    )
```

### Track Device on Login

```python
# apps/authentication/serializers.py
class DeviceLoginSerializer(TokenObtainPairSerializer):
    device_id = serializers.CharField(required=False)
    device_name = serializers.CharField(required=False)
    device_type = serializers.CharField(required=False)
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Get or create device
        device_id = attrs.get('device_id') or self._generate_device_id()
        device, created = UserDevice.objects.update_or_create(
            user=self.user,
            device_id=device_id,
            defaults={
                'device_name': attrs.get('device_name', 'Unknown Device'),
                'device_type': attrs.get('device_type', 'unknown'),
                'last_ip': self.context['request'].META.get('REMOTE_ADDR'),
            }
        )
        
        data['device_id'] = device.device_id
        return data
    
    def _generate_device_id(self):
        import uuid
        return str(uuid.uuid4())
```

### List & Revoke Devices

```python
# apps/authentication/views.py
class DeviceListView(APIView):
    """List all user devices"""
    
    def get(self, request):
        devices = request.user.devices.filter(is_active=True)
        serializer = DeviceSerializer(devices, many=True)
        
        return Response({
            "success": True,
            "data": serializer.data
        })


class RevokeDeviceView(APIView):
    """Revoke access from a specific device"""
    
    def post(self, request, device_id):
        try:
            device = request.user.devices.get(device_id=device_id)
            
            # Blacklist all tokens for this device
            for token_device in device.refresh_tokens.all():
                from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
                BlacklistedToken.objects.get_or_create(token=token_device.token)
            
            device.is_active = False
            device.save()
            
            return Response({
                "success": True,
                "message": "Device access revoked"
            })
        
        except UserDevice.DoesNotExist:
            return Response({
                "success": False,
                "message": "Device not found"
            }, status=status.HTTP_404_NOT_FOUND)
```

---

## 📊 Authentication Flow Summary

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│    Login    │────▶│   Server    │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ Validate    │
                    │ Credentials │
                    └─────────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
        ┌─────────┐               ┌─────────┐
        │ Invalid │               │  Valid  │
        └─────────┘               └─────────┘
              │                         │
              ▼                         ▼
        ┌─────────┐               ┌─────────────┐
        │  401    │               │ Generate    │
        │ Error   │               │ JWT Tokens  │
        └─────────┘               └─────────────┘
                                        │
                                        ▼
                                  ┌─────────────┐
                                  │ Return      │
                                  │ Access +    │
                                  │ Refresh     │
                                  └─────────────┘
```

---

## 🎯 Best Practices

### 1. Token Security

```python
# ✅ Short-lived access tokens
'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),

# ✅ Rotate refresh tokens
'ROTATE_REFRESH_TOKENS': True,
'BLACKLIST_AFTER_ROTATION': True,

# ✅ Use HTTPS only
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
```

### 2. Password Security

```python
# config/settings/base.py
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
```

### 3. Rate Limiting

```python
# Prevent brute force
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '5/minute',  # Login attempts
    }
}
```

---

## 📋 Authentication Checklist

### Junior ✅
- [ ] Setup SimpleJWT
- [ ] Custom User model dengan email
- [ ] Login/Register endpoints
- [ ] Protected routes dengan IsAuthenticated

### Mid ✅
- [ ] Token refresh strategy
- [ ] Custom claims (role, permissions)
- [ ] Logout dengan blacklisting
- [ ] Password validation

### Senior ✅
- [ ] OAuth2/Social auth
- [ ] Multi-device management
- [ ] Device tracking & revocation
- [ ] Rate limiting pada auth endpoints

### Expert ✅
- [ ] Sliding tokens
- [ ] Token encryption (JWE)
- [ ] Refresh token rotation
- [ ] Automatic token cleanup
- [ ] Security audit logging
