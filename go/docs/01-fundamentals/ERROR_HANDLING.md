# ⚠️ Error Handling di Go

## Kenapa Penting?

Go tidak punya exceptions seperti Python/Java. Error handling di Go:
- Explicit - harus di-handle di setiap level
- Return value - error adalah value yang di-return
- Composable - bisa di-wrap dan di-chain

---

## 📚 Daftar Isi

1. [Basic Error Handling](#1️⃣-basic-error-handling)
2. [Custom Errors](#2️⃣-custom-errors)
3. [Error Wrapping](#3️⃣-error-wrapping)
4. [Sentinel Errors](#4️⃣-sentinel-errors)
5. [Error Types](#5️⃣-error-types)
6. [HTTP Error Responses](#6️⃣-http-error-responses)
7. [Panic & Recover](#7️⃣-panic--recover)
8. [Error Handling Patterns](#8️⃣-error-handling-patterns)

---

## 1️⃣ Basic Error Handling

### JUNIOR: The `if err != nil` Pattern

```go
// Go's standard error handling
func GetUser(id int) (*User, error) {
    user, err := db.FindUserByID(id)
    if err != nil {
        return nil, err
    }
    return user, nil
}

// Calling the function
user, err := GetUser(123)
if err != nil {
    log.Printf("Failed to get user: %v", err)
    return
}
fmt.Println(user.Name)
```

### Multiple Error Checks

```go
func CreateTask(userID int, data TaskInput) (*Task, error) {
    // Validate user
    user, err := GetUser(userID)
    if err != nil {
        return nil, err
    }
    
    // Validate input
    if err := data.Validate(); err != nil {
        return nil, err
    }
    
    // Create task
    task, err := db.CreateTask(user.ID, data)
    if err != nil {
        return nil, err
    }
    
    // Send notification
    if err := notifyUser(user, task); err != nil {
        // Log but don't fail
        log.Printf("Failed to notify user: %v", err)
    }
    
    return task, nil
}
```

---

## 2️⃣ Custom Errors

### Simple Custom Error

```go
// errors package
import "errors"

var ErrUserNotFound = errors.New("user not found")
var ErrInvalidInput = errors.New("invalid input")

func GetUser(id int) (*User, error) {
    user, err := db.FindUserByID(id)
    if err != nil {
        if errors.Is(err, sql.ErrNoRows) {
            return nil, ErrUserNotFound
        }
        return nil, err
    }
    return user, nil
}
```

### MID: Custom Error Struct

```go
// internal/errors/errors.go
package errors

import "fmt"

// AppError - custom application error
type AppError struct {
    Code    string `json:"code"`
    Message string `json:"message"`
    Err     error  `json:"-"`
}

func (e *AppError) Error() string {
    if e.Err != nil {
        return fmt.Sprintf("%s: %v", e.Message, e.Err)
    }
    return e.Message
}

func (e *AppError) Unwrap() error {
    return e.Err
}

// Constructor functions
func NewNotFound(resource string) *AppError {
    return &AppError{
        Code:    "NOT_FOUND",
        Message: fmt.Sprintf("%s not found", resource),
    }
}

func NewBadRequest(message string) *AppError {
    return &AppError{
        Code:    "BAD_REQUEST",
        Message: message,
    }
}

func NewUnauthorized(message string) *AppError {
    return &AppError{
        Code:    "UNAUTHORIZED",
        Message: message,
    }
}

func NewInternal(err error) *AppError {
    return &AppError{
        Code:    "INTERNAL_ERROR",
        Message: "An internal error occurred",
        Err:     err,
    }
}
```

### Usage

```go
func GetTask(id int) (*Task, error) {
    task, err := repo.FindByID(id)
    if err != nil {
        if errors.Is(err, sql.ErrNoRows) {
            return nil, errors.NewNotFound("task")
        }
        return nil, errors.NewInternal(err)
    }
    return task, nil
}
```

---

## 3️⃣ Error Wrapping

### Go 1.13+ Error Wrapping

```go
import (
    "errors"
    "fmt"
)

func GetTaskByID(id int) (*Task, error) {
    task, err := db.Query("SELECT * FROM tasks WHERE id = ?", id)
    if err != nil {
        // Wrap error with context
        return nil, fmt.Errorf("failed to get task %d: %w", id, err)
    }
    return task, nil
}

func ProcessTask(id int) error {
    task, err := GetTaskByID(id)
    if err != nil {
        // Add more context
        return fmt.Errorf("process task failed: %w", err)
    }
    // ... process
    return nil
}

// Checking wrapped errors
err := ProcessTask(123)
if err != nil {
    // Check if it's a specific error
    if errors.Is(err, sql.ErrNoRows) {
        // Handle not found
    }
    
    // Get the original error
    var appErr *AppError
    if errors.As(err, &appErr) {
        fmt.Println(appErr.Code)
    }
}
```

### SENIOR: pkg/errors (Rich Stack Traces)

```go
import "github.com/pkg/errors"

func GetUser(id int) (*User, error) {
    user, err := db.FindByID(id)
    if err != nil {
        // Wrap with stack trace
        return nil, errors.Wrap(err, "failed to get user")
    }
    return user, nil
}

func ProcessUser(id int) error {
    user, err := GetUser(id)
    if err != nil {
        return errors.WithMessage(err, "process user failed")
    }
    return nil
}

// Print with stack trace
err := ProcessUser(123)
if err != nil {
    fmt.Printf("%+v\n", err)
    // Output:
    // failed to get user
    //     main.GetUser
    //         /app/main.go:15
    //     main.ProcessUser
    //         /app/main.go:23
}
```

---

## 4️⃣ Sentinel Errors

### Define Sentinel Errors

```go
// internal/domain/errors.go
package domain

import "errors"

// Sentinel errors - package level errors
var (
    ErrNotFound       = errors.New("resource not found")
    ErrAlreadyExists  = errors.New("resource already exists")
    ErrUnauthorized   = errors.New("unauthorized")
    ErrForbidden      = errors.New("forbidden")
    ErrInvalidInput   = errors.New("invalid input")
    ErrConflict       = errors.New("conflict")
)

// Domain-specific errors
var (
    ErrTaskNotFound     = errors.New("task not found")
    ErrTaskCompleted    = errors.New("task already completed")
    ErrInvalidStatus    = errors.New("invalid task status")
    ErrUserNotFound     = errors.New("user not found")
    ErrEmailExists      = errors.New("email already exists")
    ErrInvalidPassword  = errors.New("invalid password")
)
```

### Usage Pattern

```go
func (s *TaskService) CompleteTask(id int) error {
    task, err := s.repo.FindByID(id)
    if err != nil {
        if errors.Is(err, sql.ErrNoRows) {
            return domain.ErrTaskNotFound
        }
        return err
    }
    
    if task.Status == "DONE" {
        return domain.ErrTaskCompleted
    }
    
    task.Status = "DONE"
    return s.repo.Update(task)
}

// Handler
func (h *TaskHandler) Complete(w http.ResponseWriter, r *http.Request) {
    id := chi.URLParam(r, "id")
    
    err := h.service.CompleteTask(id)
    if err != nil {
        switch {
        case errors.Is(err, domain.ErrTaskNotFound):
            respondError(w, http.StatusNotFound, "Task not found")
        case errors.Is(err, domain.ErrTaskCompleted):
            respondError(w, http.StatusConflict, "Task already completed")
        default:
            respondError(w, http.StatusInternalServerError, "Internal error")
        }
        return
    }
    
    respondJSON(w, http.StatusOK, map[string]string{"status": "completed"})
}
```

---

## 5️⃣ Error Types

### SENIOR: Rich Error Types

```go
// internal/errors/types.go
package errors

import (
    "fmt"
    "net/http"
)

// ErrorType for categorization
type ErrorType string

const (
    ErrorTypeValidation   ErrorType = "VALIDATION_ERROR"
    ErrorTypeNotFound     ErrorType = "NOT_FOUND"
    ErrorTypeUnauthorized ErrorType = "UNAUTHORIZED"
    ErrorTypeForbidden    ErrorType = "FORBIDDEN"
    ErrorTypeConflict     ErrorType = "CONFLICT"
    ErrorTypeInternal     ErrorType = "INTERNAL_ERROR"
)

// Error with full context
type Error struct {
    Type       ErrorType         `json:"type"`
    Message    string            `json:"message"`
    Details    map[string]string `json:"details,omitempty"`
    StatusCode int               `json:"-"`
    Err        error             `json:"-"`
}

func (e *Error) Error() string {
    if e.Err != nil {
        return fmt.Sprintf("[%s] %s: %v", e.Type, e.Message, e.Err)
    }
    return fmt.Sprintf("[%s] %s", e.Type, e.Message)
}

func (e *Error) Unwrap() error {
    return e.Err
}

// Constructors
func ValidationError(message string, details map[string]string) *Error {
    return &Error{
        Type:       ErrorTypeValidation,
        Message:    message,
        Details:    details,
        StatusCode: http.StatusBadRequest,
    }
}

func NotFoundError(resource string) *Error {
    return &Error{
        Type:       ErrorTypeNotFound,
        Message:    fmt.Sprintf("%s not found", resource),
        StatusCode: http.StatusNotFound,
    }
}

func UnauthorizedError(message string) *Error {
    return &Error{
        Type:       ErrorTypeUnauthorized,
        Message:    message,
        StatusCode: http.StatusUnauthorized,
    }
}

func InternalError(err error) *Error {
    return &Error{
        Type:       ErrorTypeInternal,
        Message:    "An internal error occurred",
        StatusCode: http.StatusInternalServerError,
        Err:        err,
    }
}
```

### Validation Errors

```go
// internal/errors/validation.go
package errors

type ValidationError struct {
    Field   string `json:"field"`
    Message string `json:"message"`
}

type ValidationErrors struct {
    Errors []ValidationError `json:"errors"`
}

func (v *ValidationErrors) Error() string {
    return fmt.Sprintf("validation failed: %d errors", len(v.Errors))
}

func (v *ValidationErrors) Add(field, message string) {
    v.Errors = append(v.Errors, ValidationError{
        Field:   field,
        Message: message,
    })
}

func (v *ValidationErrors) HasErrors() bool {
    return len(v.Errors) > 0
}

// Usage
func ValidateTaskInput(input TaskInput) error {
    errs := &ValidationErrors{}
    
    if input.Title == "" {
        errs.Add("title", "Title is required")
    }
    if len(input.Title) > 255 {
        errs.Add("title", "Title must be less than 255 characters")
    }
    if input.Priority != "" && !isValidPriority(input.Priority) {
        errs.Add("priority", "Priority must be LOW, MEDIUM, or HIGH")
    }
    
    if errs.HasErrors() {
        return errs
    }
    return nil
}
```

---

## 6️⃣ HTTP Error Responses

### Error Response Handler

```go
// internal/api/response.go
package api

import (
    "encoding/json"
    "net/http"
    
    appErrors "myapp/internal/errors"
)

type ErrorResponse struct {
    Success bool              `json:"success"`
    Error   ErrorDetail       `json:"error"`
}

type ErrorDetail struct {
    Type    string            `json:"type"`
    Message string            `json:"message"`
    Details map[string]string `json:"details,omitempty"`
}

func RespondError(w http.ResponseWriter, err error) {
    var response ErrorResponse
    var statusCode int
    
    // Check error type
    switch e := err.(type) {
    case *appErrors.Error:
        statusCode = e.StatusCode
        response = ErrorResponse{
            Success: false,
            Error: ErrorDetail{
                Type:    string(e.Type),
                Message: e.Message,
                Details: e.Details,
            },
        }
    case *appErrors.ValidationErrors:
        statusCode = http.StatusBadRequest
        details := make(map[string]string)
        for _, ve := range e.Errors {
            details[ve.Field] = ve.Message
        }
        response = ErrorResponse{
            Success: false,
            Error: ErrorDetail{
                Type:    "VALIDATION_ERROR",
                Message: "Validation failed",
                Details: details,
            },
        }
    default:
        statusCode = http.StatusInternalServerError
        response = ErrorResponse{
            Success: false,
            Error: ErrorDetail{
                Type:    "INTERNAL_ERROR",
                Message: "An internal error occurred",
            },
        }
    }
    
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(statusCode)
    json.NewEncoder(w).Encode(response)
}
```

### Handler with Error Handling

```go
// internal/api/handlers/task.go
func (h *TaskHandler) Create(w http.ResponseWriter, r *http.Request) {
    var input CreateTaskInput
    if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
        api.RespondError(w, errors.ValidationError("Invalid JSON", nil))
        return
    }
    
    // Validate
    if err := ValidateTaskInput(input); err != nil {
        api.RespondError(w, err)
        return
    }
    
    // Get user from context
    userID := r.Context().Value("user_id").(int)
    
    // Create task
    task, err := h.service.CreateTask(userID, input)
    if err != nil {
        api.RespondError(w, err)
        return
    }
    
    api.RespondJSON(w, http.StatusCreated, task)
}
```

---

## 7️⃣ Panic & Recover

### When to Use Panic

```go
// ❌ DON'T panic for normal errors
func GetUser(id int) *User {
    user, err := db.Find(id)
    if err != nil {
        panic(err)  // DON'T DO THIS!
    }
    return user
}

// ✅ DO panic for programmer errors (unrecoverable)
func MustParseConfig(path string) Config {
    cfg, err := ParseConfig(path)
    if err != nil {
        panic(fmt.Sprintf("failed to parse config: %v", err))
    }
    return cfg
}

// ✅ DO panic for impossible conditions
func divide(a, b int) int {
    if b == 0 {
        panic("division by zero")  // Should never happen if validated
    }
    return a / b
}
```

### Recovery Middleware

```go
// internal/middleware/recovery.go
package middleware

import (
    "log"
    "net/http"
    "runtime/debug"
)

func Recovery(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        defer func() {
            if err := recover(); err != nil {
                // Log stack trace
                log.Printf("panic recovered: %v\n%s", err, debug.Stack())
                
                // Return 500 error
                w.Header().Set("Content-Type", "application/json")
                w.WriteHeader(http.StatusInternalServerError)
                w.Write([]byte(`{"success":false,"error":{"type":"INTERNAL_ERROR","message":"An internal error occurred"}}`))
            }
        }()
        
        next.ServeHTTP(w, r)
    })
}

// Usage with Chi
r := chi.NewRouter()
r.Use(middleware.Recovery)
```

---

## 8️⃣ Error Handling Patterns

### EXPERT: Functional Error Handling

```go
// Result type pattern
type Result[T any] struct {
    Value T
    Err   error
}

func NewResult[T any](value T, err error) Result[T] {
    return Result[T]{Value: value, Err: err}
}

func (r Result[T]) IsOk() bool {
    return r.Err == nil
}

func (r Result[T]) Unwrap() T {
    if r.Err != nil {
        panic(r.Err)
    }
    return r.Value
}

// Usage
result := NewResult(GetUser(123))
if result.IsOk() {
    user := result.Value
    // use user
}
```

### Error Aggregation

```go
// Collect multiple errors
type MultiError struct {
    Errors []error
}

func (m *MultiError) Add(err error) {
    if err != nil {
        m.Errors = append(m.Errors, err)
    }
}

func (m *MultiError) HasErrors() bool {
    return len(m.Errors) > 0
}

func (m *MultiError) Error() string {
    if len(m.Errors) == 1 {
        return m.Errors[0].Error()
    }
    return fmt.Sprintf("multiple errors: %d total", len(m.Errors))
}

func (m *MultiError) ErrorOrNil() error {
    if m.HasErrors() {
        return m
    }
    return nil
}

// Usage
func ValidateAll(items []Item) error {
    errs := &MultiError{}
    
    for i, item := range items {
        if err := item.Validate(); err != nil {
            errs.Add(fmt.Errorf("item %d: %w", i, err))
        }
    }
    
    return errs.ErrorOrNil()
}
```

### Retry with Errors

```go
func WithRetry(attempts int, delay time.Duration, fn func() error) error {
    var lastErr error
    
    for i := 0; i < attempts; i++ {
        err := fn()
        if err == nil {
            return nil
        }
        
        lastErr = err
        
        // Don't retry on certain errors
        if errors.Is(err, ErrNotFound) || errors.Is(err, ErrUnauthorized) {
            return err
        }
        
        log.Printf("attempt %d failed: %v, retrying...", i+1, err)
        time.Sleep(delay)
        delay *= 2  // Exponential backoff
    }
    
    return fmt.Errorf("all %d attempts failed: %w", attempts, lastErr)
}

// Usage
err := WithRetry(3, time.Second, func() error {
    return callExternalAPI()
})
```

---

## 📋 Error Handling Checklist

### Junior ✅
- [ ] Always check `if err != nil`
- [ ] Return errors up the call stack
- [ ] Use `errors.New()` for simple errors

### Mid ✅
- [ ] Create custom error types
- [ ] Use `fmt.Errorf("...: %w", err)` for wrapping
- [ ] Use `errors.Is()` and `errors.As()`
- [ ] Define sentinel errors

### Senior ✅
- [ ] Rich error types with context
- [ ] Validation error aggregation
- [ ] HTTP error response handler
- [ ] Recovery middleware

### Expert ✅
- [ ] Stack traces dengan pkg/errors
- [ ] Retry patterns
- [ ] Error aggregation
- [ ] Structured logging dengan errors
