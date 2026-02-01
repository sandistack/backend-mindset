# 🔗 Middleware di Go

## Kenapa Penting?

Middleware adalah cara untuk:
- ✅ Menjalankan code sebelum/sesudah handler
- ✅ Reusable logic (auth, logging, CORS)
- ✅ Chain of responsibility pattern
- ✅ Clean separation of concerns

---

## 📚 Daftar Isi

1. [Middleware Basics](#1️⃣-middleware-basics)
2. [Common Middleware](#2️⃣-common-middleware)
3. [Chi Middleware](#3️⃣-chi-middleware)
4. [Gin Middleware](#4️⃣-gin-middleware)
5. [Custom Middleware](#5️⃣-custom-middleware)
6. [Middleware Chain](#6️⃣-middleware-chain)
7. [Context & Middleware](#7️⃣-context--middleware)
8. [Testing Middleware](#8️⃣-testing-middleware)

---

## 1️⃣ Middleware Basics

### Standard Library Pattern

```go
// Middleware signature
type Middleware func(http.Handler) http.Handler

// Basic middleware
func LoggingMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        
        // Before handler
        log.Printf("Started %s %s", r.Method, r.URL.Path)
        
        // Call next handler
        next.ServeHTTP(w, r)
        
        // After handler
        log.Printf("Completed in %v", time.Since(start))
    })
}

// Using middleware
func main() {
    mux := http.NewServeMux()
    mux.HandleFunc("/", homeHandler)
    
    // Wrap with middleware
    handler := LoggingMiddleware(mux)
    
    http.ListenAndServe(":8080", handler)
}
```

### Middleware Chain

```go
// Chain multiple middleware
func Chain(h http.Handler, middlewares ...Middleware) http.Handler {
    for i := len(middlewares) - 1; i >= 0; i-- {
        h = middlewares[i](h)
    }
    return h
}

// Usage
handler := Chain(
    mux,
    LoggingMiddleware,
    AuthMiddleware,
    CORSMiddleware,
)
```

---

## 2️⃣ Common Middleware

### Logging Middleware

```go
// internal/middleware/logging.go
package middleware

import (
    "log"
    "net/http"
    "time"
)

type responseWriter struct {
    http.ResponseWriter
    status      int
    wroteHeader bool
}

func wrapResponseWriter(w http.ResponseWriter) *responseWriter {
    return &responseWriter{ResponseWriter: w, status: http.StatusOK}
}

func (rw *responseWriter) WriteHeader(code int) {
    if !rw.wroteHeader {
        rw.status = code
        rw.wroteHeader = true
        rw.ResponseWriter.WriteHeader(code)
    }
}

func Logging(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        
        wrapped := wrapResponseWriter(w)
        next.ServeHTTP(wrapped, r)
        
        log.Printf(
            "%s %s %d %s",
            r.Method,
            r.URL.Path,
            wrapped.status,
            time.Since(start),
        )
    })
}
```

### CORS Middleware

```go
// internal/middleware/cors.go
package middleware

import "net/http"

func CORS(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("Access-Control-Allow-Origin", "*")
        w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS, PATCH")
        w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Request-ID")
        w.Header().Set("Access-Control-Max-Age", "86400")
        
        // Handle preflight
        if r.Method == http.MethodOptions {
            w.WriteHeader(http.StatusNoContent)
            return
        }
        
        next.ServeHTTP(w, r)
    })
}

// Configurable CORS
type CORSConfig struct {
    AllowOrigins     []string
    AllowMethods     []string
    AllowHeaders     []string
    AllowCredentials bool
    MaxAge           int
}

func CORSWithConfig(config CORSConfig) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            origin := r.Header.Get("Origin")
            
            // Check if origin is allowed
            allowed := false
            for _, o := range config.AllowOrigins {
                if o == "*" || o == origin {
                    allowed = true
                    break
                }
            }
            
            if allowed {
                w.Header().Set("Access-Control-Allow-Origin", origin)
            }
            
            if config.AllowCredentials {
                w.Header().Set("Access-Control-Allow-Credentials", "true")
            }
            
            if r.Method == http.MethodOptions {
                w.Header().Set("Access-Control-Allow-Methods", strings.Join(config.AllowMethods, ", "))
                w.Header().Set("Access-Control-Allow-Headers", strings.Join(config.AllowHeaders, ", "))
                w.Header().Set("Access-Control-Max-Age", strconv.Itoa(config.MaxAge))
                w.WriteHeader(http.StatusNoContent)
                return
            }
            
            next.ServeHTTP(w, r)
        })
    }
}
```

### Request ID Middleware

```go
// internal/middleware/request_id.go
package middleware

import (
    "context"
    "net/http"
    
    "github.com/google/uuid"
)

type contextKey string

const RequestIDKey contextKey = "request_id"

func RequestID(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // Check for existing request ID
        requestID := r.Header.Get("X-Request-ID")
        if requestID == "" {
            requestID = uuid.New().String()
        }
        
        // Add to context
        ctx := context.WithValue(r.Context(), RequestIDKey, requestID)
        
        // Add to response header
        w.Header().Set("X-Request-ID", requestID)
        
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

// Helper to get request ID from context
func GetRequestID(ctx context.Context) string {
    if id, ok := ctx.Value(RequestIDKey).(string); ok {
        return id
    }
    return ""
}
```

---

## 3️⃣ Chi Middleware

### Using Chi's Built-in Middleware

```go
import (
    "github.com/go-chi/chi/v5"
    "github.com/go-chi/chi/v5/middleware"
)

func main() {
    r := chi.NewRouter()
    
    // Built-in middleware
    r.Use(middleware.RequestID)
    r.Use(middleware.RealIP)
    r.Use(middleware.Logger)
    r.Use(middleware.Recoverer)
    r.Use(middleware.Timeout(60 * time.Second))
    r.Use(middleware.Compress(5))
    
    // Custom middleware
    r.Use(CustomMiddleware)
    
    r.Get("/", homeHandler)
    
    http.ListenAndServe(":8080", r)
}
```

### Chi Middleware for Specific Routes

```go
r := chi.NewRouter()

// Global middleware
r.Use(middleware.Logger)

// Group with specific middleware
r.Group(func(r chi.Router) {
    r.Use(AuthMiddleware)
    
    r.Get("/profile", profileHandler)
    r.Get("/settings", settingsHandler)
})

// Route-specific middleware
r.With(AdminOnly).Get("/admin", adminHandler)

// Subrouter with middleware
r.Route("/api/v1", func(r chi.Router) {
    r.Use(APIKeyMiddleware)
    
    r.Get("/users", listUsers)
    r.Post("/users", createUser)
})
```

---

## 4️⃣ Gin Middleware

### Using Gin Middleware

```go
import "github.com/gin-gonic/gin"

func main() {
    r := gin.New()
    
    // Built-in middleware
    r.Use(gin.Logger())
    r.Use(gin.Recovery())
    
    // Custom middleware
    r.Use(CustomMiddleware())
    
    // Group with middleware
    api := r.Group("/api")
    api.Use(AuthMiddleware())
    {
        api.GET("/users", listUsers)
        api.POST("/users", createUser)
    }
    
    r.Run(":8080")
}

// Gin middleware function
func CustomMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        // Before
        start := time.Now()
        
        // Process request
        c.Next()
        
        // After
        latency := time.Since(start)
        status := c.Writer.Status()
        
        log.Printf("%d | %v | %s", status, latency, c.Request.URL.Path)
    }
}
```

### Gin Auth Middleware

```go
func AuthMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        token := c.GetHeader("Authorization")
        
        if token == "" {
            c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{
                "error": "Authorization header required",
            })
            return
        }
        
        // Validate token
        claims, err := ValidateToken(strings.TrimPrefix(token, "Bearer "))
        if err != nil {
            c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{
                "error": "Invalid token",
            })
            return
        }
        
        // Set user in context
        c.Set("user_id", claims.UserID)
        c.Set("user_role", claims.Role)
        
        c.Next()
    }
}
```

---

## 5️⃣ Custom Middleware

### Authentication Middleware

```go
// internal/middleware/auth.go
package middleware

import (
    "context"
    "net/http"
    "strings"
)

type UserContextKey string

const UserKey UserContextKey = "user"

type User struct {
    ID    int
    Email string
    Role  string
}

func Auth(jwtService *JWTService) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            authHeader := r.Header.Get("Authorization")
            
            if authHeader == "" {
                respondError(w, http.StatusUnauthorized, "Authorization header required")
                return
            }
            
            // Extract token
            parts := strings.Split(authHeader, " ")
            if len(parts) != 2 || parts[0] != "Bearer" {
                respondError(w, http.StatusUnauthorized, "Invalid authorization format")
                return
            }
            
            token := parts[1]
            
            // Validate token
            claims, err := jwtService.ValidateToken(token)
            if err != nil {
                respondError(w, http.StatusUnauthorized, "Invalid token")
                return
            }
            
            // Add user to context
            user := &User{
                ID:    claims.UserID,
                Email: claims.Email,
                Role:  claims.Role,
            }
            
            ctx := context.WithValue(r.Context(), UserKey, user)
            next.ServeHTTP(w, r.WithContext(ctx))
        })
    }
}

// Helper to get user from context
func GetUser(ctx context.Context) *User {
    if user, ok := ctx.Value(UserKey).(*User); ok {
        return user
    }
    return nil
}
```

### Role-Based Access Control

```go
// internal/middleware/rbac.go
package middleware

import "net/http"

func RequireRole(roles ...string) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            user := GetUser(r.Context())
            
            if user == nil {
                respondError(w, http.StatusUnauthorized, "Unauthorized")
                return
            }
            
            // Check if user has required role
            hasRole := false
            for _, role := range roles {
                if user.Role == role {
                    hasRole = true
                    break
                }
            }
            
            if !hasRole {
                respondError(w, http.StatusForbidden, "Insufficient permissions")
                return
            }
            
            next.ServeHTTP(w, r)
        })
    }
}

// Usage
r.With(RequireRole("admin", "moderator")).Get("/admin", adminHandler)
r.With(RequireRole("admin")).Delete("/users/{id}", deleteUser)
```

### Rate Limiting Middleware

```go
// internal/middleware/rate_limit.go
package middleware

import (
    "net/http"
    "sync"
    "time"
    
    "golang.org/x/time/rate"
)

type IPRateLimiter struct {
    ips   map[string]*rate.Limiter
    mu    *sync.RWMutex
    rate  rate.Limit
    burst int
}

func NewIPRateLimiter(r rate.Limit, b int) *IPRateLimiter {
    return &IPRateLimiter{
        ips:   make(map[string]*rate.Limiter),
        mu:    &sync.RWMutex{},
        rate:  r,
        burst: b,
    }
}

func (i *IPRateLimiter) GetLimiter(ip string) *rate.Limiter {
    i.mu.Lock()
    defer i.mu.Unlock()
    
    limiter, exists := i.ips[ip]
    if !exists {
        limiter = rate.NewLimiter(i.rate, i.burst)
        i.ips[ip] = limiter
    }
    
    return limiter
}

func RateLimit(limiter *IPRateLimiter) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            ip := r.RemoteAddr
            
            if !limiter.GetLimiter(ip).Allow() {
                w.Header().Set("Retry-After", "60")
                respondError(w, http.StatusTooManyRequests, "Rate limit exceeded")
                return
            }
            
            next.ServeHTTP(w, r)
        })
    }
}

// Usage
limiter := NewIPRateLimiter(rate.Limit(10), 20) // 10 req/sec, burst 20
r.Use(RateLimit(limiter))
```

---

## 6️⃣ Middleware Chain

### Configurable Middleware Stack

```go
// internal/middleware/stack.go
package middleware

type Stack struct {
    middlewares []func(http.Handler) http.Handler
}

func NewStack() *Stack {
    return &Stack{
        middlewares: make([]func(http.Handler) http.Handler, 0),
    }
}

func (s *Stack) Use(mw func(http.Handler) http.Handler) *Stack {
    s.middlewares = append(s.middlewares, mw)
    return s
}

func (s *Stack) Then(h http.Handler) http.Handler {
    for i := len(s.middlewares) - 1; i >= 0; i-- {
        h = s.middlewares[i](h)
    }
    return h
}

func (s *Stack) ThenFunc(fn http.HandlerFunc) http.Handler {
    return s.Then(fn)
}

// Usage
commonMiddleware := NewStack().
    Use(RequestID).
    Use(Logging).
    Use(Recovery).
    Use(CORS)

authMiddleware := NewStack().
    Use(Auth(jwtService)).
    Use(RequireRole("user"))

// Apply to handler
http.Handle("/api/tasks", authMiddleware.Then(
    commonMiddleware.Then(tasksHandler),
))
```

### Chi-style Middleware Groups

```go
func SetupRouter(jwtService *JWTService) *chi.Mux {
    r := chi.NewRouter()
    
    // Global middleware
    r.Use(middleware.RequestID)
    r.Use(middleware.RealIP)
    r.Use(middleware.Logger)
    r.Use(middleware.Recoverer)
    r.Use(CORS)
    
    // Public routes
    r.Group(func(r chi.Router) {
        r.Post("/auth/login", loginHandler)
        r.Post("/auth/register", registerHandler)
        r.Get("/health", healthHandler)
    })
    
    // Protected routes
    r.Group(func(r chi.Router) {
        r.Use(Auth(jwtService))
        
        // User routes
        r.Get("/me", getMeHandler)
        r.Put("/me", updateMeHandler)
        
        // Task routes
        r.Route("/tasks", func(r chi.Router) {
            r.Get("/", listTasksHandler)
            r.Post("/", createTaskHandler)
            r.Get("/{id}", getTaskHandler)
            r.Put("/{id}", updateTaskHandler)
            r.Delete("/{id}", deleteTaskHandler)
        })
    })
    
    // Admin routes
    r.Group(func(r chi.Router) {
        r.Use(Auth(jwtService))
        r.Use(RequireRole("admin"))
        
        r.Get("/admin/users", listAllUsersHandler)
        r.Delete("/admin/users/{id}", deleteUserHandler)
    })
    
    return r
}
```

---

## 7️⃣ Context & Middleware

### Storing Values in Context

```go
// internal/middleware/context.go
package middleware

import (
    "context"
    "net/http"
    "time"
)

type ContextKey string

const (
    RequestIDKey   ContextKey = "request_id"
    UserKey        ContextKey = "user"
    RequestTimeKey ContextKey = "request_time"
    TenantKey      ContextKey = "tenant"
)

// Set value in context
func WithRequestID(ctx context.Context, id string) context.Context {
    return context.WithValue(ctx, RequestIDKey, id)
}

func WithUser(ctx context.Context, user *User) context.Context {
    return context.WithValue(ctx, UserKey, user)
}

func WithTenant(ctx context.Context, tenantID string) context.Context {
    return context.WithValue(ctx, TenantKey, tenantID)
}

// Get value from context
func GetRequestID(ctx context.Context) string {
    if v, ok := ctx.Value(RequestIDKey).(string); ok {
        return v
    }
    return ""
}

func GetUser(ctx context.Context) *User {
    if v, ok := ctx.Value(UserKey).(*User); ok {
        return v
    }
    return nil
}

func MustGetUser(ctx context.Context) *User {
    user := GetUser(ctx)
    if user == nil {
        panic("user not found in context")
    }
    return user
}
```

### Using Context in Handlers

```go
func CreateTaskHandler(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()
    
    // Get user from context (set by auth middleware)
    user := middleware.GetUser(ctx)
    if user == nil {
        respondError(w, http.StatusUnauthorized, "User not found")
        return
    }
    
    // Get request ID for logging
    requestID := middleware.GetRequestID(ctx)
    log.Printf("[%s] Creating task for user %d", requestID, user.ID)
    
    // Parse input
    var input CreateTaskInput
    if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
        respondError(w, http.StatusBadRequest, "Invalid JSON")
        return
    }
    
    // Create task
    task, err := taskService.Create(ctx, user.ID, input)
    if err != nil {
        log.Printf("[%s] Failed to create task: %v", requestID, err)
        respondError(w, http.StatusInternalServerError, "Failed to create task")
        return
    }
    
    respondJSON(w, http.StatusCreated, task)
}
```

---

## 8️⃣ Testing Middleware

### Unit Testing Middleware

```go
// internal/middleware/auth_test.go
package middleware_test

import (
    "net/http"
    "net/http/httptest"
    "testing"
    
    "myapp/internal/middleware"
)

func TestAuthMiddleware(t *testing.T) {
    jwtService := NewMockJWTService()
    authMiddleware := middleware.Auth(jwtService)
    
    tests := []struct {
        name           string
        authHeader     string
        expectedStatus int
    }{
        {
            name:           "no auth header",
            authHeader:     "",
            expectedStatus: http.StatusUnauthorized,
        },
        {
            name:           "invalid format",
            authHeader:     "InvalidToken",
            expectedStatus: http.StatusUnauthorized,
        },
        {
            name:           "invalid token",
            authHeader:     "Bearer invalid_token",
            expectedStatus: http.StatusUnauthorized,
        },
        {
            name:           "valid token",
            authHeader:     "Bearer valid_token",
            expectedStatus: http.StatusOK,
        },
    }
    
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // Create test handler
            handler := authMiddleware(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
                w.WriteHeader(http.StatusOK)
            }))
            
            // Create request
            req := httptest.NewRequest("GET", "/test", nil)
            if tt.authHeader != "" {
                req.Header.Set("Authorization", tt.authHeader)
            }
            
            // Record response
            rr := httptest.NewRecorder()
            handler.ServeHTTP(rr, req)
            
            // Check status
            if rr.Code != tt.expectedStatus {
                t.Errorf("expected status %d, got %d", tt.expectedStatus, rr.Code)
            }
        })
    }
}

func TestLoggingMiddleware(t *testing.T) {
    handler := middleware.Logging(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.WriteHeader(http.StatusOK)
        w.Write([]byte("OK"))
    }))
    
    req := httptest.NewRequest("GET", "/test", nil)
    rr := httptest.NewRecorder()
    
    handler.ServeHTTP(rr, req)
    
    if rr.Code != http.StatusOK {
        t.Errorf("expected status 200, got %d", rr.Code)
    }
}
```

### Integration Testing with Middleware

```go
func TestAPIWithMiddleware(t *testing.T) {
    // Setup router with middleware
    r := chi.NewRouter()
    r.Use(middleware.RequestID)
    r.Use(middleware.Logging)
    r.Use(middleware.Auth(jwtService))
    
    r.Get("/protected", func(w http.ResponseWriter, r *http.Request) {
        user := middleware.GetUser(r.Context())
        json.NewEncoder(w).Encode(map[string]int{"user_id": user.ID})
    })
    
    // Test with valid token
    req := httptest.NewRequest("GET", "/protected", nil)
    req.Header.Set("Authorization", "Bearer "+validToken)
    
    rr := httptest.NewRecorder()
    r.ServeHTTP(rr, req)
    
    if rr.Code != http.StatusOK {
        t.Errorf("expected 200, got %d", rr.Code)
    }
    
    // Check request ID in response
    if rr.Header().Get("X-Request-ID") == "" {
        t.Error("expected X-Request-ID header")
    }
}
```

---

## 📋 Middleware Checklist

### Junior ✅
- [ ] Understand middleware pattern
- [ ] Use built-in middleware (Logger, Recoverer)
- [ ] Basic CORS setup

### Mid ✅
- [ ] Custom auth middleware
- [ ] Request ID tracking
- [ ] Response wrapper for status capture
- [ ] Middleware groups/routes

### Senior ✅
- [ ] Role-based access control
- [ ] Rate limiting
- [ ] Context management
- [ ] Configurable middleware

### Expert ✅
- [ ] Middleware stack builder
- [ ] Testing middleware
- [ ] Performance optimization
- [ ] Distributed tracing integration
