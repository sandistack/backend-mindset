# 🌐 API DESIGN - REST Best Practices (Junior → Senior)

Dokumentasi lengkap tentang mendesain REST API yang baik, konsisten, dan scalable.

---

## 🎯 Apa itu REST API?

**REST** = Representational State Transfer

**API** = Application Programming Interface

REST API adalah cara aplikasi berkomunikasi melalui HTTP:

```
Client                     Server
   │                          │
   │── GET /api/users ──────→│
   │                          │
   │←── 200 OK + data ────────│
   │                          │
```

---

## 1️⃣ JUNIOR LEVEL - HTTP Basics

### HTTP Methods

| Method | Purpose | Safe | Idempotent | Example |
|--------|---------|------|------------|---------|
| `GET` | Read data | ✅ | ✅ | Get user |
| `POST` | Create new | ❌ | ❌ | Create user |
| `PUT` | Replace entire | ❌ | ✅ | Replace user |
| `PATCH` | Partial update | ❌ | ✅ | Update email |
| `DELETE` | Remove | ❌ | ✅ | Delete user |

**Safe:** Tidak mengubah data server
**Idempotent:** Hasil sama walau dipanggil berkali-kali

### HTTP Status Codes

**2xx - Success:**
```
200 OK              - Request berhasil
201 Created         - Resource baru dibuat
204 No Content      - Berhasil, tanpa response body
```

**4xx - Client Error:**
```
400 Bad Request     - Request tidak valid
401 Unauthorized    - Belum login
403 Forbidden       - Tidak punya akses
404 Not Found       - Resource tidak ditemukan
409 Conflict        - Conflict (duplicate, etc)
422 Unprocessable   - Validation error
429 Too Many        - Rate limit exceeded
```

**5xx - Server Error:**
```
500 Internal Error  - Server error
502 Bad Gateway     - Gateway error
503 Unavailable     - Service down
504 Timeout         - Gateway timeout
```

### Basic Request/Response

```http
# Request
GET /api/users/123 HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

# Response
HTTP/1.1 200 OK
Content-Type: application/json

{
    "id": 123,
    "name": "John Doe",
    "email": "john@example.com"
}
```

---

## 2️⃣ MID LEVEL - URL Design

### Resource Naming

```bash
# ✅ Good: Nouns, plural
GET    /api/users           # List users
POST   /api/users           # Create user
GET    /api/users/123       # Get user 123
PUT    /api/users/123       # Replace user 123
PATCH  /api/users/123       # Update user 123
DELETE /api/users/123       # Delete user 123

# ❌ Bad: Verbs in URL
GET    /api/getUsers
POST   /api/createUser
POST   /api/deleteUser/123
```

### Nested Resources

```bash
# User's tasks
GET    /api/users/123/tasks         # Get user's tasks
POST   /api/users/123/tasks         # Create task for user
GET    /api/users/123/tasks/456     # Get specific task

# Alternative: Filter with query params
GET    /api/tasks?user_id=123       # Get tasks by user
```

### Query Parameters

```bash
# Filtering
GET /api/tasks?status=done
GET /api/tasks?status=done&priority=high

# Searching
GET /api/users?search=john
GET /api/users?q=john@email

# Pagination
GET /api/users?page=2&limit=20
GET /api/users?offset=20&limit=20

# Sorting
GET /api/tasks?sort=created_at
GET /api/tasks?sort=-created_at    # Descending
GET /api/tasks?sort=status,-date   # Multiple

# Field selection
GET /api/users?fields=id,name,email

# Combine all
GET /api/tasks?status=done&sort=-created_at&page=1&limit=10
```

---

## 3️⃣ MID-SENIOR LEVEL - Response Design

### Consistent Response Format

```json
// Success response
{
    "success": true,
    "message": "User created successfully",
    "data": {
        "id": 123,
        "name": "John Doe",
        "email": "john@example.com"
    }
}

// Error response
{
    "success": false,
    "message": "Validation failed",
    "errors": {
        "email": ["Email is required"],
        "password": ["Password must be at least 8 characters"]
    }
}

// List response with pagination
{
    "success": true,
    "data": [
        {"id": 1, "name": "Task 1"},
        {"id": 2, "name": "Task 2"}
    ],
    "pagination": {
        "page": 1,
        "limit": 20,
        "total_pages": 5,
        "total_items": 100
    }
}
```

### Resource Representation

```json
// Minimal (list view)
{
    "id": 123,
    "name": "John Doe"
}

// Full (detail view)
{
    "id": 123,
    "name": "John Doe",
    "email": "john@example.com",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-20T15:45:00Z",
    "profile": {
        "avatar": "https://...",
        "bio": "Software Developer"
    },
    "tasks_count": 15
}
```

### Timestamps Format

```json
// ✅ Good: ISO 8601 format (UTC)
{
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-20T15:45:00.123Z"
}

// ❌ Bad: Various formats
{
    "created_at": "15/01/2024",
    "updated_at": "January 20, 2024 3:45 PM"
}
```

---

## 4️⃣ SENIOR LEVEL - API Versioning

### URL Path Versioning

```bash
# Most common approach
GET /api/v1/users
GET /api/v2/users

# Deprecation notice in response header
X-API-Deprecation: v1 will be removed on 2025-01-01
```

### Header Versioning

```http
GET /api/users
Accept: application/vnd.myapp.v1+json

GET /api/users
Accept: application/vnd.myapp.v2+json
```

### Query Parameter Versioning

```bash
GET /api/users?version=1
GET /api/users?version=2
```

### Best Practice

```bash
# Recommended: URL versioning
/api/v1/  →  Stable version
/api/v2/  →  New version with breaking changes

# Keep both active during transition
# Deprecate old version with notice
# Remove after migration period
```

---

## 5️⃣ SENIOR LEVEL - Authentication

### API Key

```http
# In header
GET /api/users
X-API-Key: your-api-key-here

# In query (less secure)
GET /api/users?api_key=your-api-key-here
```

### Bearer Token (JWT)

```http
GET /api/users
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### OAuth 2.0 Flow

```
1. Client requests authorization
   GET /oauth/authorize?client_id=xxx&redirect_uri=xxx

2. User authorizes, redirect with code
   GET /callback?code=authorization_code

3. Exchange code for token
   POST /oauth/token
   {
       "grant_type": "authorization_code",
       "code": "authorization_code",
       "client_id": "xxx",
       "client_secret": "xxx"
   }

4. Use token for API calls
   GET /api/users
   Authorization: Bearer access_token
```

---

## 6️⃣ SENIOR LEVEL - Error Handling

### Standard Error Response

```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Validation failed",
        "details": [
            {
                "field": "email",
                "message": "Invalid email format"
            },
            {
                "field": "password",
                "message": "Password too short"
            }
        ]
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "path": "/api/users",
    "request_id": "req_abc123"
}
```

### Error Codes

```json
// Define error codes
{
    "VALIDATION_ERROR": 400,
    "UNAUTHORIZED": 401,
    "FORBIDDEN": 403,
    "NOT_FOUND": 404,
    "CONFLICT": 409,
    "RATE_LIMITED": 429,
    "INTERNAL_ERROR": 500
}

// Usage
{
    "error": {
        "code": "NOT_FOUND",
        "message": "User not found"
    }
}
```

### Problem Details (RFC 7807)

```json
{
    "type": "https://api.example.com/errors/validation",
    "title": "Validation Error",
    "status": 400,
    "detail": "The request body contains invalid data",
    "instance": "/api/users",
    "errors": [
        {
            "field": "email",
            "message": "Invalid format"
        }
    ]
}
```

---

## 7️⃣ EXPERT LEVEL - Advanced Patterns

### HATEOAS (Hypermedia)

```json
{
    "id": 123,
    "name": "Task 1",
    "status": "in_progress",
    "_links": {
        "self": {
            "href": "/api/tasks/123"
        },
        "complete": {
            "href": "/api/tasks/123/complete",
            "method": "POST"
        },
        "delete": {
            "href": "/api/tasks/123",
            "method": "DELETE"
        },
        "user": {
            "href": "/api/users/456"
        }
    }
}
```

### Bulk Operations

```bash
# Bulk create
POST /api/tasks/bulk
{
    "tasks": [
        {"title": "Task 1"},
        {"title": "Task 2"},
        {"title": "Task 3"}
    ]
}

# Bulk update
PATCH /api/tasks/bulk
{
    "ids": [1, 2, 3],
    "data": {
        "status": "done"
    }
}

# Bulk delete
DELETE /api/tasks/bulk
{
    "ids": [1, 2, 3]
}
```

### Rate Limiting Headers

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640000000

# When exceeded
HTTP/1.1 429 Too Many Requests
Retry-After: 60
```

### Conditional Requests

```http
# ETag for caching
GET /api/users/123
Response:
ETag: "abc123"

# Conditional GET
GET /api/users/123
If-None-Match: "abc123"
Response: 304 Not Modified

# Conditional PUT (prevent conflicts)
PUT /api/users/123
If-Match: "abc123"
{...}
```

---

## 8️⃣ EXPERT LEVEL - Documentation (OpenAPI)

### OpenAPI Specification

```yaml
# openapi.yaml
openapi: 3.0.0
info:
  title: Task API
  version: 1.0.0
  description: API for managing tasks

servers:
  - url: https://api.example.com/v1

paths:
  /tasks:
    get:
      summary: List all tasks
      parameters:
        - name: status
          in: query
          schema:
            type: string
            enum: [todo, in_progress, done]
        - name: page
          in: query
          schema:
            type: integer
            default: 1
      responses:
        '200':
          description: List of tasks
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/Task'
    
    post:
      summary: Create a task
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateTask'
      responses:
        '201':
          description: Task created

components:
  schemas:
    Task:
      type: object
      properties:
        id:
          type: integer
        title:
          type: string
        status:
          type: string
        created_at:
          type: string
          format: date-time
    
    CreateTask:
      type: object
      required:
        - title
      properties:
        title:
          type: string
          minLength: 3
        description:
          type: string
```

---

## 📊 API Design Comparison

### REST vs GraphQL

| Aspect | REST | GraphQL |
|--------|------|---------|
| **Data Fetching** | Fixed endpoints | Flexible queries |
| **Over-fetching** | Common | Avoided |
| **Under-fetching** | Multiple requests | Single request |
| **Caching** | Easy (HTTP cache) | Complex |
| **Versioning** | URL-based | Schema evolution |
| **Learning Curve** | Lower | Higher |
| **Best For** | Simple CRUD | Complex data needs |

### REST vs gRPC

| Aspect | REST | gRPC |
|--------|------|------|
| **Protocol** | HTTP/1.1 or 2 | HTTP/2 |
| **Format** | JSON | Protocol Buffers |
| **Speed** | Slower | Faster |
| **Browser** | Full support | Limited |
| **Streaming** | Limited | Bidirectional |
| **Best For** | Public APIs | Microservices |

---

## 🎯 Best Practices Checklist

### URL Design
- [ ] Use nouns, not verbs
- [ ] Use plural names (`/users`, not `/user`)
- [ ] Use lowercase with hyphens (`/user-profiles`)
- [ ] Keep URLs short and simple
- [ ] Use query params for filtering/sorting

### Response Design
- [ ] Consistent response format
- [ ] Include proper status codes
- [ ] Use ISO 8601 for dates
- [ ] Return created/updated resources
- [ ] Paginate large collections

### Security
- [ ] Use HTTPS always
- [ ] Validate all input
- [ ] Rate limit endpoints
- [ ] Authenticate properly
- [ ] Don't expose internal errors

### Documentation
- [ ] Document all endpoints
- [ ] Include request/response examples
- [ ] List all possible errors
- [ ] Keep docs up to date
- [ ] Provide SDKs if possible

---

## 💡 Summary

| Level | Focus |
|-------|-------|
| **Junior** | HTTP methods, status codes, basic requests |
| **Mid** | URL design, query params, response format |
| **Mid-Senior** | Versioning, authentication, error handling |
| **Senior** | HATEOAS, bulk operations, rate limiting |
| **Expert** | OpenAPI, GraphQL, API gateway |

**Golden Rules:**
- ✅ Be consistent
- ✅ Be RESTful (use HTTP properly)
- ✅ Version your API
- ✅ Document everything
- ✅ Handle errors gracefully
- ✅ Secure your endpoints
- ✅ Think about pagination early
- ✅ Test your API

**URL Design Formula:**
```
[PROTOCOL]://[HOST]/api/[VERSION]/[RESOURCE]/[ID]/[SUB-RESOURCE]?[QUERY]

Example:
https://api.example.com/api/v1/users/123/tasks?status=done&sort=-created_at
```
