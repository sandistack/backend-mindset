# 🛡️ SECURITY - Security Best Practices di Go (Junior → Senior)

Dokumentasi lengkap tentang security best practices di Go.

---

## 🎯 Security Principles

```
CIA Triad:
- Confidentiality: Data hanya bisa diakses authorized users
- Integrity: Data tidak bisa dimodifikasi unauthorized
- Availability: System selalu available

OWASP Top 10:
1. Injection
2. Broken Authentication
3. Sensitive Data Exposure
4. XML External Entities (XXE)
5. Broken Access Control
6. Security Misconfiguration
7. Cross-Site Scripting (XSS)
8. Insecure Deserialization
9. Using Components with Known Vulnerabilities
10. Insufficient Logging & Monitoring
```

---

## 1️⃣ JUNIOR LEVEL - Input Validation

### Basic Validation

```go
package main

import (
    "net/http"
    "regexp"
    "strings"
    
    "github.com/gin-gonic/gin"
)

type UserInput struct {
    Name    string `json:"name" binding:"required,min=2,max=100"`
    Email   string `json:"email" binding:"required,email"`
    Age     int    `json:"age" binding:"required,gte=0,lte=150"`
    Website string `json:"website" binding:"omitempty,url"`
}

// Custom sanitization
func sanitizeString(input string) string {
    // Remove leading/trailing whitespace
    input = strings.TrimSpace(input)
    
    // Remove null bytes
    input = strings.ReplaceAll(input, "\x00", "")
    
    return input
}

// Validate username (alphanumeric and underscore only)
func isValidUsername(username string) bool {
    matched, _ := regexp.MatchString(`^[a-zA-Z0-9_]{3,20}$`, username)
    return matched
}

// Validate phone number
func isValidPhone(phone string) bool {
    matched, _ := regexp.MatchString(`^\+?[0-9]{10,15}$`, phone)
    return matched
}

func createUser(c *gin.Context) {
    var input UserInput
    if err := c.ShouldBindJSON(&input); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }
    
    // Additional sanitization
    input.Name = sanitizeString(input.Name)
    input.Email = strings.ToLower(sanitizeString(input.Email))
    
    // ... process
}
```

### SQL Injection Prevention

```go
package main

import (
    "gorm.io/gorm"
)

// ❌ VULNERABLE to SQL injection
func unsafeQuery(db *gorm.DB, name string) []User {
    var users []User
    db.Raw("SELECT * FROM users WHERE name = '" + name + "'").Scan(&users)
    return users
    // Input: "'; DROP TABLE users; --"
    // Query: SELECT * FROM users WHERE name = ''; DROP TABLE users; --'
}

// ✅ SAFE - Parameterized query
func safeQuery(db *gorm.DB, name string) []User {
    var users []User
    db.Raw("SELECT * FROM users WHERE name = ?", name).Scan(&users)
    return users
}

// ✅ SAFE - GORM methods
func safeGormQuery(db *gorm.DB, name string) []User {
    var users []User
    db.Where("name = ?", name).Find(&users)
    return users
}

// ✅ SAFE - GORM struct (only non-zero values used)
func safeStructQuery(db *gorm.DB, name string) []User {
    var users []User
    db.Where(&User{Name: name}).Find(&users)
    return users
}
```

---

## 2️⃣ MID LEVEL - XSS Prevention

### HTML Escape

```go
package main

import (
    "html"
    "html/template"
    "net/http"
    
    "github.com/gin-gonic/gin"
    "github.com/microcosm-cc/bluemonday"
)

// Basic HTML escape
func escapeHTML(input string) string {
    return html.EscapeString(input)
    // <script>alert('xss')</script>
    // becomes: &lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;
}

// Using bluemonday for rich text sanitization
var strictPolicy = bluemonday.StrictPolicy()
var ugcPolicy = bluemonday.UGCPolicy() // Allows safe HTML

func sanitizeHTML(input string) string {
    return strictPolicy.Sanitize(input) // Removes ALL HTML
}

func sanitizeUGC(input string) string {
    return ugcPolicy.Sanitize(input) // Allows safe HTML like <b>, <i>
}

// Template auto-escaping
func renderTemplate(c *gin.Context) {
    data := gin.H{
        "userInput": "<script>alert('xss')</script>",
    }
    
    // Gin's HTML rendering auto-escapes by default
    c.HTML(http.StatusOK, "template.html", data)
}

// Content Security Policy header
func CSPMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        c.Header("Content-Security-Policy", 
            "default-src 'self'; "+
            "script-src 'self'; "+
            "style-src 'self' 'unsafe-inline'; "+
            "img-src 'self' data: https:; "+
            "font-src 'self'; "+
            "frame-ancestors 'none';")
        c.Next()
    }
}
```

---

## 3️⃣ MID LEVEL - CORS Configuration

### Proper CORS Setup

```go
package middleware

import (
    "net/http"
    "strings"
    
    "github.com/gin-gonic/gin"
)

type CORSConfig struct {
    AllowedOrigins   []string
    AllowedMethods   []string
    AllowedHeaders   []string
    ExposedHeaders   []string
    AllowCredentials bool
    MaxAge           int
}

func CORSMiddleware(config CORSConfig) gin.HandlerFunc {
    return func(c *gin.Context) {
        origin := c.GetHeader("Origin")
        
        // Check if origin is allowed
        allowed := false
        for _, allowedOrigin := range config.AllowedOrigins {
            if allowedOrigin == "*" || allowedOrigin == origin {
                allowed = true
                c.Header("Access-Control-Allow-Origin", origin)
                break
            }
        }
        
        if !allowed {
            if c.Request.Method == http.MethodOptions {
                c.AbortWithStatus(http.StatusForbidden)
                return
            }
            c.Next()
            return
        }
        
        // Set CORS headers
        c.Header("Access-Control-Allow-Methods", strings.Join(config.AllowedMethods, ", "))
        c.Header("Access-Control-Allow-Headers", strings.Join(config.AllowedHeaders, ", "))
        
        if len(config.ExposedHeaders) > 0 {
            c.Header("Access-Control-Expose-Headers", strings.Join(config.ExposedHeaders, ", "))
        }
        
        if config.AllowCredentials {
            c.Header("Access-Control-Allow-Credentials", "true")
        }
        
        if config.MaxAge > 0 {
            c.Header("Access-Control-Max-Age", fmt.Sprintf("%d", config.MaxAge))
        }
        
        // Handle preflight
        if c.Request.Method == http.MethodOptions {
            c.AbortWithStatus(http.StatusNoContent)
            return
        }
        
        c.Next()
    }
}

// Usage
func main() {
    r := gin.Default()
    
    r.Use(CORSMiddleware(CORSConfig{
        AllowedOrigins:   []string{"https://example.com", "https://app.example.com"},
        AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
        AllowedHeaders:   []string{"Authorization", "Content-Type"},
        ExposedHeaders:   []string{"X-Total-Count"},
        AllowCredentials: true,
        MaxAge:           86400,
    }))
    
    r.Run(":8080")
}
```

---

## 4️⃣ MID LEVEL - Rate Limiting

### Token Bucket Rate Limiter

```go
package middleware

import (
    "net/http"
    "sync"
    "time"
    
    "github.com/gin-gonic/gin"
)

type RateLimiter struct {
    visitors map[string]*Visitor
    mu       sync.RWMutex
    rate     int           // requests per duration
    duration time.Duration
}

type Visitor struct {
    tokens    int
    lastSeen  time.Time
}

func NewRateLimiter(rate int, duration time.Duration) *RateLimiter {
    rl := &RateLimiter{
        visitors: make(map[string]*Visitor),
        rate:     rate,
        duration: duration,
    }
    
    // Cleanup goroutine
    go rl.cleanup()
    
    return rl
}

func (rl *RateLimiter) cleanup() {
    for {
        time.Sleep(time.Minute)
        
        rl.mu.Lock()
        for ip, v := range rl.visitors {
            if time.Since(v.lastSeen) > 3*rl.duration {
                delete(rl.visitors, ip)
            }
        }
        rl.mu.Unlock()
    }
}

func (rl *RateLimiter) Allow(ip string) bool {
    rl.mu.Lock()
    defer rl.mu.Unlock()
    
    v, exists := rl.visitors[ip]
    if !exists {
        rl.visitors[ip] = &Visitor{
            tokens:   rl.rate - 1,
            lastSeen: time.Now(),
        }
        return true
    }
    
    // Refill tokens based on time passed
    elapsed := time.Since(v.lastSeen)
    refill := int(elapsed / rl.duration) * rl.rate
    v.tokens = min(v.tokens+refill, rl.rate)
    v.lastSeen = time.Now()
    
    if v.tokens > 0 {
        v.tokens--
        return true
    }
    
    return false
}

func RateLimitMiddleware(rl *RateLimiter) gin.HandlerFunc {
    return func(c *gin.Context) {
        ip := c.ClientIP()
        
        if !rl.Allow(ip) {
            c.JSON(http.StatusTooManyRequests, gin.H{
                "error": "Rate limit exceeded",
            })
            c.Abort()
            return
        }
        
        c.Next()
    }
}

// Usage
func main() {
    r := gin.Default()
    
    // 100 requests per minute
    limiter := NewRateLimiter(100, time.Minute)
    r.Use(RateLimitMiddleware(limiter))
    
    // Stricter limit for auth endpoints
    authLimiter := NewRateLimiter(5, time.Minute)
    r.POST("/login", RateLimitMiddleware(authLimiter), loginHandler)
    
    r.Run(":8080")
}
```

### Redis Rate Limiter

```go
package middleware

import (
    "context"
    "fmt"
    "time"
    
    "github.com/redis/go-redis/v9"
)

type RedisRateLimiter struct {
    client   *redis.Client
    rate     int
    duration time.Duration
}

func NewRedisRateLimiter(client *redis.Client, rate int, duration time.Duration) *RedisRateLimiter {
    return &RedisRateLimiter{
        client:   client,
        rate:     rate,
        duration: duration,
    }
}

func (rl *RedisRateLimiter) Allow(ctx context.Context, key string) (bool, error) {
    redisKey := fmt.Sprintf("ratelimit:%s", key)
    
    // Increment counter
    count, err := rl.client.Incr(ctx, redisKey).Result()
    if err != nil {
        return false, err
    }
    
    // Set expiry on first request
    if count == 1 {
        rl.client.Expire(ctx, redisKey, rl.duration)
    }
    
    return count <= int64(rl.rate), nil
}
```

---

## 5️⃣ SENIOR LEVEL - Security Headers

### Complete Security Headers

```go
package middleware

import "github.com/gin-gonic/gin"

func SecurityHeaders() gin.HandlerFunc {
    return func(c *gin.Context) {
        // Prevent clickjacking
        c.Header("X-Frame-Options", "DENY")
        
        // Prevent MIME type sniffing
        c.Header("X-Content-Type-Options", "nosniff")
        
        // Enable XSS protection
        c.Header("X-XSS-Protection", "1; mode=block")
        
        // Referrer policy
        c.Header("Referrer-Policy", "strict-origin-when-cross-origin")
        
        // Permissions policy (formerly Feature-Policy)
        c.Header("Permissions-Policy", 
            "geolocation=(), microphone=(), camera=()")
        
        // Content Security Policy
        c.Header("Content-Security-Policy", 
            "default-src 'self'; "+
            "script-src 'self'; "+
            "style-src 'self' 'unsafe-inline'; "+
            "img-src 'self' data: https:; "+
            "font-src 'self'; "+
            "connect-src 'self'; "+
            "frame-ancestors 'none'; "+
            "base-uri 'self'; "+
            "form-action 'self';")
        
        // Strict Transport Security (HTTPS only)
        c.Header("Strict-Transport-Security", 
            "max-age=31536000; includeSubDomains; preload")
        
        c.Next()
    }
}
```

---

## 6️⃣ SENIOR LEVEL - CSRF Protection

### CSRF Token Implementation

```go
package middleware

import (
    "crypto/rand"
    "encoding/base64"
    "net/http"
    "sync"
    "time"
    
    "github.com/gin-gonic/gin"
)

type CSRFProtection struct {
    tokens map[string]time.Time
    mu     sync.RWMutex
    expiry time.Duration
}

func NewCSRFProtection() *CSRFProtection {
    csrf := &CSRFProtection{
        tokens: make(map[string]time.Time),
        expiry: time.Hour,
    }
    
    go csrf.cleanup()
    
    return csrf
}

func (c *CSRFProtection) cleanup() {
    for {
        time.Sleep(time.Minute)
        
        c.mu.Lock()
        now := time.Now()
        for token, expiry := range c.tokens {
            if now.After(expiry) {
                delete(c.tokens, token)
            }
        }
        c.mu.Unlock()
    }
}

func (c *CSRFProtection) Generate() string {
    bytes := make([]byte, 32)
    rand.Read(bytes)
    token := base64.URLEncoding.EncodeToString(bytes)
    
    c.mu.Lock()
    c.tokens[token] = time.Now().Add(c.expiry)
    c.mu.Unlock()
    
    return token
}

func (c *CSRFProtection) Validate(token string) bool {
    c.mu.RLock()
    expiry, exists := c.tokens[token]
    c.mu.RUnlock()
    
    if !exists || time.Now().After(expiry) {
        return false
    }
    
    // One-time use
    c.mu.Lock()
    delete(c.tokens, token)
    c.mu.Unlock()
    
    return true
}

func CSRFMiddleware(csrf *CSRFProtection) gin.HandlerFunc {
    return func(c *gin.Context) {
        // Skip for GET, HEAD, OPTIONS
        if c.Request.Method == http.MethodGet ||
           c.Request.Method == http.MethodHead ||
           c.Request.Method == http.MethodOptions {
            // Generate and set token
            token := csrf.Generate()
            c.SetCookie("csrf_token", token, 3600, "/", "", true, true)
            c.Set("csrf_token", token)
            c.Next()
            return
        }
        
        // Validate token for state-changing methods
        cookieToken, _ := c.Cookie("csrf_token")
        headerToken := c.GetHeader("X-CSRF-Token")
        
        if headerToken == "" || cookieToken == "" || headerToken != cookieToken {
            c.JSON(http.StatusForbidden, gin.H{"error": "Invalid CSRF token"})
            c.Abort()
            return
        }
        
        if !csrf.Validate(headerToken) {
            c.JSON(http.StatusForbidden, gin.H{"error": "CSRF token expired"})
            c.Abort()
            return
        }
        
        c.Next()
    }
}
```

---

## 7️⃣ SENIOR LEVEL - Secrets Management

### Environment Variables

```go
package config

import (
    "log"
    "os"
    
    "github.com/joho/godotenv"
)

type Config struct {
    DatabaseURL  string
    JWTSecret    string
    APIKey       string
    RedisURL     string
    Environment  string
}

func Load() *Config {
    // Load .env in development
    if os.Getenv("ENVIRONMENT") != "production" {
        if err := godotenv.Load(); err != nil {
            log.Println("No .env file found")
        }
    }
    
    config := &Config{
        DatabaseURL:  getEnvRequired("DATABASE_URL"),
        JWTSecret:    getEnvRequired("JWT_SECRET"),
        APIKey:       getEnvRequired("API_KEY"),
        RedisURL:     getEnv("REDIS_URL", "redis://localhost:6379"),
        Environment:  getEnv("ENVIRONMENT", "development"),
    }
    
    // Validate JWT secret length
    if len(config.JWTSecret) < 32 {
        log.Fatal("JWT_SECRET must be at least 32 characters")
    }
    
    return config
}

func getEnv(key, defaultValue string) string {
    if value := os.Getenv(key); value != "" {
        return value
    }
    return defaultValue
}

func getEnvRequired(key string) string {
    value := os.Getenv(key)
    if value == "" {
        log.Fatalf("Required environment variable %s is not set", key)
    }
    return value
}
```

### .env Example

```bash
# .env.example (commit this)
DATABASE_URL=postgres://user:password@localhost:5432/dbname?sslmode=disable
JWT_SECRET=your-very-long-secret-key-at-least-32-chars
API_KEY=your-api-key
REDIS_URL=redis://localhost:6379
ENVIRONMENT=development

# .env (DO NOT commit this)
DATABASE_URL=postgres://prod_user:super_secret@prod-db:5432/proddb
JWT_SECRET=production-super-secret-key-very-long
```

---

## 8️⃣ EXPERT LEVEL - Request Signing

### HMAC Request Signing

```go
package middleware

import (
    "bytes"
    "crypto/hmac"
    "crypto/sha256"
    "encoding/hex"
    "io"
    "net/http"
    "strconv"
    "time"
    
    "github.com/gin-gonic/gin"
)

type SignatureValidator struct {
    secretKey []byte
    maxAge    time.Duration
}

func NewSignatureValidator(secretKey string, maxAge time.Duration) *SignatureValidator {
    return &SignatureValidator{
        secretKey: []byte(secretKey),
        maxAge:    maxAge,
    }
}

func (v *SignatureValidator) Sign(body []byte, timestamp int64) string {
    data := append(body, []byte(strconv.FormatInt(timestamp, 10))...)
    h := hmac.New(sha256.New, v.secretKey)
    h.Write(data)
    return hex.EncodeToString(h.Sum(nil))
}

func (v *SignatureValidator) Verify(body []byte, timestamp int64, signature string) bool {
    // Check timestamp freshness
    requestTime := time.Unix(timestamp, 0)
    if time.Since(requestTime) > v.maxAge {
        return false
    }
    
    expectedSignature := v.Sign(body, timestamp)
    return hmac.Equal([]byte(signature), []byte(expectedSignature))
}

func SignatureMiddleware(validator *SignatureValidator) gin.HandlerFunc {
    return func(c *gin.Context) {
        signature := c.GetHeader("X-Signature")
        timestampStr := c.GetHeader("X-Timestamp")
        
        if signature == "" || timestampStr == "" {
            c.JSON(http.StatusUnauthorized, gin.H{"error": "Missing signature"})
            c.Abort()
            return
        }
        
        timestamp, err := strconv.ParseInt(timestampStr, 10, 64)
        if err != nil {
            c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid timestamp"})
            c.Abort()
            return
        }
        
        // Read and restore body
        body, _ := io.ReadAll(c.Request.Body)
        c.Request.Body = io.NopCloser(bytes.NewBuffer(body))
        
        if !validator.Verify(body, timestamp, signature) {
            c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid signature"})
            c.Abort()
            return
        }
        
        c.Next()
    }
}
```

---

## 9️⃣ EXPERT LEVEL - Audit Logging

### Security Audit Logger

```go
package audit

import (
    "encoding/json"
    "time"
    
    "github.com/gin-gonic/gin"
    "go.uber.org/zap"
)

type AuditEvent struct {
    Timestamp  time.Time         `json:"timestamp"`
    Action     string            `json:"action"`
    UserID     uint              `json:"user_id,omitempty"`
    IP         string            `json:"ip"`
    UserAgent  string            `json:"user_agent"`
    Resource   string            `json:"resource"`
    Method     string            `json:"method"`
    StatusCode int               `json:"status_code"`
    Duration   time.Duration     `json:"duration_ms"`
    Details    map[string]string `json:"details,omitempty"`
}

type AuditLogger struct {
    logger *zap.Logger
}

func NewAuditLogger(logger *zap.Logger) *AuditLogger {
    return &AuditLogger{logger: logger}
}

func (a *AuditLogger) Log(event AuditEvent) {
    data, _ := json.Marshal(event)
    a.logger.Info("AUDIT", zap.String("event", string(data)))
}

func AuditMiddleware(auditLogger *AuditLogger) gin.HandlerFunc {
    return func(c *gin.Context) {
        start := time.Now()
        
        c.Next()
        
        // Log after request completes
        event := AuditEvent{
            Timestamp:  start,
            Action:     determineAction(c),
            UserID:     c.GetUint("user_id"),
            IP:         c.ClientIP(),
            UserAgent:  c.GetHeader("User-Agent"),
            Resource:   c.FullPath(),
            Method:     c.Request.Method,
            StatusCode: c.Writer.Status(),
            Duration:   time.Since(start),
        }
        
        // Add sensitive action details
        if isSensitiveAction(c) {
            event.Details = extractAuditDetails(c)
        }
        
        auditLogger.Log(event)
    }
}

func determineAction(c *gin.Context) string {
    switch c.Request.Method {
    case "POST":
        return "CREATE"
    case "PUT", "PATCH":
        return "UPDATE"
    case "DELETE":
        return "DELETE"
    default:
        return "READ"
    }
}

func isSensitiveAction(c *gin.Context) bool {
    sensitivePaths := []string{
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/users",
        "/api/v1/admin",
    }
    
    for _, path := range sensitivePaths {
        if c.FullPath() == path {
            return true
        }
    }
    
    return false
}
```

---

## 📊 Security Checklist

| Category | Check |
|----------|-------|
| **Input** | ✅ Validate all input |
| **Input** | ✅ Sanitize HTML |
| **Input** | ✅ Use parameterized queries |
| **Auth** | ✅ Use bcrypt for passwords |
| **Auth** | ✅ Short-lived tokens |
| **Auth** | ✅ Rate limit auth endpoints |
| **Headers** | ✅ Set security headers |
| **Headers** | ✅ Proper CORS config |
| **Secrets** | ✅ Environment variables |
| **Secrets** | ✅ Don't commit secrets |
| **Logging** | ✅ Audit sensitive actions |
| **Logging** | ✅ Don't log sensitive data |

---

## 💡 Summary

| Level | Focus |
|-------|-------|
| **Junior** | Input validation, SQL injection |
| **Mid** | XSS, CORS, basic rate limiting |
| **Mid-Senior** | Security headers, CSRF |
| **Senior** | Secrets management, Redis rate limiting |
| **Expert** | Request signing, audit logging |

**Best Practices:**
- ✅ Validate and sanitize ALL input
- ✅ Use parameterized queries always
- ✅ Set proper security headers
- ✅ Implement rate limiting
- ✅ Log security events
- ✅ Keep dependencies updated
- ❌ Don't trust client input
- ❌ Don't expose error details
- ❌ Don't commit secrets to git
