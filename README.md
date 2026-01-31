# 📚 Backend Developer - Complete Summary

Rangkuman dari semua yang kita bahas untuk menjadi backend developer yang baik.

---

## 🎯 Kriteria Developer yang Dicari

| Kriteria | Arti |
|----------|------|
| **Readable** | Orang lain bisa ngerti kode kamu tanpa nanya |
| **Maintainable** | Gampang diubah tanpa rusak bagian lain |
| **Scalable** | Logic gak hancur saat data / traffic naik |
| **Testable** | Gampang di-test secara individual |
| **Secure** | Gak bocor data, gak asal trust input |
| **Predictable** | Behavior konsisten di semua endpoint |

---

## 📁 Folder Structure

Struktur yang konsisten di semua framework (Django, Express, Go):

```
project/
├── config/             # Konfigurasi app, database, environment
├── middleware/         # Interceptors (auth, logging, rate limit, error handler)
├── modules/            # Feature-based (auth, tasks, audit)
│   └── feature/
│       ├── model          # Database schema
│       ├── serializer     # Validation + format data
│       ├── service        # Business logic + logging
│       ├── controller     # Handle HTTP request/response
│       └── routes         # URL definitions
├── utils/              # Shared helpers (response, audit)
├── logs/               # File logs (auto-rotate)
└── .env                # Environment variables
```

---

## 🔄 Request Flow

```
HTTP Request
    ↓
[Routes]        → URL matching
    ↓
[Middleware]    → Auth check, rate limit, logging
    ↓
[Controller]   → Handle HTTP, call serializer & service
    ↓
[Serializer]   → Validate & sanitize input
    ↓
[Service]      → Business logic + audit logging
    ↓
[Model]        → Database operations
    ↓
[Service]      → Return result
    ↓
[Controller]   → Format & return HTTP response
```

---

## 📋 Checklist Backend Developer

### 1. Code Quality
- Naming convention konsisten (snake_case, camelCase, PascalCase)
- Single Responsibility - satu function satu tanggung jawab
- Hindari magic numbers/strings, pakai constants
- Comment secukupnya, kode yang baik self-explanatory

### 2. Architecture & Structure
- Pisahkan concerns: routing, business logic, data access
- Konsisten pakai layered architecture (Controller → Service → Model)
- Dependency injection untuk flexibility & testability

### 3. Security
- Validasi & sanitize semua input dari user
- Pakai environment variables untuk credentials
- Proper authentication (JWT) dan authorization
- Hindari SQL injection dengan ORM
- Hash password sebelum disimpan
- Jangan expose internal error details ke user

### 4. Performance
- Database indexing yang tepat
- Pagination untuk data banyak
- Efficient queries (avoid N+1)

### 5. Error Handling
- Try-catch di tempat yang tepat
- Logging yang informatif (jangan log sensitive data)
- Consistent error response format
- Custom error types/classes

### 6. Testing
- Unit test untuk business logic (service layer)
- Integration test untuk API endpoints
- Test edge cases dan error scenarios
- Aim for 80%+ coverage

### 7. Documentation
- README yang jelas
- API documentation
- Docs folder untuk internal reference

---

## 🛡️ Middleware

Middleware = interceptor yang jalan sebelum/setelah request.

| Middleware | Fungsi | Wajib? |
|-----------|--------|--------|
| **Auth** | Cek JWT token | ✅ Yes |
| **Error Handler** | Catch unhandled errors | ✅ Yes |
| **Request Logging** | Log semua HTTP requests | ✅ Yes |
| **Rate Limiter** | Prevent API abuse | ✅ Yes |
| **CORS** | Allow cross-origin requests | Situational |

**Kapan pakai middleware:**
- ✅ Global concerns (auth, logging, error handling)
- ✅ Applies to ALL / most requests

**Jangan pakai middleware untuk:**
- ❌ Business logic
- ❌ Database operations
- ❌ Feature-specific logic

---

## ✅ Validation & Serializer

Serializer = jembatan antara database dan API.

**Fungsi:**
- Validate input dari user
- Sanitize data (trim whitespace, lowercase email)
- Format output (model → JSON)
- Separate read vs write schemas

**Best Practices:**
- Validate SEMUA input sebelum masuk database
- Field-level validation (per field)
- Object-level validation (cross-field, misal password match)
- Custom error messages yang clear
- Separate serializer untuk create/update vs display

---

## 🏗️ Service Layer

Service = tempat business logic tinggal.

**Tanggung jawab:**
- Business logic & orchestration
- Audit logging (CREATE, UPDATE, DELETE)
- Permission checks
- Call model/repository untuk database

**Jangan di service:**
- ❌ HTTP handling (itu di controller)
- ❌ Input validation (itu di serializer)

**Pattern:**
```
try:
    # Business logic
    result = do_something()

    # Audit log (success)
    log_activity(user, 'CREATE', 'feature', 'description', request)

    return result

except Exception as e:
    # File log (technical detail)
    logger.error(f"Error: {e}")

    # Audit log (failed)
    log_activity(user, 'ERROR', 'feature', f'Error: {e}', request, 'FAILED')

    raise
```

---

## 📊 Response Schema

Semua endpoint harus return format yang SAMA.

### Success (Single)
```json
{
    "success": true,
    "message": "Task created successfully",
    "data": { ... }
}
```

### Success (List / Paginated)
```json
{
    "success": true,
    "message": "Tasks retrieved successfully",
    "data": [ ... ],
    "pagination": {
        "count": 50,
        "current_page": 1,
        "total_pages": 5,
        "next": true,
        "previous": false
    }
}
```

### Error
```json
{
    "success": false,
    "message": "Validation failed",
    "errors": {
        "title": ["Title must be at least 3 characters"]
    }
}
```

**Rules:**
- Jangan return data langsung tanpa wrapper
- Jangan return default framework error format
- Jangan expose internal error details ke user
- Pakai response helper functions (DRY)

---

## 📈 Pagination

Pagination = split data besar menjadi halaman kecil.

**Kenapa penting:**
- ✅ Performance: Gak load semua data sekaligus
- ✅ Scalable: Works dengan jutaan records
- ✅ UX: Faster response time

**Types:**
| Type | Best For | Example |
|------|----------|---------|
| **Page Number** | Simple apps | `?page=2&page_size=10` |
| **Limit Offset** | Flexible | `?limit=10&offset=20` |
| **Cursor** | Large datasets (1M+) | `?cursor=abc123` |

**Best Practices:**
- Default page size: 10-20
- Max page size: 100
- Always include pagination info in response

---

## 📝 Logging Strategy (Hybrid)

### File Logging → Technical logs
- **What:** Errors, app events, debug info
- **Where:** `logs/app.log`, `logs/error.log`
- **Retention:** Auto-rotate (7 hari app.log, 90 hari error.log)
- **When:** Setiap operation di service layer
- **Purpose:** Developer debugging di production

### Database Logging → Audit trail
- **What:** User activities (CREATE, UPDATE, DELETE, ERROR)
- **Where:** `audit_logs` table
- **Retention:** 90 hari (auto cleanup)
- **When:** Setiap user action yang penting
- **Purpose:** Admin monitoring, compliance, reporting

**Jangan log:**
- ❌ Passwords atau sensitive data
- ❌ Setiap READ operation (terlalu banyak)
- ❌ Internal system events yang tidak penting

**Wajib log:**
- ✅ CREATE, UPDATE, DELETE operations
- ✅ Login attempts (success & failed)
- ✅ Errors & exceptions
- ✅ Permission denied attempts

---

## 🔐 Authentication & Authorization

### Authentication = "Siapa kamu?"
- Register: Hash password, save user
- Login: Verify credentials, return JWT token
- Every protected request: Verify JWT token

### Authorization = "Apa yang boleh kamu lakukan?"
- User: Cuma akses own data
- Admin: Akses semua data
- Check permission di service layer

### JWT Flow
```
Login → Server returns { access_token, refresh_token }
    ↓
Every request → Send access_token di Authorization header
    ↓
Token expired → Use refresh_token to get new access_token
```

---

## 🗂️ Groups & Permissions vs Simple Role

| Approach | Kapan Pakai | Complexity |
|----------|-------------|-----------|
| **Simple Role** (USER, ADMIN) | Simple apps, 1-2 roles | Low |
| **Django Groups** | Complex apps, multiple roles, fine-grained permissions | Medium |
| **Custom RBAC** | Enterprise, very complex permission matrix | High |

**For Task Management API:** Simple Role cukup ✅

---

## 🔄 Mapping Konsep: Django vs Express vs Go

| Konsep | Django | Express | Go |
|--------|--------|---------|-----|
| Entry Point | manage.py | server.js | cmd/api/main.go |
| Config | settings/ | config/ | internal/config/ |
| Middleware | MIDDLEWARE list | middlewares/ | middleware/ |
| Model | models.py | *.model.js | domain/ |
| Validation | serializers.py | *.serializer.js | serializer.go (DTO) |
| Business Logic | services.py | *.service.js | service.go |
| HTTP Handler | views.py | *.controller.js | handler.go |
| Routes | urls.py | *.routes.js | routes.go |
| DB Queries | Model (built-in) | Model (built-in) | repository.go ← Extra! |
| Logger | logging module | winston | logrus / zap |
| ORM | Django ORM | Sequelize | GORM |

**Go ada Repository layer** yang Django & Express tidak punya, karena Go lebih explicit dan prefer isolasi database logic.

---

## 📚 Documentation Structure

```
docs/
├── GROUPS.md       # Django Groups & Permissions
├── LOG.md          # Logging strategies (file vs DB vs hybrid)
├── PAGINATION.md   # Pagination types & best practices
├── SCHEMA.md       # API response schema & error handling
├── TEST.md         # Testing strategies & examples
└── TIPS.md         # Quick tips & how-tos per framework
```

---

## 🚀 Project: Task Management API

Sama project, 3 framework:

| # | Framework |
|---|-----------|
| 1 | Django (Python) |
| 2 | Express (Node.js) |
| 3 | Go (Gin) |

**Fitur yang sama di semua:**
- Authentication (Register, Login, JWT)
- Task CRUD (Create, Read, Update, Delete)
- Filtering & Search
- Pagination
- Audit Logging (file + database)
- Consistent Response Schema
- Error Handling
- Rate Limiting