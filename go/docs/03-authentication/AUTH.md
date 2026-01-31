# 🔐 AUTHENTICATION - JWT & Auth di Go (Junior → Senior)

Dokumentasi lengkap tentang authentication dan authorization di Go.

---

## 🎯 Authentication vs Authorization

```
Authentication (AuthN):
- "Siapa kamu?" (Who are you?)
- Verify identity
- Login, JWT, Session

Authorization (AuthZ):
- "Boleh akses?" (What can you do?)
- Verify permissions
- Roles, Permissions, RBAC
```

---

## 1️⃣ JUNIOR LEVEL - Password Hashing

### bcrypt untuk Password

```go
package main

import (
    "fmt"
    "log"
    
    "golang.org/x/crypto/bcrypt"
)

func main() {
    password := "mysecretpassword"
    
    // Hash password
    hashedPassword, err := bcrypt.GenerateFromPassword(
        []byte(password),
        bcrypt.DefaultCost, // Cost factor (10-14 recommended)
    )
    if err != nil {
        log.Fatal(err)
    }
    
    fmt.Println("Hashed:", string(hashedPassword))
    // $2a$10$N9qo8uLOickgx2ZMRZoMye...
    
    // Verify password
    err = bcrypt.CompareHashAndPassword(hashedPassword, []byte(password))
    if err != nil {
        fmt.Println("Password incorrect")
    } else {
        fmt.Println("Password correct!")
    }
    
    // Wrong password
    err = bcrypt.CompareHashAndPassword(hashedPassword, []byte("wrongpassword"))
    if err != nil {
        fmt.Println("Password incorrect") // This will print
    }
}
```

### Password Service

```go
// internal/service/password.go
package service

import (
    "errors"
    
    "golang.org/x/crypto/bcrypt"
)

var (
    ErrPasswordTooShort = errors.New("password must be at least 8 characters")
    ErrPasswordMismatch = errors.New("password does not match")
)

type PasswordService struct {
    cost int
}

func NewPasswordService() *PasswordService {
    return &PasswordService{cost: bcrypt.DefaultCost}
}

func (s *PasswordService) Hash(password string) (string, error) {
    if len(password) < 8 {
        return "", ErrPasswordTooShort
    }
    
    hashed, err := bcrypt.GenerateFromPassword([]byte(password), s.cost)
    if err != nil {
        return "", err
    }
    
    return string(hashed), nil
}

func (s *PasswordService) Verify(hashedPassword, password string) error {
    err := bcrypt.CompareHashAndPassword([]byte(hashedPassword), []byte(password))
    if err != nil {
        return ErrPasswordMismatch
    }
    return nil
}
```

---

## 2️⃣ MID LEVEL - JWT Authentication

### Install JWT Library

```bash
go get -u github.com/golang-jwt/jwt/v5
```

### JWT Service

```go
// internal/service/jwt.go
package service

import (
    "errors"
    "time"
    
    "github.com/golang-jwt/jwt/v5"
)

var (
    ErrInvalidToken = errors.New("invalid token")
    ErrExpiredToken = errors.New("token has expired")
)

type JWTService struct {
    secretKey     []byte
    accessExpiry  time.Duration
    refreshExpiry time.Duration
}

type Claims struct {
    UserID uint   `json:"user_id"`
    Email  string `json:"email"`
    Role   string `json:"role"`
    jwt.RegisteredClaims
}

type TokenPair struct {
    AccessToken  string `json:"access_token"`
    RefreshToken string `json:"refresh_token"`
    ExpiresIn    int64  `json:"expires_in"`
}

func NewJWTService(secretKey string) *JWTService {
    return &JWTService{
        secretKey:     []byte(secretKey),
        accessExpiry:  15 * time.Minute,
        refreshExpiry: 7 * 24 * time.Hour,
    }
}

func (s *JWTService) GenerateTokenPair(userID uint, email, role string) (*TokenPair, error) {
    // Access token
    accessToken, err := s.generateToken(userID, email, role, s.accessExpiry)
    if err != nil {
        return nil, err
    }
    
    // Refresh token
    refreshToken, err := s.generateToken(userID, email, role, s.refreshExpiry)
    if err != nil {
        return nil, err
    }
    
    return &TokenPair{
        AccessToken:  accessToken,
        RefreshToken: refreshToken,
        ExpiresIn:    int64(s.accessExpiry.Seconds()),
    }, nil
}

func (s *JWTService) generateToken(userID uint, email, role string, expiry time.Duration) (string, error) {
    claims := Claims{
        UserID: userID,
        Email:  email,
        Role:   role,
        RegisteredClaims: jwt.RegisteredClaims{
            ExpiresAt: jwt.NewNumericDate(time.Now().Add(expiry)),
            IssuedAt:  jwt.NewNumericDate(time.Now()),
            NotBefore: jwt.NewNumericDate(time.Now()),
        },
    }
    
    token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
    return token.SignedString(s.secretKey)
}

func (s *JWTService) ValidateToken(tokenString string) (*Claims, error) {
    token, err := jwt.ParseWithClaims(tokenString, &Claims{}, func(token *jwt.Token) (interface{}, error) {
        // Validate signing method
        if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
            return nil, ErrInvalidToken
        }
        return s.secretKey, nil
    })
    
    if err != nil {
        if errors.Is(err, jwt.ErrTokenExpired) {
            return nil, ErrExpiredToken
        }
        return nil, ErrInvalidToken
    }
    
    claims, ok := token.Claims.(*Claims)
    if !ok || !token.Valid {
        return nil, ErrInvalidToken
    }
    
    return claims, nil
}

func (s *JWTService) RefreshToken(refreshToken string) (*TokenPair, error) {
    claims, err := s.ValidateToken(refreshToken)
    if err != nil {
        return nil, err
    }
    
    return s.GenerateTokenPair(claims.UserID, claims.Email, claims.Role)
}
```

---

## 3️⃣ MID LEVEL - Auth Handlers

### Login & Register

```go
// internal/handler/auth.go
package handler

import (
    "net/http"
    
    "github.com/gin-gonic/gin"
    "github.com/username/myapp/internal/service"
    "github.com/username/myapp/internal/repository"
    "github.com/username/myapp/pkg/response"
)

type AuthHandler struct {
    userRepo    repository.UserRepository
    jwtService  *service.JWTService
    passwordSvc *service.PasswordService
}

func NewAuthHandler(
    userRepo repository.UserRepository,
    jwtService *service.JWTService,
    passwordSvc *service.PasswordService,
) *AuthHandler {
    return &AuthHandler{
        userRepo:    userRepo,
        jwtService:  jwtService,
        passwordSvc: passwordSvc,
    }
}

type RegisterRequest struct {
    Name     string `json:"name" binding:"required,min=2,max=100"`
    Email    string `json:"email" binding:"required,email"`
    Password string `json:"password" binding:"required,min=8"`
}

type LoginRequest struct {
    Email    string `json:"email" binding:"required,email"`
    Password string `json:"password" binding:"required"`
}

func (h *AuthHandler) Register(c *gin.Context) {
    var req RegisterRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        response.BadRequest(c, err.Error(), nil)
        return
    }
    
    // Check if email exists
    existing, _ := h.userRepo.FindByEmail(c.Request.Context(), req.Email)
    if existing != nil {
        response.BadRequest(c, "Email already exists", nil)
        return
    }
    
    // Hash password
    hashedPassword, err := h.passwordSvc.Hash(req.Password)
    if err != nil {
        response.BadRequest(c, err.Error(), nil)
        return
    }
    
    // Create user
    user := &models.User{
        Name:     req.Name,
        Email:    req.Email,
        Password: hashedPassword,
        Role:     "user",
    }
    
    if err := h.userRepo.Create(c.Request.Context(), user); err != nil {
        response.InternalError(c, err)
        return
    }
    
    // Generate tokens
    tokens, err := h.jwtService.GenerateTokenPair(user.ID, user.Email, user.Role)
    if err != nil {
        response.InternalError(c, err)
        return
    }
    
    response.Created(c, "Registration successful", gin.H{
        "user":   user,
        "tokens": tokens,
    })
}

func (h *AuthHandler) Login(c *gin.Context) {
    var req LoginRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        response.BadRequest(c, err.Error(), nil)
        return
    }
    
    // Find user
    user, err := h.userRepo.FindByEmail(c.Request.Context(), req.Email)
    if err != nil || user == nil {
        response.Unauthorized(c, "Invalid credentials")
        return
    }
    
    // Verify password
    if err := h.passwordSvc.Verify(user.Password, req.Password); err != nil {
        response.Unauthorized(c, "Invalid credentials")
        return
    }
    
    // Generate tokens
    tokens, err := h.jwtService.GenerateTokenPair(user.ID, user.Email, user.Role)
    if err != nil {
        response.InternalError(c, err)
        return
    }
    
    response.OK(c, "Login successful", gin.H{
        "user":   user,
        "tokens": tokens,
    })
}

func (h *AuthHandler) RefreshToken(c *gin.Context) {
    var req struct {
        RefreshToken string `json:"refresh_token" binding:"required"`
    }
    
    if err := c.ShouldBindJSON(&req); err != nil {
        response.BadRequest(c, err.Error(), nil)
        return
    }
    
    tokens, err := h.jwtService.RefreshToken(req.RefreshToken)
    if err != nil {
        response.Unauthorized(c, "Invalid refresh token")
        return
    }
    
    response.OK(c, "Token refreshed", tokens)
}

func (h *AuthHandler) Logout(c *gin.Context) {
    // For stateless JWT, client just discards token
    // For stateful, we'd blacklist the token
    response.OK(c, "Logout successful", nil)
}

func (h *AuthHandler) Me(c *gin.Context) {
    userID := c.GetUint("user_id")
    
    user, err := h.userRepo.FindByID(c.Request.Context(), userID)
    if err != nil {
        response.NotFound(c, "User")
        return
    }
    
    response.OK(c, "Profile retrieved", user)
}
```

---

## 4️⃣ MID LEVEL - Auth Middleware

### JWT Middleware

```go
// internal/middleware/auth.go
package middleware

import (
    "strings"
    
    "github.com/gin-gonic/gin"
    "github.com/username/myapp/internal/service"
    "github.com/username/myapp/pkg/response"
)

func AuthMiddleware(jwtService *service.JWTService) gin.HandlerFunc {
    return func(c *gin.Context) {
        authHeader := c.GetHeader("Authorization")
        
        if authHeader == "" {
            response.Unauthorized(c, "Authorization header required")
            c.Abort()
            return
        }
        
        // Bearer token format
        parts := strings.Split(authHeader, " ")
        if len(parts) != 2 || parts[0] != "Bearer" {
            response.Unauthorized(c, "Invalid authorization format")
            c.Abort()
            return
        }
        
        tokenString := parts[1]
        
        claims, err := jwtService.ValidateToken(tokenString)
        if err != nil {
            if err == service.ErrExpiredToken {
                response.Unauthorized(c, "Token has expired")
            } else {
                response.Unauthorized(c, "Invalid token")
            }
            c.Abort()
            return
        }
        
        // Set user info in context
        c.Set("user_id", claims.UserID)
        c.Set("email", claims.Email)
        c.Set("role", claims.Role)
        
        c.Next()
    }
}

// Optional auth - doesn't fail if no token
func OptionalAuthMiddleware(jwtService *service.JWTService) gin.HandlerFunc {
    return func(c *gin.Context) {
        authHeader := c.GetHeader("Authorization")
        
        if authHeader != "" {
            parts := strings.Split(authHeader, " ")
            if len(parts) == 2 && parts[0] == "Bearer" {
                claims, err := jwtService.ValidateToken(parts[1])
                if err == nil {
                    c.Set("user_id", claims.UserID)
                    c.Set("email", claims.Email)
                    c.Set("role", claims.Role)
                }
            }
        }
        
        c.Next()
    }
}
```

### Route Setup

```go
// internal/router/router.go
package router

import (
    "github.com/gin-gonic/gin"
    "github.com/username/myapp/internal/handler"
    "github.com/username/myapp/internal/middleware"
)

func SetupRouter(
    authHandler *handler.AuthHandler,
    userHandler *handler.UserHandler,
    jwtService *service.JWTService,
) *gin.Engine {
    r := gin.Default()
    
    api := r.Group("/api/v1")
    
    // Public routes
    auth := api.Group("/auth")
    {
        auth.POST("/register", authHandler.Register)
        auth.POST("/login", authHandler.Login)
        auth.POST("/refresh", authHandler.RefreshToken)
    }
    
    // Protected routes
    protected := api.Group("")
    protected.Use(middleware.AuthMiddleware(jwtService))
    {
        protected.GET("/auth/me", authHandler.Me)
        protected.POST("/auth/logout", authHandler.Logout)
        
        users := protected.Group("/users")
        {
            users.GET("", userHandler.List)
            users.GET("/:id", userHandler.Get)
            users.PUT("/:id", userHandler.Update)
            users.DELETE("/:id", userHandler.Delete)
        }
    }
    
    return r
}
```

---

## 5️⃣ SENIOR LEVEL - Role-Based Access Control (RBAC)

### Role Middleware

```go
// internal/middleware/role.go
package middleware

import (
    "github.com/gin-gonic/gin"
    "github.com/username/myapp/pkg/response"
)

// RequireRole checks if user has specific role
func RequireRole(roles ...string) gin.HandlerFunc {
    return func(c *gin.Context) {
        userRole := c.GetString("role")
        
        for _, role := range roles {
            if userRole == role {
                c.Next()
                return
            }
        }
        
        response.Forbidden(c, "Insufficient permissions")
        c.Abort()
    }
}

// RequireAdmin shortcut for admin role
func RequireAdmin() gin.HandlerFunc {
    return RequireRole("admin")
}

// RequireOwnerOrAdmin checks if user is owner or admin
func RequireOwnerOrAdmin(paramName string) gin.HandlerFunc {
    return func(c *gin.Context) {
        userID := c.GetUint("user_id")
        role := c.GetString("role")
        
        // Admin can access anything
        if role == "admin" {
            c.Next()
            return
        }
        
        // Check if user is owner
        resourceID := c.Param(paramName)
        if fmt.Sprintf("%d", userID) == resourceID {
            c.Next()
            return
        }
        
        response.Forbidden(c, "You can only access your own resources")
        c.Abort()
    }
}
```

### Usage

```go
func SetupRouter() *gin.Engine {
    r := gin.Default()
    
    protected := r.Group("/api/v1")
    protected.Use(middleware.AuthMiddleware(jwtService))
    
    // Admin only routes
    admin := protected.Group("/admin")
    admin.Use(middleware.RequireAdmin())
    {
        admin.GET("/users", userHandler.ListAll)
        admin.DELETE("/users/:id", userHandler.ForceDelete)
    }
    
    // Owner or admin routes
    protected.PUT("/users/:id", middleware.RequireOwnerOrAdmin("id"), userHandler.Update)
    protected.DELETE("/users/:id", middleware.RequireOwnerOrAdmin("id"), userHandler.Delete)
    
    // Multiple roles
    protected.GET("/reports", middleware.RequireRole("admin", "manager"), reportHandler.List)
    
    return r
}
```

---

## 6️⃣ SENIOR LEVEL - Permission-Based Access Control

### Permission Model

```go
// internal/models/permission.go
package models

import "gorm.io/gorm"

type Role struct {
    gorm.Model
    Name        string       `gorm:"uniqueIndex" json:"name"`
    Permissions []Permission `gorm:"many2many:role_permissions;" json:"permissions"`
}

type Permission struct {
    gorm.Model
    Name        string `gorm:"uniqueIndex" json:"name"` // e.g., "users:read", "users:write"
    Description string `json:"description"`
}

type User struct {
    gorm.Model
    Name     string `json:"name"`
    Email    string `json:"email"`
    Password string `json:"-"`
    RoleID   uint   `json:"role_id"`
    Role     Role   `json:"role"`
}
```

### Permission Service

```go
// internal/service/permission.go
package service

import (
    "context"
    "strings"
    
    "github.com/username/myapp/internal/repository"
)

type PermissionService struct {
    roleRepo repository.RoleRepository
    cache    map[uint][]string // roleID -> permissions
}

func NewPermissionService(roleRepo repository.RoleRepository) *PermissionService {
    return &PermissionService{
        roleRepo: roleRepo,
        cache:    make(map[uint][]string),
    }
}

func (s *PermissionService) HasPermission(ctx context.Context, roleID uint, permission string) bool {
    permissions, err := s.GetPermissions(ctx, roleID)
    if err != nil {
        return false
    }
    
    for _, p := range permissions {
        // Exact match
        if p == permission {
            return true
        }
        
        // Wildcard match (e.g., "users:*" matches "users:read")
        if strings.HasSuffix(p, ":*") {
            prefix := strings.TrimSuffix(p, "*")
            if strings.HasPrefix(permission, prefix) {
                return true
            }
        }
    }
    
    return false
}

func (s *PermissionService) GetPermissions(ctx context.Context, roleID uint) ([]string, error) {
    // Check cache
    if perms, ok := s.cache[roleID]; ok {
        return perms, nil
    }
    
    // Load from DB
    role, err := s.roleRepo.FindByIDWithPermissions(ctx, roleID)
    if err != nil {
        return nil, err
    }
    
    permissions := make([]string, len(role.Permissions))
    for i, p := range role.Permissions {
        permissions[i] = p.Name
    }
    
    // Cache
    s.cache[roleID] = permissions
    
    return permissions, nil
}
```

### Permission Middleware

```go
// internal/middleware/permission.go
package middleware

import (
    "github.com/gin-gonic/gin"
    "github.com/username/myapp/internal/service"
    "github.com/username/myapp/pkg/response"
)

func RequirePermission(permSvc *service.PermissionService, permission string) gin.HandlerFunc {
    return func(c *gin.Context) {
        roleID := c.GetUint("role_id")
        
        if !permSvc.HasPermission(c.Request.Context(), roleID, permission) {
            response.Forbidden(c, "Missing permission: "+permission)
            c.Abort()
            return
        }
        
        c.Next()
    }
}
```

### Usage

```go
func SetupRouter(permSvc *service.PermissionService) *gin.Engine {
    r := gin.Default()
    
    users := r.Group("/users")
    users.Use(middleware.AuthMiddleware(jwtService))
    {
        users.GET("", middleware.RequirePermission(permSvc, "users:read"), userHandler.List)
        users.POST("", middleware.RequirePermission(permSvc, "users:create"), userHandler.Create)
        users.PUT("/:id", middleware.RequirePermission(permSvc, "users:update"), userHandler.Update)
        users.DELETE("/:id", middleware.RequirePermission(permSvc, "users:delete"), userHandler.Delete)
    }
    
    return r
}
```

---

## 7️⃣ EXPERT LEVEL - Token Blacklisting

### Redis Token Blacklist

```go
// internal/service/token_blacklist.go
package service

import (
    "context"
    "time"
    
    "github.com/redis/go-redis/v9"
)

type TokenBlacklist struct {
    redis *redis.Client
}

func NewTokenBlacklist(redis *redis.Client) *TokenBlacklist {
    return &TokenBlacklist{redis: redis}
}

func (b *TokenBlacklist) Add(ctx context.Context, token string, expiry time.Duration) error {
    return b.redis.Set(ctx, "blacklist:"+token, "1", expiry).Err()
}

func (b *TokenBlacklist) IsBlacklisted(ctx context.Context, token string) bool {
    result, err := b.redis.Get(ctx, "blacklist:"+token).Result()
    return err == nil && result == "1"
}

// Blacklist all tokens for a user
func (b *TokenBlacklist) BlacklistUser(ctx context.Context, userID uint, expiry time.Duration) error {
    key := fmt.Sprintf("user_blacklist:%d", userID)
    return b.redis.Set(ctx, key, time.Now().Unix(), expiry).Err()
}

func (b *TokenBlacklist) IsUserBlacklisted(ctx context.Context, userID uint, issuedAt time.Time) bool {
    key := fmt.Sprintf("user_blacklist:%d", userID)
    result, err := b.redis.Get(ctx, key).Result()
    if err != nil {
        return false
    }
    
    blacklistedAt, _ := strconv.ParseInt(result, 10, 64)
    return issuedAt.Unix() < blacklistedAt
}
```

### Enhanced Auth Middleware

```go
func AuthMiddleware(jwtService *service.JWTService, blacklist *service.TokenBlacklist) gin.HandlerFunc {
    return func(c *gin.Context) {
        // ... parse token ...
        
        claims, err := jwtService.ValidateToken(tokenString)
        if err != nil {
            response.Unauthorized(c, "Invalid token")
            c.Abort()
            return
        }
        
        // Check token blacklist
        if blacklist.IsBlacklisted(c.Request.Context(), tokenString) {
            response.Unauthorized(c, "Token has been revoked")
            c.Abort()
            return
        }
        
        // Check user blacklist (for "logout everywhere")
        if blacklist.IsUserBlacklisted(c.Request.Context(), claims.UserID, claims.IssuedAt.Time) {
            response.Unauthorized(c, "Session has been invalidated")
            c.Abort()
            return
        }
        
        c.Set("user_id", claims.UserID)
        c.Next()
    }
}
```

### Logout Everywhere

```go
func (h *AuthHandler) LogoutEverywhere(c *gin.Context) {
    userID := c.GetUint("user_id")
    
    // Blacklist all existing tokens
    h.blacklist.BlacklistUser(
        c.Request.Context(),
        userID,
        7*24*time.Hour, // Match refresh token expiry
    )
    
    response.OK(c, "Logged out from all devices", nil)
}
```

---

## 📊 Auth Comparison

| Method | Pros | Cons |
|--------|------|------|
| **Session** | Server control, easy revocation | Scalability issues |
| **JWT** | Stateless, scalable | Can't revoke easily |
| **JWT + Blacklist** | Best of both | Redis dependency |
| **OAuth2** | Standard, third-party | Complex |

### JWT vs Session

| Aspect | JWT | Session |
|--------|-----|---------|
| Storage | Client | Server |
| Scalability | Excellent | Needs shared store |
| Revocation | Hard (needs blacklist) | Easy |
| Size | Larger | Small cookie |
| Use Case | APIs, Mobile | Web apps |

---

## 💡 Summary

| Level | Focus |
|-------|-------|
| **Junior** | Password hashing, bcrypt |
| **Mid** | JWT generation, validation |
| **Mid-Senior** | Auth middleware, handlers |
| **Senior** | RBAC, permissions |
| **Expert** | Token blacklisting, OAuth2 |

**Best Practices:**
- ✅ Use bcrypt for passwords (cost 10-14)
- ✅ Use short-lived access tokens (15-30 min)
- ✅ Use refresh tokens for renewal
- ✅ Store sensitive data server-side
- ✅ Implement rate limiting on auth endpoints
- ❌ Don't store passwords in plain text
- ❌ Don't expose internal errors
- ❌ Don't use weak JWT secrets
