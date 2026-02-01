# 📦 Response Schema di Go

## Kenapa Penting?

Response yang konsisten:
- ✅ Frontend mudah handle response
- ✅ Error handling yang predictable
- ✅ API documentation yang jelas
- ✅ Better developer experience

---

## 📚 Daftar Isi

1. [Standard Response Format](#1️⃣-standard-response-format)
2. [Response Helpers](#2️⃣-response-helpers)
3. [Error Responses](#3️⃣-error-responses)
4. [Pagination Response](#4️⃣-pagination-response)
5. [Generic Response](#5️⃣-generic-response)
6. [Response Middleware](#6️⃣-response-middleware)

---

## 1️⃣ Standard Response Format

### Basic Response Structure

```go
// internal/api/response/response.go
package response

// Success response
type Response struct {
    Success bool        `json:"success"`
    Message string      `json:"message,omitempty"`
    Data    interface{} `json:"data,omitempty"`
}

// Error response
type ErrorResponse struct {
    Success bool        `json:"success"`
    Error   ErrorDetail `json:"error"`
}

type ErrorDetail struct {
    Code    string            `json:"code"`
    Message string            `json:"message"`
    Details map[string]string `json:"details,omitempty"`
}
```

### Example Responses

```json
// Success response
{
    "success": true,
    "message": "Task created successfully",
    "data": {
        "id": 1,
        "title": "My Task",
        "status": "TODO"
    }
}

// Error response
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Validation failed",
        "details": {
            "title": "Title is required",
            "priority": "Invalid priority value"
        }
    }
}

// List response with pagination
{
    "success": true,
    "data": [...],
    "pagination": {
        "page": 1,
        "page_size": 20,
        "total_items": 100,
        "total_pages": 5
    }
}
```

---

## 2️⃣ Response Helpers

### Helper Functions

```go
// internal/api/response/helpers.go
package response

import (
    "encoding/json"
    "net/http"
)

// JSON writes a JSON response
func JSON(w http.ResponseWriter, status int, data interface{}) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(status)
    json.NewEncoder(w).Encode(data)
}

// Success sends a success response
func Success(w http.ResponseWriter, message string, data interface{}) {
    JSON(w, http.StatusOK, Response{
        Success: true,
        Message: message,
        Data:    data,
    })
}

// Created sends a 201 response
func Created(w http.ResponseWriter, message string, data interface{}) {
    JSON(w, http.StatusCreated, Response{
        Success: true,
        Message: message,
        Data:    data,
    })
}

// NoContent sends a 204 response
func NoContent(w http.ResponseWriter) {
    w.WriteHeader(http.StatusNoContent)
}

// Error sends an error response
func Error(w http.ResponseWriter, status int, code, message string) {
    JSON(w, status, ErrorResponse{
        Success: false,
        Error: ErrorDetail{
            Code:    code,
            Message: message,
        },
    })
}

// ErrorWithDetails sends an error with field details
func ErrorWithDetails(w http.ResponseWriter, status int, code, message string, details map[string]string) {
    JSON(w, status, ErrorResponse{
        Success: false,
        Error: ErrorDetail{
            Code:    code,
            Message: message,
            Details: details,
        },
    })
}

// Common error responses
func BadRequest(w http.ResponseWriter, message string) {
    Error(w, http.StatusBadRequest, "BAD_REQUEST", message)
}

func Unauthorized(w http.ResponseWriter, message string) {
    Error(w, http.StatusUnauthorized, "UNAUTHORIZED", message)
}

func Forbidden(w http.ResponseWriter, message string) {
    Error(w, http.StatusForbidden, "FORBIDDEN", message)
}

func NotFound(w http.ResponseWriter, message string) {
    Error(w, http.StatusNotFound, "NOT_FOUND", message)
}

func Conflict(w http.ResponseWriter, message string) {
    Error(w, http.StatusConflict, "CONFLICT", message)
}

func InternalError(w http.ResponseWriter) {
    Error(w, http.StatusInternalServerError, "INTERNAL_ERROR", "An internal error occurred")
}
```

### Usage in Handlers

```go
func CreateTaskHandler(w http.ResponseWriter, r *http.Request) {
    var input CreateTaskInput
    if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
        response.BadRequest(w, "Invalid JSON body")
        return
    }
    
    // Validate
    if errors := input.Validate(); len(errors) > 0 {
        response.ErrorWithDetails(w, http.StatusBadRequest, "VALIDATION_ERROR", "Validation failed", errors)
        return
    }
    
    // Create
    task, err := taskService.Create(r.Context(), input)
    if err != nil {
        log.Printf("Failed to create task: %v", err)
        response.InternalError(w)
        return
    }
    
    response.Created(w, "Task created successfully", task)
}

func GetTaskHandler(w http.ResponseWriter, r *http.Request) {
    id := chi.URLParam(r, "id")
    
    task, err := taskService.GetByID(r.Context(), id)
    if err != nil {
        if errors.Is(err, domain.ErrNotFound) {
            response.NotFound(w, "Task not found")
            return
        }
        response.InternalError(w)
        return
    }
    
    response.Success(w, "Task retrieved successfully", task)
}
```

---

## 3️⃣ Error Responses

### Error Types Mapping

```go
// internal/api/response/error_handler.go
package response

import (
    "errors"
    "net/http"
    
    appErrors "myapp/internal/errors"
)

// HandleError maps domain errors to HTTP responses
func HandleError(w http.ResponseWriter, err error) {
    // Check for custom error types
    var appErr *appErrors.Error
    if errors.As(err, &appErr) {
        JSON(w, appErr.StatusCode, ErrorResponse{
            Success: false,
            Error: ErrorDetail{
                Code:    string(appErr.Type),
                Message: appErr.Message,
                Details: appErr.Details,
            },
        })
        return
    }
    
    // Check for validation errors
    var valErr *appErrors.ValidationErrors
    if errors.As(err, &valErr) {
        details := make(map[string]string)
        for _, e := range valErr.Errors {
            details[e.Field] = e.Message
        }
        ErrorWithDetails(w, http.StatusBadRequest, "VALIDATION_ERROR", "Validation failed", details)
        return
    }
    
    // Check for sentinel errors
    switch {
    case errors.Is(err, appErrors.ErrNotFound):
        NotFound(w, "Resource not found")
    case errors.Is(err, appErrors.ErrUnauthorized):
        Unauthorized(w, "Unauthorized")
    case errors.Is(err, appErrors.ErrForbidden):
        Forbidden(w, "Access denied")
    case errors.Is(err, appErrors.ErrConflict):
        Conflict(w, "Resource already exists")
    default:
        InternalError(w)
    }
}
```

### Usage

```go
func UpdateTaskHandler(w http.ResponseWriter, r *http.Request) {
    id := chi.URLParam(r, "id")
    
    var input UpdateTaskInput
    if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
        response.BadRequest(w, "Invalid JSON body")
        return
    }
    
    task, err := taskService.Update(r.Context(), id, input)
    if err != nil {
        response.HandleError(w, err)
        return
    }
    
    response.Success(w, "Task updated successfully", task)
}
```

---

## 4️⃣ Pagination Response

### Pagination Types

```go
// internal/api/response/pagination.go
package response

type Pagination struct {
    Page       int `json:"page"`
    PageSize   int `json:"page_size"`
    TotalItems int `json:"total_items"`
    TotalPages int `json:"total_pages"`
}

type PaginatedResponse struct {
    Success    bool        `json:"success"`
    Data       interface{} `json:"data"`
    Pagination Pagination  `json:"pagination"`
}

// Helper function
func Paginated(w http.ResponseWriter, data interface{}, page, pageSize, totalItems int) {
    totalPages := (totalItems + pageSize - 1) / pageSize
    
    JSON(w, http.StatusOK, PaginatedResponse{
        Success: true,
        Data:    data,
        Pagination: Pagination{
            Page:       page,
            PageSize:   pageSize,
            TotalItems: totalItems,
            TotalPages: totalPages,
        },
    })
}
```

### Cursor Pagination

```go
// internal/api/response/cursor.go
package response

type CursorPagination struct {
    NextCursor string `json:"next_cursor,omitempty"`
    PrevCursor string `json:"prev_cursor,omitempty"`
    HasMore    bool   `json:"has_more"`
}

type CursorPaginatedResponse struct {
    Success    bool             `json:"success"`
    Data       interface{}      `json:"data"`
    Pagination CursorPagination `json:"pagination"`
}

func CursorPaginated(w http.ResponseWriter, data interface{}, nextCursor, prevCursor string, hasMore bool) {
    JSON(w, http.StatusOK, CursorPaginatedResponse{
        Success: true,
        Data:    data,
        Pagination: CursorPagination{
            NextCursor: nextCursor,
            PrevCursor: prevCursor,
            HasMore:    hasMore,
        },
    })
}
```

### Usage

```go
func ListTasksHandler(w http.ResponseWriter, r *http.Request) {
    // Parse query params
    page, _ := strconv.Atoi(r.URL.Query().Get("page"))
    if page < 1 {
        page = 1
    }
    
    pageSize, _ := strconv.Atoi(r.URL.Query().Get("page_size"))
    if pageSize < 1 || pageSize > 100 {
        pageSize = 20
    }
    
    // Get data
    tasks, total, err := taskService.List(r.Context(), page, pageSize)
    if err != nil {
        response.HandleError(w, err)
        return
    }
    
    response.Paginated(w, tasks, page, pageSize, total)
}
```

---

## 5️⃣ Generic Response

### Go 1.18+ Generics

```go
// internal/api/response/generic.go
package response

// Generic response type
type APIResponse[T any] struct {
    Success bool   `json:"success"`
    Message string `json:"message,omitempty"`
    Data    T      `json:"data,omitempty"`
}

type APIListResponse[T any] struct {
    Success    bool       `json:"success"`
    Data       []T        `json:"data"`
    Pagination Pagination `json:"pagination"`
}

// Helper with generics
func SuccessData[T any](w http.ResponseWriter, data T) {
    JSON(w, http.StatusOK, APIResponse[T]{
        Success: true,
        Data:    data,
    })
}

func SuccessList[T any](w http.ResponseWriter, data []T, pagination Pagination) {
    JSON(w, http.StatusOK, APIListResponse[T]{
        Success:    true,
        Data:       data,
        Pagination: pagination,
    })
}
```

### Typed Responses

```go
// internal/api/response/types.go
package response

// Specific response types for documentation/OpenAPI
type TaskResponse struct {
    Success bool   `json:"success"`
    Message string `json:"message,omitempty"`
    Data    Task   `json:"data"`
}

type TaskListResponse struct {
    Success    bool       `json:"success"`
    Data       []Task     `json:"data"`
    Pagination Pagination `json:"pagination"`
}

type UserResponse struct {
    Success bool   `json:"success"`
    Message string `json:"message,omitempty"`
    Data    User   `json:"data"`
}
```

---

## 6️⃣ Response Middleware

### Response Writer Wrapper

```go
// internal/middleware/response.go
package middleware

import (
    "bytes"
    "encoding/json"
    "net/http"
)

type responseWrapper struct {
    http.ResponseWriter
    body       *bytes.Buffer
    statusCode int
}

func (rw *responseWrapper) Write(b []byte) (int, error) {
    rw.body.Write(b)
    return rw.ResponseWriter.Write(b)
}

func (rw *responseWrapper) WriteHeader(statusCode int) {
    rw.statusCode = statusCode
    rw.ResponseWriter.WriteHeader(statusCode)
}

// ResponseLogger logs all responses
func ResponseLogger(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        wrapper := &responseWrapper{
            ResponseWriter: w,
            body:           &bytes.Buffer{},
            statusCode:     http.StatusOK,
        }
        
        next.ServeHTTP(wrapper, r)
        
        // Log response
        log.Printf(
            "Response: %d %s %s",
            wrapper.statusCode,
            r.Method,
            r.URL.Path,
        )
    })
}
```

### Standard Response Wrapper

```go
// Middleware to ensure consistent response format
func EnsureJSONResponse(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // Set content type
        w.Header().Set("Content-Type", "application/json")
        
        next.ServeHTTP(w, r)
    })
}
```

---

## 📋 Response Examples

### Success Responses

```go
// Single item
response.Success(w, "Task retrieved", task)
// {"success": true, "message": "Task retrieved", "data": {...}}

// Created
response.Created(w, "Task created", task)
// HTTP 201
// {"success": true, "message": "Task created", "data": {...}}

// List with pagination
response.Paginated(w, tasks, 1, 20, 100)
// {"success": true, "data": [...], "pagination": {...}}

// No content
response.NoContent(w)
// HTTP 204
```

### Error Responses

```go
// Bad request
response.BadRequest(w, "Invalid input")
// HTTP 400
// {"success": false, "error": {"code": "BAD_REQUEST", "message": "Invalid input"}}

// Validation error
response.ErrorWithDetails(w, 400, "VALIDATION_ERROR", "Validation failed", map[string]string{
    "title": "Title is required",
})
// HTTP 400
// {"success": false, "error": {"code": "VALIDATION_ERROR", "message": "Validation failed", "details": {...}}}

// Not found
response.NotFound(w, "Task not found")
// HTTP 404
// {"success": false, "error": {"code": "NOT_FOUND", "message": "Task not found"}}

// Unauthorized
response.Unauthorized(w, "Invalid token")
// HTTP 401

// Internal error
response.InternalError(w)
// HTTP 500
// {"success": false, "error": {"code": "INTERNAL_ERROR", "message": "An internal error occurred"}}
```

---

## 📋 Response Checklist

### Junior ✅
- [ ] Consistent JSON structure
- [ ] Basic success/error responses
- [ ] Proper HTTP status codes

### Mid ✅
- [ ] Error helper functions
- [ ] Validation error details
- [ ] Pagination response

### Senior ✅
- [ ] Generic response types
- [ ] Error type mapping
- [ ] Cursor pagination

### Expert ✅
- [ ] Response middleware
- [ ] OpenAPI/Swagger integration
- [ ] Response compression
