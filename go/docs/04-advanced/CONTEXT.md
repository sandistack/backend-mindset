# 🔄 Context di Go

## Kenapa Penting?

Context untuk:
- ✅ Request-scoped values
- ✅ Cancellation signals
- ✅ Timeouts & deadlines
- ✅ Graceful shutdown

---

## 📚 Daftar Isi

1. [Context Basics](#1️⃣-context-basics)
2. [Cancellation](#2️⃣-cancellation)
3. [Timeouts & Deadlines](#3️⃣-timeouts--deadlines)
4. [Context Values](#4️⃣-context-values)
5. [Best Practices](#5️⃣-best-practices)
6. [Real-World Patterns](#6️⃣-real-world-patterns)

---

## 1️⃣ Context Basics

### Context Interface

```go
type Context interface {
    // Deadline returns when the context will be canceled (if set)
    Deadline() (deadline time.Time, ok bool)
    
    // Done returns a channel that closes when context is canceled
    Done() <-chan struct{}
    
    // Err returns why the context was canceled
    Err() error
    
    // Value returns the value associated with key
    Value(key interface{}) interface{}
}
```

### Creating Contexts

```go
import "context"

// Background - top-level context, never canceled
ctx := context.Background()

// TODO - placeholder when unsure what context to use
ctx := context.TODO()

// WithCancel - can be manually canceled
ctx, cancel := context.WithCancel(context.Background())
defer cancel() // Always defer cancel to avoid leaks

// WithTimeout - canceled after duration
ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()

// WithDeadline - canceled at specific time
deadline := time.Now().Add(10 * time.Second)
ctx, cancel := context.WithDeadline(context.Background(), deadline)
defer cancel()

// WithValue - attach values to context
ctx := context.WithValue(context.Background(), "userID", 123)
```

---

## 2️⃣ Cancellation

### Basic Cancellation

```go
// internal/service/user_service.go
package service

import (
    "context"
    "fmt"
    "time"
)

func ProcessUser(ctx context.Context, userID int) error {
    // Check if context is already canceled
    select {
    case <-ctx.Done():
        return ctx.Err()
    default:
    }
    
    // Simulate long-running operation
    for i := 0; i < 10; i++ {
        select {
        case <-ctx.Done():
            // Context canceled, stop processing
            return fmt.Errorf("processing canceled: %w", ctx.Err())
        default:
            // Continue processing
            fmt.Printf("Processing step %d for user %d\n", i+1, userID)
            time.Sleep(time.Second)
        }
    }
    
    return nil
}

// Usage
func main() {
    ctx, cancel := context.WithCancel(context.Background())
    
    go func() {
        time.Sleep(3 * time.Second)
        cancel() // Cancel after 3 seconds
    }()
    
    err := ProcessUser(ctx, 123)
    if err != nil {
        fmt.Println("Error:", err)
    }
}
```

### Propagating Cancellation

```go
// Parent context cancels all children
func ParentChildExample() {
    parent, parentCancel := context.WithCancel(context.Background())
    defer parentCancel()
    
    // Child 1
    child1, child1Cancel := context.WithCancel(parent)
    defer child1Cancel()
    
    go worker(child1, "Worker 1")
    
    // Child 2
    child2, child2Cancel := context.WithCancel(parent)
    defer child2Cancel()
    
    go worker(child2, "Worker 2")
    
    time.Sleep(2 * time.Second)
    parentCancel() // Cancels both children
    
    time.Sleep(time.Second)
}

func worker(ctx context.Context, name string) {
    for {
        select {
        case <-ctx.Done():
            fmt.Printf("%s stopped\n", name)
            return
        default:
            fmt.Printf("%s working...\n", name)
            time.Sleep(500 * time.Millisecond)
        }
    }
}
```

### Goroutine Coordination

```go
// internal/worker/coordinator.go
package worker

import (
    "context"
    "sync"
)

func RunWorkers(ctx context.Context, numWorkers int, jobs <-chan int) {
    var wg sync.WaitGroup
    
    for i := 0; i < numWorkers; i++ {
        wg.Add(1)
        go func(workerID int) {
            defer wg.Done()
            
            for {
                select {
                case <-ctx.Done():
                    fmt.Printf("Worker %d stopping\n", workerID)
                    return
                case job, ok := <-jobs:
                    if !ok {
                        return
                    }
                    processJob(ctx, workerID, job)
                }
            }
        }(i)
    }
    
    wg.Wait()
}

func processJob(ctx context.Context, workerID, jobID int) {
    select {
    case <-ctx.Done():
        return
    default:
        fmt.Printf("Worker %d processing job %d\n", workerID, jobID)
        time.Sleep(time.Second)
    }
}
```

---

## 3️⃣ Timeouts & Deadlines

### HTTP Request with Timeout

```go
// internal/client/http_client.go
package client

import (
    "context"
    "fmt"
    "io"
    "net/http"
    "time"
)

type HTTPClient struct {
    client *http.Client
}

func NewHTTPClient(timeout time.Duration) *HTTPClient {
    return &HTTPClient{
        client: &http.Client{
            Timeout: timeout,
        },
    }
}

func (c *HTTPClient) Get(ctx context.Context, url string) ([]byte, error) {
    req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
    if err != nil {
        return nil, err
    }
    
    resp, err := c.client.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    
    if resp.StatusCode != http.StatusOK {
        return nil, fmt.Errorf("bad status: %s", resp.Status)
    }
    
    return io.ReadAll(resp.Body)
}

// Usage
func main() {
    client := NewHTTPClient(10 * time.Second)
    
    // Request with timeout
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()
    
    data, err := client.Get(ctx, "https://api.example.com/data")
    if err != nil {
        log.Fatal(err)
    }
    
    fmt.Println(string(data))
}
```

### Database Query with Timeout

```go
// internal/repository/user_repo.go
package repository

import (
    "context"
    "database/sql"
    "time"
)

type UserRepository struct {
    db *sql.DB
}

func (r *UserRepository) GetByID(ctx context.Context, id int) (*User, error) {
    // Add timeout to context
    ctx, cancel := context.WithTimeout(ctx, 3*time.Second)
    defer cancel()
    
    query := "SELECT id, email, name FROM users WHERE id = $1"
    
    var user User
    err := r.db.QueryRowContext(ctx, query, id).Scan(&user.ID, &user.Email, &user.Name)
    if err != nil {
        return nil, err
    }
    
    return &user, nil
}

func (r *UserRepository) List(ctx context.Context) ([]*User, error) {
    ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
    defer cancel()
    
    query := "SELECT id, email, name FROM users"
    
    rows, err := r.db.QueryContext(ctx, query)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    
    var users []*User
    for rows.Next() {
        var user User
        if err := rows.Scan(&user.ID, &user.Email, &user.Name); err != nil {
            return nil, err
        }
        users = append(users, &user)
    }
    
    return users, rows.Err()
}
```

### Deadline-based Operations

```go
// internal/service/batch_processor.go
package service

import (
    "context"
    "fmt"
    "time"
)

func ProcessBatch(ctx context.Context, items []int) error {
    // Set hard deadline
    deadline := time.Now().Add(10 * time.Second)
    ctx, cancel := context.WithDeadline(ctx, deadline)
    defer cancel()
    
    for i, item := range items {
        // Check deadline before each item
        if deadline, ok := ctx.Deadline(); ok {
            if time.Until(deadline) < time.Second {
                return fmt.Errorf("not enough time to process remaining items")
            }
        }
        
        select {
        case <-ctx.Done():
            return fmt.Errorf("batch processing canceled: %w", ctx.Err())
        default:
            if err := processItem(ctx, item); err != nil {
                return fmt.Errorf("failed to process item %d: %w", i, err)
            }
        }
    }
    
    return nil
}
```

---

## 4️⃣ Context Values

### Storing Values

```go
// internal/middleware/request_id.go
package middleware

import (
    "context"
    "net/http"
    
    "github.com/google/uuid"
)

type contextKey string

const (
    requestIDKey contextKey = "requestID"
    userIDKey    contextKey = "userID"
)

func RequestID(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        requestID := uuid.New().String()
        
        // Add request ID to context
        ctx := context.WithValue(r.Context(), requestIDKey, requestID)
        
        // Add to response header
        w.Header().Set("X-Request-ID", requestID)
        
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

// Retrieve request ID
func GetRequestID(ctx context.Context) string {
    if id, ok := ctx.Value(requestIDKey).(string); ok {
        return id
    }
    return ""
}

// Store user ID
func WithUserID(ctx context.Context, userID int) context.Context {
    return context.WithValue(ctx, userIDKey, userID)
}

// Retrieve user ID
func GetUserID(ctx context.Context) (int, bool) {
    if id, ok := ctx.Value(userIDKey).(int); ok {
        return id, true
    }
    return 0, false
}
```

### Type-Safe Context Keys

```go
// internal/contextkeys/keys.go
package contextkeys

import "context"

type UserKey struct{}
type TenantKey struct{}
type TraceIDKey struct{}

// Store user
func WithUser(ctx context.Context, user *User) context.Context {
    return context.WithValue(ctx, UserKey{}, user)
}

// Retrieve user
func GetUser(ctx context.Context) (*User, bool) {
    user, ok := ctx.Value(UserKey{}).(*User)
    return user, ok
}

// Store tenant
func WithTenant(ctx context.Context, tenantID string) context.Context {
    return context.WithValue(ctx, TenantKey{}, tenantID)
}

// Retrieve tenant
func GetTenant(ctx context.Context) (string, bool) {
    tenantID, ok := ctx.Value(TenantKey{}).(string)
    return tenantID, ok
}
```

---

## 5️⃣ Best Practices

### DO ✅

```go
// 1. Pass context as first parameter
func ProcessUser(ctx context.Context, userID int) error {
    // ...
}

// 2. Always call cancel()
func GoodExample() {
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel() // ✅ Prevents context leak
    
    doSomething(ctx)
}

// 3. Check context cancellation in loops
func ProcessItems(ctx context.Context, items []int) error {
    for _, item := range items {
        select {
        case <-ctx.Done():
            return ctx.Err()
        default:
            processItem(item)
        }
    }
    return nil
}

// 4. Propagate context down the call stack
func HandlerA(ctx context.Context) {
    HandlerB(ctx) // ✅ Pass context
}

func HandlerB(ctx context.Context) {
    // Use context
}
```

### DON'T ❌

```go
// 1. Don't store context in struct
type Service struct {
    ctx context.Context // ❌ Don't do this
}

// 2. Don't use context.Background() in library code
func LibraryFunction() {
    ctx := context.Background() // ❌ Should accept context as parameter
}

// 3. Don't use context for optional parameters
func CreateUser(ctx context.Context) error {
    // ❌ Don't use context.Value() for required fields
    email := ctx.Value("email").(string)
    
    // ✅ Use explicit parameters instead
}

func CreateUser(ctx context.Context, email string) error {
    // ...
}

// 4. Don't forget to call cancel()
func BadExample() {
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    // ❌ Missing defer cancel()
    
    doSomething(ctx)
}
```

---

## 6️⃣ Real-World Patterns

### HTTP Handler with Context

```go
// internal/handler/user_handler.go
package handler

import (
    "context"
    "encoding/json"
    "net/http"
    "time"
)

type UserHandler struct {
    service UserService
}

func (h *UserHandler) GetUser(w http.ResponseWriter, r *http.Request) {
    // Get user ID from URL
    userID := getUserIDFromURL(r)
    
    // Add timeout to request context
    ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
    defer cancel()
    
    // Get user from service
    user, err := h.service.GetByID(ctx, userID)
    if err != nil {
        if err == context.DeadlineExceeded {
            http.Error(w, "Request timeout", http.StatusRequestTimeout)
            return
        }
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    
    // Return response
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(user)
}
```

### Service Layer with Context

```go
// internal/service/user_service.go
package service

import (
    "context"
    "fmt"
)

type UserService struct {
    repo  UserRepository
    cache Cache
}

func (s *UserService) GetByID(ctx context.Context, id int) (*User, error) {
    // Check cache first
    cacheKey := fmt.Sprintf("user:%d", id)
    
    var user User
    err := s.cache.Get(ctx, cacheKey, &user)
    if err == nil {
        return &user, nil
    }
    
    // Cache miss - query database
    user, err = s.repo.GetByID(ctx, id)
    if err != nil {
        return nil, err
    }
    
    // Store in cache (with separate context to avoid timeout)
    cacheCtx, cancel := context.WithTimeout(context.Background(), time.Second)
    defer cancel()
    
    s.cache.Set(cacheCtx, cacheKey, user, 5*time.Minute)
    
    return user, nil
}
```

### Background Job with Context

```go
// internal/worker/email_worker.go
package worker

import (
    "context"
    "log"
    "time"
)

type EmailWorker struct {
    emailService EmailService
}

func (w *EmailWorker) Start(ctx context.Context) {
    ticker := time.NewTicker(time.Minute)
    defer ticker.Stop()
    
    for {
        select {
        case <-ctx.Done():
            log.Println("Email worker stopping...")
            return
            
        case <-ticker.C:
            // Create timeout context for each batch
            batchCtx, cancel := context.WithTimeout(ctx, 30*time.Second)
            
            if err := w.processBatch(batchCtx); err != nil {
                log.Printf("Failed to process batch: %v", err)
            }
            
            cancel()
        }
    }
}

func (w *EmailWorker) processBatch(ctx context.Context) error {
    emails, err := w.emailService.GetPendingEmails(ctx, 100)
    if err != nil {
        return err
    }
    
    for _, email := range emails {
        select {
        case <-ctx.Done():
            return ctx.Err()
        default:
            if err := w.emailService.Send(ctx, email); err != nil {
                log.Printf("Failed to send email: %v", err)
            }
        }
    }
    
    return nil
}
```

### Graceful Shutdown

```go
// cmd/api/main.go
package main

import (
    "context"
    "log"
    "net/http"
    "os"
    "os/signal"
    "syscall"
    "time"
)

func main() {
    // Create server
    server := &http.Server{
        Addr:    ":8080",
        Handler: setupRoutes(),
    }
    
    // Start server in goroutine
    go func() {
        log.Println("Server starting on :8080")
        if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
            log.Fatalf("Server error: %v", err)
        }
    }()
    
    // Wait for interrupt signal
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit
    
    log.Println("Shutting down server...")
    
    // Graceful shutdown with timeout
    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()
    
    if err := server.Shutdown(ctx); err != nil {
        log.Fatalf("Server forced to shutdown: %v", err)
    }
    
    log.Println("Server stopped")
}
```

---

## 📋 Context Checklist

### Junior ✅
- [ ] Use context.Background() for top-level
- [ ] Pass context as first parameter
- [ ] Always defer cancel()
- [ ] Check ctx.Done() in loops

### Mid ✅
- [ ] Use WithTimeout for external calls
- [ ] Store request-scoped values (request ID, user)
- [ ] Handle context.DeadlineExceeded
- [ ] Propagate context through layers

### Senior ✅
- [ ] Type-safe context keys
- [ ] Separate context for cache operations
- [ ] Context-aware logging
- [ ] Graceful shutdown with context

### Expert ✅
- [ ] Custom context implementations
- [ ] Context middleware patterns
- [ ] Distributed tracing with context
- [ ] Performance monitoring via context
