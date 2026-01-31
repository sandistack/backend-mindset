# 🌐 HTTP & API - Web Development dengan Go (Junior → Senior)

Dokumentasi lengkap tentang HTTP handlers dan REST API development di Go.

---

## 🎯 Web Development di Go

```
Go built-in: net/http
- Simple dan powerful
- Tidak perlu framework untuk basic apps

Popular Frameworks:
- Gin: Paling populer, cepat, mirip Express.js
- Echo: Modern, banyak fitur
- Fiber: Inspired by Express, super fast
- Chi: Lightweight router

Rekomendasi:
- Gin untuk production-ready apps
- net/http untuk learning/microservices
```

---

## 1️⃣ JUNIOR LEVEL - net/http Basics

### Hello World Server

```go
package main

import (
    "fmt"
    "log"
    "net/http"
)

func helloHandler(w http.ResponseWriter, r *http.Request) {
    fmt.Fprintf(w, "Hello, World!")
}

func main() {
    http.HandleFunc("/", helloHandler)
    
    fmt.Println("Server starting on :8080...")
    log.Fatal(http.ListenAndServe(":8080", nil))
}
```

### HTTP Methods

```go
package main

import (
    "encoding/json"
    "fmt"
    "log"
    "net/http"
)

func handler(w http.ResponseWriter, r *http.Request) {
    switch r.Method {
    case http.MethodGet:
        fmt.Fprintf(w, "GET request")
    case http.MethodPost:
        fmt.Fprintf(w, "POST request")
    case http.MethodPut:
        fmt.Fprintf(w, "PUT request")
    case http.MethodDelete:
        fmt.Fprintf(w, "DELETE request")
    default:
        http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
    }
}

func main() {
    http.HandleFunc("/api", handler)
    log.Fatal(http.ListenAndServe(":8080", nil))
}
```

### JSON Response

```go
package main

import (
    "encoding/json"
    "log"
    "net/http"
)

type User struct {
    ID    int    `json:"id"`
    Name  string `json:"name"`
    Email string `json:"email"`
}

type Response struct {
    Success bool        `json:"success"`
    Message string      `json:"message,omitempty"`
    Data    interface{} `json:"data,omitempty"`
}

func usersHandler(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    
    users := []User{
        {ID: 1, Name: "John", Email: "john@example.com"},
        {ID: 2, Name: "Jane", Email: "jane@example.com"},
    }
    
    response := Response{
        Success: true,
        Message: "Users retrieved",
        Data:    users,
    }
    
    json.NewEncoder(w).Encode(response)
}

func main() {
    http.HandleFunc("/users", usersHandler)
    log.Fatal(http.ListenAndServe(":8080", nil))
}
```

### Reading Request Body

```go
package main

import (
    "encoding/json"
    "io"
    "log"
    "net/http"
)

type CreateUserRequest struct {
    Name  string `json:"name"`
    Email string `json:"email"`
}

func createUserHandler(w http.ResponseWriter, r *http.Request) {
    if r.Method != http.MethodPost {
        http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
        return
    }
    
    // Read body
    body, err := io.ReadAll(r.Body)
    if err != nil {
        http.Error(w, "Error reading request body", http.StatusBadRequest)
        return
    }
    defer r.Body.Close()
    
    // Parse JSON
    var req CreateUserRequest
    if err := json.Unmarshal(body, &req); err != nil {
        http.Error(w, "Invalid JSON", http.StatusBadRequest)
        return
    }
    
    // Response
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(http.StatusCreated)
    
    response := map[string]interface{}{
        "success": true,
        "message": "User created",
        "data": map[string]string{
            "name":  req.Name,
            "email": req.Email,
        },
    }
    
    json.NewEncoder(w).Encode(response)
}

func main() {
    http.HandleFunc("/users", createUserHandler)
    log.Fatal(http.ListenAndServe(":8080", nil))
}
```

---

## 2️⃣ MID LEVEL - Gin Framework

### Install & Setup

```bash
go get -u github.com/gin-gonic/gin
```

```go
package main

import (
    "net/http"
    
    "github.com/gin-gonic/gin"
)

func main() {
    r := gin.Default() // Includes Logger and Recovery middleware
    
    r.GET("/", func(c *gin.Context) {
        c.JSON(http.StatusOK, gin.H{
            "message": "Hello, World!",
        })
    })
    
    r.Run(":8080")
}
```

### CRUD Operations

```go
package main

import (
    "net/http"
    "strconv"
    "sync"
    
    "github.com/gin-gonic/gin"
)

// Models
type User struct {
    ID    int    `json:"id"`
    Name  string `json:"name"`
    Email string `json:"email"`
}

type CreateUserRequest struct {
    Name  string `json:"name" binding:"required"`
    Email string `json:"email" binding:"required,email"`
}

type UpdateUserRequest struct {
    Name  string `json:"name"`
    Email string `json:"email" binding:"omitempty,email"`
}

// In-memory storage
var (
    users   = make(map[int]User)
    lastID  = 0
    usersMu sync.RWMutex
)

// Handlers
func getUsers(c *gin.Context) {
    usersMu.RLock()
    defer usersMu.RUnlock()
    
    userList := make([]User, 0, len(users))
    for _, user := range users {
        userList = append(userList, user)
    }
    
    c.JSON(http.StatusOK, gin.H{
        "success": true,
        "data":    userList,
    })
}

func getUser(c *gin.Context) {
    id, err := strconv.Atoi(c.Param("id"))
    if err != nil {
        c.JSON(http.StatusBadRequest, gin.H{
            "success": false,
            "error":   "Invalid ID",
        })
        return
    }
    
    usersMu.RLock()
    user, exists := users[id]
    usersMu.RUnlock()
    
    if !exists {
        c.JSON(http.StatusNotFound, gin.H{
            "success": false,
            "error":   "User not found",
        })
        return
    }
    
    c.JSON(http.StatusOK, gin.H{
        "success": true,
        "data":    user,
    })
}

func createUser(c *gin.Context) {
    var req CreateUserRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{
            "success": false,
            "error":   err.Error(),
        })
        return
    }
    
    usersMu.Lock()
    lastID++
    user := User{
        ID:    lastID,
        Name:  req.Name,
        Email: req.Email,
    }
    users[lastID] = user
    usersMu.Unlock()
    
    c.JSON(http.StatusCreated, gin.H{
        "success": true,
        "message": "User created",
        "data":    user,
    })
}

func updateUser(c *gin.Context) {
    id, err := strconv.Atoi(c.Param("id"))
    if err != nil {
        c.JSON(http.StatusBadRequest, gin.H{
            "success": false,
            "error":   "Invalid ID",
        })
        return
    }
    
    var req UpdateUserRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{
            "success": false,
            "error":   err.Error(),
        })
        return
    }
    
    usersMu.Lock()
    defer usersMu.Unlock()
    
    user, exists := users[id]
    if !exists {
        c.JSON(http.StatusNotFound, gin.H{
            "success": false,
            "error":   "User not found",
        })
        return
    }
    
    if req.Name != "" {
        user.Name = req.Name
    }
    if req.Email != "" {
        user.Email = req.Email
    }
    users[id] = user
    
    c.JSON(http.StatusOK, gin.H{
        "success": true,
        "message": "User updated",
        "data":    user,
    })
}

func deleteUser(c *gin.Context) {
    id, err := strconv.Atoi(c.Param("id"))
    if err != nil {
        c.JSON(http.StatusBadRequest, gin.H{
            "success": false,
            "error":   "Invalid ID",
        })
        return
    }
    
    usersMu.Lock()
    defer usersMu.Unlock()
    
    if _, exists := users[id]; !exists {
        c.JSON(http.StatusNotFound, gin.H{
            "success": false,
            "error":   "User not found",
        })
        return
    }
    
    delete(users, id)
    
    c.JSON(http.StatusOK, gin.H{
        "success": true,
        "message": "User deleted",
    })
}

func main() {
    r := gin.Default()
    
    api := r.Group("/api/v1")
    {
        api.GET("/users", getUsers)
        api.GET("/users/:id", getUser)
        api.POST("/users", createUser)
        api.PUT("/users/:id", updateUser)
        api.DELETE("/users/:id", deleteUser)
    }
    
    r.Run(":8080")
}
```

### Query Parameters

```go
package main

import (
    "net/http"
    "strconv"
    
    "github.com/gin-gonic/gin"
)

func searchHandler(c *gin.Context) {
    // GET /search?q=golang&page=1&limit=10
    
    query := c.Query("q")                     // Returns "" if not exists
    page := c.DefaultQuery("page", "1")       // Default value
    limit := c.DefaultQuery("limit", "10")
    
    pageNum, _ := strconv.Atoi(page)
    limitNum, _ := strconv.Atoi(limit)
    
    c.JSON(http.StatusOK, gin.H{
        "query": query,
        "page":  pageNum,
        "limit": limitNum,
    })
}

func main() {
    r := gin.Default()
    r.GET("/search", searchHandler)
    r.Run(":8080")
}
```

### File Upload

```go
package main

import (
    "fmt"
    "net/http"
    "path/filepath"
    
    "github.com/gin-gonic/gin"
)

func uploadHandler(c *gin.Context) {
    // Single file
    file, err := c.FormFile("file")
    if err != nil {
        c.JSON(http.StatusBadRequest, gin.H{
            "error": "No file uploaded",
        })
        return
    }
    
    // Save file
    filename := filepath.Base(file.Filename)
    dst := "./uploads/" + filename
    
    if err := c.SaveUploadedFile(file, dst); err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{
            "error": "Failed to save file",
        })
        return
    }
    
    c.JSON(http.StatusOK, gin.H{
        "message":  "File uploaded",
        "filename": filename,
        "size":     file.Size,
    })
}

func multipleUploadHandler(c *gin.Context) {
    // Multiple files
    form, err := c.MultipartForm()
    if err != nil {
        c.JSON(http.StatusBadRequest, gin.H{
            "error": err.Error(),
        })
        return
    }
    
    files := form.File["files"]
    
    for _, file := range files {
        filename := filepath.Base(file.Filename)
        dst := "./uploads/" + filename
        c.SaveUploadedFile(file, dst)
    }
    
    c.JSON(http.StatusOK, gin.H{
        "message": fmt.Sprintf("%d files uploaded", len(files)),
    })
}

func main() {
    r := gin.Default()
    
    r.MaxMultipartMemory = 8 << 20 // 8 MB
    
    r.POST("/upload", uploadHandler)
    r.POST("/upload/multiple", multipleUploadHandler)
    
    r.Run(":8080")
}
```

---

## 3️⃣ MID LEVEL - Middleware

### Custom Middleware

```go
package main

import (
    "log"
    "net/http"
    "time"
    
    "github.com/gin-gonic/gin"
)

// Logger middleware
func Logger() gin.HandlerFunc {
    return func(c *gin.Context) {
        start := time.Now()
        path := c.Request.URL.Path
        method := c.Request.Method
        
        // Process request
        c.Next()
        
        // After request
        latency := time.Since(start)
        status := c.Writer.Status()
        
        log.Printf("[%s] %s %d %v", method, path, status, latency)
    }
}

// CORS middleware
func CORS() gin.HandlerFunc {
    return func(c *gin.Context) {
        c.Header("Access-Control-Allow-Origin", "*")
        c.Header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        c.Header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        
        if c.Request.Method == "OPTIONS" {
            c.AbortWithStatus(http.StatusNoContent)
            return
        }
        
        c.Next()
    }
}

// Error handler middleware
func ErrorHandler() gin.HandlerFunc {
    return func(c *gin.Context) {
        c.Next()
        
        if len(c.Errors) > 0 {
            err := c.Errors.Last()
            c.JSON(http.StatusInternalServerError, gin.H{
                "success": false,
                "error":   err.Error(),
            })
        }
    }
}

// Rate limiter middleware (simple)
func RateLimiter(maxRequests int, duration time.Duration) gin.HandlerFunc {
    requests := make(map[string][]time.Time)
    
    return func(c *gin.Context) {
        ip := c.ClientIP()
        now := time.Now()
        
        // Clean old requests
        validRequests := []time.Time{}
        for _, t := range requests[ip] {
            if now.Sub(t) < duration {
                validRequests = append(validRequests, t)
            }
        }
        
        if len(validRequests) >= maxRequests {
            c.AbortWithStatusJSON(http.StatusTooManyRequests, gin.H{
                "error": "Rate limit exceeded",
            })
            return
        }
        
        requests[ip] = append(validRequests, now)
        c.Next()
    }
}

func main() {
    r := gin.New()
    
    // Global middleware
    r.Use(Logger())
    r.Use(CORS())
    r.Use(ErrorHandler())
    r.Use(gin.Recovery())
    
    // Rate limited route
    r.GET("/api", RateLimiter(10, time.Minute), func(c *gin.Context) {
        c.JSON(http.StatusOK, gin.H{"message": "OK"})
    })
    
    r.Run(":8080")
}
```

### Authentication Middleware

```go
package main

import (
    "net/http"
    "strings"
    
    "github.com/gin-gonic/gin"
    "github.com/golang-jwt/jwt/v5"
)

var jwtSecret = []byte("your-secret-key")

type Claims struct {
    UserID uint   `json:"user_id"`
    Email  string `json:"email"`
    jwt.RegisteredClaims
}

// Auth middleware
func AuthMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        authHeader := c.GetHeader("Authorization")
        
        if authHeader == "" {
            c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{
                "success": false,
                "error":   "Authorization header required",
            })
            return
        }
        
        // Bearer token
        parts := strings.Split(authHeader, " ")
        if len(parts) != 2 || parts[0] != "Bearer" {
            c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{
                "success": false,
                "error":   "Invalid authorization format",
            })
            return
        }
        
        tokenString := parts[1]
        
        // Parse token
        claims := &Claims{}
        token, err := jwt.ParseWithClaims(tokenString, claims, func(token *jwt.Token) (interface{}, error) {
            return jwtSecret, nil
        })
        
        if err != nil || !token.Valid {
            c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{
                "success": false,
                "error":   "Invalid or expired token",
            })
            return
        }
        
        // Set user info in context
        c.Set("user_id", claims.UserID)
        c.Set("email", claims.Email)
        
        c.Next()
    }
}

func main() {
    r := gin.Default()
    
    // Public routes
    r.POST("/login", loginHandler)
    
    // Protected routes
    protected := r.Group("/api")
    protected.Use(AuthMiddleware())
    {
        protected.GET("/profile", profileHandler)
        protected.GET("/users", usersHandler)
    }
    
    r.Run(":8080")
}

func loginHandler(c *gin.Context) {
    // ... login logic, return JWT
}

func profileHandler(c *gin.Context) {
    userID := c.GetUint("user_id")
    email := c.GetString("email")
    
    c.JSON(http.StatusOK, gin.H{
        "user_id": userID,
        "email":   email,
    })
}

func usersHandler(c *gin.Context) {
    c.JSON(http.StatusOK, gin.H{"message": "Users list"})
}
```

---

## 4️⃣ MID-SENIOR LEVEL - Response Helpers

### Standardized Response

```go
// pkg/response/response.go
package response

import (
    "net/http"
    
    "github.com/gin-gonic/gin"
)

type Response struct {
    Success bool        `json:"success"`
    Message string      `json:"message,omitempty"`
    Data    interface{} `json:"data,omitempty"`
    Error   *ErrorInfo  `json:"error,omitempty"`
    Meta    *Meta       `json:"meta,omitempty"`
}

type ErrorInfo struct {
    Code    string            `json:"code"`
    Message string            `json:"message"`
    Details map[string]string `json:"details,omitempty"`
}

type Meta struct {
    Page       int `json:"page"`
    PerPage    int `json:"per_page"`
    Total      int `json:"total"`
    TotalPages int `json:"total_pages"`
}

// Success responses
func OK(c *gin.Context, message string, data interface{}) {
    c.JSON(http.StatusOK, Response{
        Success: true,
        Message: message,
        Data:    data,
    })
}

func Created(c *gin.Context, message string, data interface{}) {
    c.JSON(http.StatusCreated, Response{
        Success: true,
        Message: message,
        Data:    data,
    })
}

func NoContent(c *gin.Context) {
    c.Status(http.StatusNoContent)
}

// With pagination
func Paginated(c *gin.Context, message string, data interface{}, meta Meta) {
    c.JSON(http.StatusOK, Response{
        Success: true,
        Message: message,
        Data:    data,
        Meta:    &meta,
    })
}

// Error responses
func BadRequest(c *gin.Context, message string, details map[string]string) {
    c.JSON(http.StatusBadRequest, Response{
        Success: false,
        Error: &ErrorInfo{
            Code:    "BAD_REQUEST",
            Message: message,
            Details: details,
        },
    })
}

func Unauthorized(c *gin.Context, message string) {
    c.JSON(http.StatusUnauthorized, Response{
        Success: false,
        Error: &ErrorInfo{
            Code:    "UNAUTHORIZED",
            Message: message,
        },
    })
}

func Forbidden(c *gin.Context, message string) {
    c.JSON(http.StatusForbidden, Response{
        Success: false,
        Error: &ErrorInfo{
            Code:    "FORBIDDEN",
            Message: message,
        },
    })
}

func NotFound(c *gin.Context, resource string) {
    c.JSON(http.StatusNotFound, Response{
        Success: false,
        Error: &ErrorInfo{
            Code:    "NOT_FOUND",
            Message: resource + " not found",
        },
    })
}

func InternalError(c *gin.Context, err error) {
    c.JSON(http.StatusInternalServerError, Response{
        Success: false,
        Error: &ErrorInfo{
            Code:    "INTERNAL_ERROR",
            Message: "An internal error occurred",
        },
    })
}

func ValidationError(c *gin.Context, err error) {
    c.JSON(http.StatusUnprocessableEntity, Response{
        Success: false,
        Error: &ErrorInfo{
            Code:    "VALIDATION_ERROR",
            Message: err.Error(),
        },
    })
}
```

### Usage

```go
package main

import (
    "github.com/gin-gonic/gin"
    "github.com/username/myapp/pkg/response"
)

func getUsers(c *gin.Context) {
    users := []User{
        {ID: 1, Name: "John"},
        {ID: 2, Name: "Jane"},
    }
    
    response.OK(c, "Users retrieved", users)
}

func getUsersPaginated(c *gin.Context) {
    users := []User{...}
    
    response.Paginated(c, "Users retrieved", users, response.Meta{
        Page:       1,
        PerPage:    10,
        Total:      100,
        TotalPages: 10,
    })
}

func getUser(c *gin.Context) {
    user, err := findUser(id)
    if err != nil {
        response.NotFound(c, "User")
        return
    }
    
    response.OK(c, "User retrieved", user)
}

func createUser(c *gin.Context) {
    var req CreateUserRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        response.ValidationError(c, err)
        return
    }
    
    user, err := createUser(req)
    if err != nil {
        response.InternalError(c, err)
        return
    }
    
    response.Created(c, "User created", user)
}
```

---

## 5️⃣ SENIOR LEVEL - Validation

### Struct Validation dengan Tags

```go
package main

import (
    "net/http"
    
    "github.com/gin-gonic/gin"
    "github.com/gin-gonic/gin/binding"
    "github.com/go-playground/validator/v10"
)

type CreateUserRequest struct {
    Name     string `json:"name" binding:"required,min=2,max=100"`
    Email    string `json:"email" binding:"required,email"`
    Password string `json:"password" binding:"required,min=8,containsany=!@#$%"`
    Age      int    `json:"age" binding:"required,gte=18,lte=120"`
    Phone    string `json:"phone" binding:"required,e164"` // +628123456789
    Website  string `json:"website" binding:"omitempty,url"`
    Role     string `json:"role" binding:"required,oneof=admin user moderator"`
}

// Common validation tags:
// required     - Field must be present
// omitempty    - Skip validation if empty
// min=n        - Minimum length/value
// max=n        - Maximum length/value
// len=n        - Exact length
// gte=n        - Greater than or equal
// lte=n        - Less than or equal
// email        - Valid email format
// url          - Valid URL format
// oneof=a b    - Value must be one of listed
// e164         - Valid phone number
// uuid         - Valid UUID
// datetime     - Valid datetime
```

### Custom Validation

```go
package main

import (
    "net/http"
    "regexp"
    
    "github.com/gin-gonic/gin"
    "github.com/gin-gonic/gin/binding"
    "github.com/go-playground/validator/v10"
)

// Custom validator
func validUsername(fl validator.FieldLevel) bool {
    value := fl.Field().String()
    match, _ := regexp.MatchString(`^[a-zA-Z0-9_]+$`, value)
    return match
}

func validIndonesianPhone(fl validator.FieldLevel) bool {
    value := fl.Field().String()
    match, _ := regexp.MatchString(`^\+62[0-9]{9,12}$`, value)
    return match
}

// Register custom validators
func registerValidators() {
    if v, ok := binding.Validator.Engine().(*validator.Validate); ok {
        v.RegisterValidation("username", validUsername)
        v.RegisterValidation("indonesian_phone", validIndonesianPhone)
    }
}

type RegisterRequest struct {
    Username string `json:"username" binding:"required,username,min=3,max=20"`
    Phone    string `json:"phone" binding:"required,indonesian_phone"`
}

func main() {
    registerValidators()
    
    r := gin.Default()
    
    r.POST("/register", func(c *gin.Context) {
        var req RegisterRequest
        if err := c.ShouldBindJSON(&req); err != nil {
            c.JSON(http.StatusBadRequest, gin.H{
                "error": err.Error(),
            })
            return
        }
        
        c.JSON(http.StatusOK, gin.H{
            "message": "Valid!",
            "data":    req,
        })
    })
    
    r.Run(":8080")
}
```

### Validation Error Formatting

```go
package main

import (
    "net/http"
    
    "github.com/gin-gonic/gin"
    "github.com/go-playground/validator/v10"
)

// Format validation errors
func formatValidationErrors(err error) map[string]string {
    errors := make(map[string]string)
    
    if validationErrors, ok := err.(validator.ValidationErrors); ok {
        for _, e := range validationErrors {
            field := e.Field()
            tag := e.Tag()
            
            switch tag {
            case "required":
                errors[field] = field + " is required"
            case "email":
                errors[field] = field + " must be a valid email"
            case "min":
                errors[field] = field + " must be at least " + e.Param() + " characters"
            case "max":
                errors[field] = field + " must be at most " + e.Param() + " characters"
            case "gte":
                errors[field] = field + " must be at least " + e.Param()
            case "lte":
                errors[field] = field + " must be at most " + e.Param()
            case "oneof":
                errors[field] = field + " must be one of: " + e.Param()
            default:
                errors[field] = field + " is invalid"
            }
        }
    }
    
    return errors
}

func createUserHandler(c *gin.Context) {
    var req CreateUserRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{
            "success": false,
            "errors":  formatValidationErrors(err),
        })
        return
    }
    
    // ... create user
}
```

---

## 6️⃣ SENIOR LEVEL - Graceful Shutdown

```go
package main

import (
    "context"
    "log"
    "net/http"
    "os"
    "os/signal"
    "syscall"
    "time"
    
    "github.com/gin-gonic/gin"
)

func main() {
    r := gin.Default()
    
    r.GET("/", func(c *gin.Context) {
        c.JSON(http.StatusOK, gin.H{"message": "Hello!"})
    })
    
    // Create server
    srv := &http.Server{
        Addr:    ":8080",
        Handler: r,
    }
    
    // Start server in goroutine
    go func() {
        log.Println("Server starting on :8080")
        if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
            log.Fatalf("Failed to start server: %v", err)
        }
    }()
    
    // Wait for interrupt signal
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit
    
    log.Println("Shutting down server...")
    
    // Graceful shutdown with timeout
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()
    
    if err := srv.Shutdown(ctx); err != nil {
        log.Fatal("Server forced to shutdown:", err)
    }
    
    log.Println("Server exited gracefully")
}
```

---

## 7️⃣ EXPERT LEVEL - Complete API Structure

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
    
    "github.com/username/myapp/internal/config"
    "github.com/username/myapp/internal/delivery/http/router"
    "github.com/username/myapp/internal/repository"
    "github.com/username/myapp/internal/usecase"
)

func main() {
    // Load config
    cfg := config.Load()
    
    // Initialize database
    db := config.NewDatabase(cfg)
    
    // Initialize layers
    userRepo := repository.NewUserRepository(db)
    userUsecase := usecase.NewUserUsecase(userRepo)
    
    // Initialize router
    r := router.NewRouter(cfg, userUsecase)
    
    // Server
    srv := &http.Server{
        Addr:         ":" + cfg.Port,
        Handler:      r,
        ReadTimeout:  15 * time.Second,
        WriteTimeout: 15 * time.Second,
        IdleTimeout:  60 * time.Second,
    }
    
    // Start server
    go func() {
        log.Printf("Server starting on :%s", cfg.Port)
        if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
            log.Fatalf("Server error: %v", err)
        }
    }()
    
    // Graceful shutdown
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit
    
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()
    
    if err := srv.Shutdown(ctx); err != nil {
        log.Fatal("Shutdown error:", err)
    }
    
    log.Println("Server stopped")
}
```

---

## 📊 HTTP Framework Comparison

| Feature | net/http | Gin | Echo | Fiber |
|---------|----------|-----|------|-------|
| Performance | Good | Excellent | Excellent | Best |
| Learning Curve | Easy | Easy | Easy | Easy |
| Middleware | Manual | Built-in | Built-in | Built-in |
| Routing | Basic | Advanced | Advanced | Advanced |
| Validation | Manual | Built-in | Built-in | Built-in |
| Popularity | Standard | Most Popular | Popular | Growing |
| Use Case | Simple APIs | Production | Production | High-perf |

---

## 💡 Summary

| Level | Focus |
|-------|-------|
| **Junior** | net/http basics, JSON, request handling |
| **Mid** | Gin framework, CRUD, middleware |
| **Mid-Senior** | Custom middleware, auth, validation |
| **Senior** | Response helpers, graceful shutdown |
| **Expert** | Clean architecture, production setup |

**Best Practices:**
- ✅ Use framework for production apps (Gin/Echo)
- ✅ Always validate input
- ✅ Standardize response format
- ✅ Implement graceful shutdown
- ✅ Use middleware for cross-cutting concerns
- ✅ Set appropriate timeouts
- ❌ Don't expose raw errors to clients
- ❌ Don't skip authentication middleware
