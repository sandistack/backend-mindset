# API Examples and Testing Guide

## Authentication Examples

### 1. Register New User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

**Response:**
```json
{
  "user": {
    "id": "uuid-here",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "email_verified": false,
    "date_joined": "2024-01-01T00:00:00Z"
  },
  "tokens": {
    "refresh": "refresh_token_here",
    "access": "access_token_here"
  },
  "message": "Registration successful. Please verify your email."
}
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123!"
  }'
```

### 3. Get User Profile

```bash
curl -X GET http://localhost:8000/api/v1/auth/users/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. Update Profile

```bash
curl -X PATCH http://localhost:8000/api/v1/auth/users/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jane",
    "bio": "Software engineer passionate about Django"
  }'
```

### 5. Change Password

```bash
curl -X POST http://localhost:8000/api/v1/auth/users/change-password/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "SecurePass123!",
    "new_password": "NewSecurePass123!",
    "new_password_confirm": "NewSecurePass123!"
  }'
```

### 6. Request Password Reset

```bash
curl -X POST http://localhost:8000/api/v1/auth/password-reset/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com"
  }'
```

### 7. Confirm Password Reset

```bash
curl -X POST http://localhost:8000/api/v1/auth/password-reset/confirm/ \
  -H "Content-Type: application/json" \
  -d '{
    "token": "uuid-token-from-email",
    "new_password": "NewSecurePass123!",
    "new_password_confirm": "NewSecurePass123!"
  }'
```

### 8. Get Login History

```bash
curl -X GET http://localhost:8000/api/v1/auth/users/login-history/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 9. Logout

```bash
curl -X POST http://localhost:8000/api/v1/auth/logout/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "YOUR_REFRESH_TOKEN"
  }'
```

### 10. Refresh Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "YOUR_REFRESH_TOKEN"
  }'
```

## Health Check

```bash
curl -X GET http://localhost:8000/health/
```

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "database": "healthy",
    "cache": "healthy"
  }
}
```

## Python Testing

### Using Python Requests

```python
import requests

# Base URL
BASE_URL = "http://localhost:8000/api/v1"

# Register
response = requests.post(f"{BASE_URL}/auth/register/", json={
    "email": "test@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "first_name": "Test",
    "last_name": "User"
})
data = response.json()
access_token = data['tokens']['access']

# Get Profile
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{BASE_URL}/auth/users/me/", headers=headers)
print(response.json())
```

## Common Errors

### 400 Bad Request
```json
{
  "error": {
    "code": "validation_error",
    "message": "Validation failed. Please check your input.",
    "details": {
      "email": ["This field is required."]
    }
  }
}
```

### 401 Unauthorized
```json
{
  "error": {
    "code": "authentication_failed",
    "message": "Authentication credentials were not provided."
  }
}
```

### 403 Forbidden
```json
{
  "error": {
    "code": "permission_denied",
    "message": "You do not have permission to perform this action."
  }
}
```

### 404 Not Found
```json
{
  "error": {
    "code": "not_found",
    "message": "Resource not found."
  }
}
```

## Rate Limiting

The API implements rate limiting:
- Anonymous users: 100 requests/hour
- Authenticated users: 1000 requests/hour

When rate limit is exceeded:
```json
{
  "error": {
    "code": "throttled",
    "message": "Request was throttled. Expected available in 3600 seconds."
  }
}
```

## Pagination

List endpoints support pagination:

```bash
curl -X GET "http://localhost:8000/api/v1/auth/users/?page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/v1/auth/users/?page=2",
  "previous": null,
  "results": [...]
}
```

## Filtering and Searching

List endpoints support filtering:

```bash
# Search users by email
curl -X GET "http://localhost:8000/api/v1/auth/users/?search=john" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Order results
curl -X GET "http://localhost:8000/api/v1/auth/users/?ordering=-date_joined" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```
