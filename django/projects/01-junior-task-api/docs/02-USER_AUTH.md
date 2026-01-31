# 🔐 Step 2: User Authentication

**Waktu:** 4-6 jam  
**Prerequisite:** Step 1 selesai

---

## 🎯 Tujuan

- Membuat Custom User Model (email-based)
- Setup JWT Authentication
- Implementasi Register, Login, Logout
- Password Reset functionality

---

## 📋 Tasks

### 2.1 Custom User Model

**Kenapa Custom User?**
- Default Django user pakai username, kita mau pakai email
- Lebih mudah extend di masa depan
- Best practice untuk project baru

**Referensi:** [SECURITY.md](../../../docs/03-authentication/SECURITY.md) - Custom User Model section

**Di `apps/authentication/models.py`:**

Yang harus dibuat:
1. `CustomUserManager` - extends `BaseUserManager`
   - `create_user(email, password, **extra_fields)`
   - `create_superuser(email, password, **extra_fields)`

2. `User` - extends `AbstractBaseUser, PermissionsMixin`
   - Fields: `email`, `name`, `is_active`, `is_staff`, `date_joined`
   - `USERNAME_FIELD = 'email'`
   - `REQUIRED_FIELDS = ['name']`

**Jangan lupa:**
- Set `AUTH_USER_MODEL = 'authentication.User'` di settings
- Jalankan `makemigrations` dan `migrate`

---

### 2.2 User Serializers

**Di `apps/authentication/serializers.py`:**

Buat serializers berikut:

1. **UserSerializer** - untuk response user data
   - Fields: id, email, name, date_joined
   - Read-only fields yang sensitif

2. **RegisterSerializer** - untuk registrasi
   - Fields: email, name, password, password_confirm
   - Validate email unique
   - Validate password match & strength
   - Custom `create()` method

3. **LoginSerializer** - untuk login
   - Fields: email, password
   - Validate credentials
   - Return user + tokens

4. **PasswordResetSerializer** - untuk request reset
   - Field: email
   - Validate email exists

5. **PasswordResetConfirmSerializer** - untuk confirm reset
   - Fields: token, password, password_confirm
   - Validate token valid
   - Validate password match

**Referensi:** [SERIALIZERS.md](../../../docs/02-database/SERIALIZERS.md)

---

### 2.3 Authentication Views

**Di `apps/authentication/views.py`:**

Buat views berikut:

1. **RegisterView** (generics.CreateAPIView)
   - permission_classes = [AllowAny]
   - Gunakan RegisterSerializer
   - Return user data + tokens

2. **LoginView** (generics.GenericAPIView)
   - permission_classes = [AllowAny]
   - Authenticate user
   - Return tokens

3. **LogoutView** (generics.GenericAPIView)
   - Blacklist refresh token
   - Return success message

4. **MeView** (generics.RetrieveUpdateAPIView)
   - Get/update current user profile
   - permission_classes = [IsAuthenticated]

5. **PasswordResetView** (generics.GenericAPIView)
   - Generate reset token
   - (Untuk sekarang, print token ke console)

6. **PasswordResetConfirmView** (generics.GenericAPIView)
   - Verify token & update password

---

### 2.4 URLs

**Di `apps/authentication/urls.py`:**

```python
urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', MeView.as_view(), name='me'),
    path('password-reset/', PasswordResetView.as_view(), name='password-reset'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    
    # JWT token endpoints
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]
```

**Di `config/urls.py`:**

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.authentication.urls')),
]
```

---

### 2.5 JWT Configuration

**Di `settings/base.py`:**

Konfigurasi `SIMPLE_JWT`:
- `ACCESS_TOKEN_LIFETIME`: 15-60 menit
- `REFRESH_TOKEN_LIFETIME`: 1-7 hari
- `ROTATE_REFRESH_TOKENS`: True (untuk security)
- `BLACKLIST_AFTER_ROTATION`: True
- `AUTH_HEADER_TYPES`: ('Bearer',)

Tambahkan ke `INSTALLED_APPS`:
- `rest_framework_simplejwt.token_blacklist`

Jalankan migrate untuk token blacklist.

---

## 📝 Response Format

Gunakan consistent response format:

**Referensi:** [RESPONSE_SCHEMA.md](../../../docs/01-fundamentals/RESPONSE_SCHEMA.md)

```json
// Success
{
    "success": true,
    "message": "Registration successful",
    "data": {
        "user": {...},
        "tokens": {
            "access": "...",
            "refresh": "..."
        }
    }
}

// Error
{
    "success": false,
    "message": "Validation error",
    "errors": {
        "email": ["Email already exists"]
    }
}
```

---

## ✅ Checklist

- [ ] Custom User model dengan email login
- [ ] Migrations applied
- [ ] Superuser bisa dibuat
- [ ] Register endpoint berfungsi
- [ ] Login endpoint return JWT tokens
- [ ] Logout blacklist token
- [ ] Token refresh berfungsi
- [ ] Me endpoint return current user
- [ ] Password reset flow lengkap

---

## 🧪 Testing Manual

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "name": "Test User", "password": "SecurePass123!", "password_confirm": "SecurePass123!"}'

# Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "SecurePass123!"}'

# Access protected endpoint
curl http://localhost:8000/api/auth/me/ \
  -H "Authorization: Bearer <access_token>"
```

---

## 🔗 Referensi

- [SECURITY.md](../../../docs/03-authentication/SECURITY.md) - JWT & security best practices
- [SERIALIZERS.md](../../../docs/02-database/SERIALIZERS.md) - Serializer patterns
- [ERROR_HANDLING.md](../../../docs/01-fundamentals/ERROR_HANDLING.md) - Error responses

---

## ➡️ Next Step

Lanjut ke [03-TASK_CRUD.md](03-TASK_CRUD.md) - Implementasi Task Model & CRUD API
