# 🚦 Rate Limiting di Go

## Kenapa Penting?

Rate limiting untuk:
- ✅ Prevent abuse
- ✅ Protect resources
- ✅ Fair usage
- ✅ DDoS mitigation

---

## 📚 Daftar Isi

1. [Token Bucket Algorithm](#1️⃣-token-bucket-algorithm)
2. [Sliding Window](#2️⃣-sliding-window)
3. [Redis-Based Rate Limiting](#3️⃣-redis-based-rate-limiting)
4. [Middleware Implementation](#4️⃣-middleware-implementation)
5. [Advanced Patterns](#5️⃣-advanced-patterns)
6. [Production Setup](#6️⃣-production-setup)

---

## 1️⃣ Token Bucket Algorithm

### Simple Token Bucket

```go
// internal/ratelimit/token_bucket.go
package ratelimit

import (
    "sync"
    "time"
)

type TokenBucket struct {
    capacity     int           // Max tokens
    tokens       int           // Current tokens
    refillRate   time.Duration // How often to add token
    lastRefill   time.Time
    mu           sync.Mutex
}

func NewTokenBucket(capacity int, refillRate time.Duration) *TokenBucket {
    return &TokenBucket{
        capacity:   capacity,
        tokens:     capacity,
        refillRate: refillRate,
        lastRefill: time.Now(),
    }
}

func (tb *TokenBucket) Allow() bool {
    tb.mu.Lock()
    defer tb.mu.Unlock()
    
    tb.refill()
    
    if tb.tokens > 0 {
        tb.tokens--
        return true
    }
    
    return false
}

func (tb *TokenBucket) refill() {
    now := time.Now()
    elapsed := now.Sub(tb.lastRefill)
    tokensToAdd := int(elapsed / tb.refillRate)
    
    if tokensToAdd > 0 {
        tb.tokens = min(tb.capacity, tb.tokens+tokensToAdd)
        tb.lastRefill = now
    }
}

func min(a, b int) int {
    if a < b {
        return a
    }
    return b
}
```

### Using golang.org/x/time/rate

```bash
go get golang.org/x/time/rate
```

```go
// internal/ratelimit/standard.go
package ratelimit

import (
    "context"
    "time"
    
    "golang.org/x/time/rate"
)

type RateLimiter struct {
    limiter *rate.Limiter
}

func NewRateLimiter(rps int, burst int) *RateLimiter {
    // rps: requests per second
    // burst: max burst size
    return &RateLimiter{
        limiter: rate.NewLimiter(rate.Limit(rps), burst),
    }
}

// Allow checks if request is allowed
func (rl *RateLimiter) Allow() bool {
    return rl.limiter.Allow()
}

// Wait blocks until request is allowed
func (rl *RateLimiter) Wait(ctx context.Context) error {
    return rl.limiter.Wait(ctx)
}

// Reserve returns a Reservation for a future time
func (rl *RateLimiter) Reserve() *rate.Reservation {
    return rl.limiter.Reserve()
}
```

### Per-User Rate Limiting

```go
// internal/ratelimit/per_user.go
package ratelimit

import (
    "sync"
    "time"
    
    "golang.org/x/time/rate"
)

type UserRateLimiter struct {
    limiters map[string]*rate.Limiter
    mu       sync.RWMutex
    rps      int
    burst    int
}

func NewUserRateLimiter(rps, burst int) *UserRateLimiter {
    rl := &UserRateLimiter{
        limiters: make(map[string]*rate.Limiter),
        rps:      rps,
        burst:    burst,
    }
    
    // Cleanup old limiters periodically
    go rl.cleanup()
    
    return rl
}

func (rl *UserRateLimiter) GetLimiter(userID string) *rate.Limiter {
    rl.mu.Lock()
    defer rl.mu.Unlock()
    
    limiter, exists := rl.limiters[userID]
    if !exists {
        limiter = rate.NewLimiter(rate.Limit(rl.rps), rl.burst)
        rl.limiters[userID] = limiter
    }
    
    return limiter
}

func (rl *UserRateLimiter) Allow(userID string) bool {
    return rl.GetLimiter(userID).Allow()
}

func (rl *UserRateLimiter) cleanup() {
    ticker := time.NewTicker(time.Hour)
    defer ticker.Stop()
    
    for range ticker.C {
        rl.mu.Lock()
        // Remove inactive limiters
        for id, limiter := range rl.limiters {
            if limiter.Tokens() == float64(rl.burst) {
                delete(rl.limiters, id)
            }
        }
        rl.mu.Unlock()
    }
}
```

---

## 2️⃣ Sliding Window

### Fixed Window Counter

```go
// internal/ratelimit/fixed_window.go
package ratelimit

import (
    "sync"
    "time"
)

type FixedWindow struct {
    limit      int
    window     time.Duration
    counters   map[string]*WindowCounter
    mu         sync.RWMutex
}

type WindowCounter struct {
    count      int
    windowStart time.Time
}

func NewFixedWindow(limit int, window time.Duration) *FixedWindow {
    return &FixedWindow{
        limit:    limit,
        window:   window,
        counters: make(map[string]*WindowCounter),
    }
}

func (fw *FixedWindow) Allow(key string) bool {
    fw.mu.Lock()
    defer fw.mu.Unlock()
    
    now := time.Now()
    counter, exists := fw.counters[key]
    
    if !exists || now.Sub(counter.windowStart) > fw.window {
        // New window
        fw.counters[key] = &WindowCounter{
            count:      1,
            windowStart: now,
        }
        return true
    }
    
    if counter.count < fw.limit {
        counter.count++
        return true
    }
    
    return false
}
```

### Sliding Window Log

```go
// internal/ratelimit/sliding_window_log.go
package ratelimit

import (
    "sync"
    "time"
)

type SlidingWindowLog struct {
    limit      int
    window     time.Duration
    logs       map[string][]time.Time
    mu         sync.RWMutex
}

func NewSlidingWindowLog(limit int, window time.Duration) *SlidingWindowLog {
    return &SlidingWindowLog{
        limit:  limit,
        window: window,
        logs:   make(map[string][]time.Time),
    }
}

func (swl *SlidingWindowLog) Allow(key string) bool {
    swl.mu.Lock()
    defer swl.mu.Unlock()
    
    now := time.Now()
    windowStart := now.Add(-swl.window)
    
    // Get or create log for this key
    log := swl.logs[key]
    
    // Remove old entries
    validLog := []time.Time{}
    for _, timestamp := range log {
        if timestamp.After(windowStart) {
            validLog = append(validLog, timestamp)
        }
    }
    
    // Check limit
    if len(validLog) < swl.limit {
        validLog = append(validLog, now)
        swl.logs[key] = validLog
        return true
    }
    
    swl.logs[key] = validLog
    return false
}
```

### Sliding Window Counter

```go
// internal/ratelimit/sliding_window_counter.go
package ratelimit

import (
    "sync"
    "time"
)

type SlidingWindowCounter struct {
    limit      int
    window     time.Duration
    counters   map[string]*WindowData
    mu         sync.RWMutex
}

type WindowData struct {
    currentCount  int
    previousCount int
    currentStart  time.Time
}

func NewSlidingWindowCounter(limit int, window time.Duration) *SlidingWindowCounter {
    return &SlidingWindowCounter{
        limit:    limit,
        window:   window,
        counters: make(map[string]*WindowData),
    }
}

func (swc *SlidingWindowCounter) Allow(key string) bool {
    swc.mu.Lock()
    defer swc.mu.Unlock()
    
    now := time.Now()
    data, exists := swc.counters[key]
    
    if !exists {
        swc.counters[key] = &WindowData{
            currentCount:  1,
            previousCount: 0,
            currentStart:  now,
        }
        return true
    }
    
    // Check if we're in a new window
    elapsed := now.Sub(data.currentStart)
    if elapsed > swc.window {
        data.previousCount = data.currentCount
        data.currentCount = 1
        data.currentStart = now
        return true
    }
    
    // Calculate weighted count
    progress := float64(elapsed) / float64(swc.window)
    prevWeight := 1.0 - progress
    weightedCount := int(float64(data.previousCount)*prevWeight) + data.currentCount
    
    if weightedCount < swc.limit {
        data.currentCount++
        return true
    }
    
    return false
}
```

---

## 3️⃣ Redis-Based Rate Limiting

### Redis Token Bucket

```go
// internal/ratelimit/redis.go
package ratelimit

import (
    "context"
    "fmt"
    "time"
    
    "github.com/go-redis/redis/v8"
)

type RedisRateLimiter struct {
    client *redis.Client
    limit  int
    window time.Duration
}

func NewRedisRateLimiter(client *redis.Client, limit int, window time.Duration) *RedisRateLimiter {
    return &RedisRateLimiter{
        client: client,
        limit:  limit,
        window: window,
    }
}

func (rl *RedisRateLimiter) Allow(ctx context.Context, key string) (bool, error) {
    redisKey := fmt.Sprintf("rate_limit:%s", key)
    
    // Increment counter
    count, err := rl.client.Incr(ctx, redisKey).Result()
    if err != nil {
        return false, err
    }
    
    // Set expiration on first request
    if count == 1 {
        rl.client.Expire(ctx, redisKey, rl.window)
    }
    
    return count <= int64(rl.limit), nil
}

func (rl *RedisRateLimiter) Remaining(ctx context.Context, key string) (int, error) {
    redisKey := fmt.Sprintf("rate_limit:%s", key)
    
    count, err := rl.client.Get(ctx, redisKey).Int()
    if err == redis.Nil {
        return rl.limit, nil
    }
    if err != nil {
        return 0, err
    }
    
    remaining := rl.limit - count
    if remaining < 0 {
        remaining = 0
    }
    
    return remaining, nil
}
```

### Redis Sliding Window (Lua Script)

```go
// internal/ratelimit/redis_sliding.go
package ratelimit

import (
    "context"
    "time"
    
    "github.com/go-redis/redis/v8"
)

var slidingWindowScript = redis.NewScript(`
    local key = KEYS[1]
    local now = tonumber(ARGV[1])
    local window = tonumber(ARGV[2])
    local limit = tonumber(ARGV[3])
    
    local clearBefore = now - window
    redis.call('ZREMRANGEBYSCORE', key, 0, clearBefore)
    
    local amount = redis.call('ZCARD', key)
    if amount < limit then
        redis.call('ZADD', key, now, now)
        redis.call('EXPIRE', key, window)
        return 1
    else
        return 0
    end
`)

type RedisSlidingWindow struct {
    client *redis.Client
    limit  int
    window time.Duration
}

func NewRedisSlidingWindow(client *redis.Client, limit int, window time.Duration) *RedisSlidingWindow {
    return &RedisSlidingWindow{
        client: client,
        limit:  limit,
        window: window,
    }
}

func (rsw *RedisSlidingWindow) Allow(ctx context.Context, key string) (bool, error) {
    now := time.Now().UnixMilli()
    window := rsw.window.Milliseconds()
    
    result, err := slidingWindowScript.Run(
        ctx,
        rsw.client,
        []string{key},
        now,
        window,
        rsw.limit,
    ).Int()
    
    if err != nil {
        return false, err
    }
    
    return result == 1, nil
}
```

---

## 4️⃣ Middleware Implementation

### Chi Middleware

```go
// internal/middleware/rate_limit.go
package middleware

import (
    "net/http"
    
    "myapp/internal/ratelimit"
)

func RateLimit(limiter *ratelimit.UserRateLimiter) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            // Get user ID from context
            userID := getUserID(r.Context())
            if userID == "" {
                userID = r.RemoteAddr // Use IP as fallback
            }
            
            if !limiter.Allow(userID) {
                w.Header().Set("X-RateLimit-Limit", fmt.Sprintf("%d", limiter.burst))
                w.Header().Set("X-RateLimit-Remaining", "0")
                w.Header().Set("Retry-After", "60")
                
                http.Error(w, "Rate limit exceeded", http.StatusTooManyRequests)
                return
            }
            
            next.ServeHTTP(w, r)
        })
    }
}
```

### Gin Middleware

```go
// internal/middleware/gin_rate_limit.go
package middleware

import (
    "net/http"
    
    "github.com/gin-gonic/gin"
    "myapp/internal/ratelimit"
)

func GinRateLimit(limiter *ratelimit.UserRateLimiter) gin.HandlerFunc {
    return func(c *gin.Context) {
        userID := getUserIDFromContext(c)
        if userID == "" {
            userID = c.ClientIP()
        }
        
        if !limiter.Allow(userID) {
            c.Header("X-RateLimit-Limit", fmt.Sprintf("%d", limiter.burst))
            c.Header("X-RateLimit-Remaining", "0")
            c.Header("Retry-After", "60")
            
            c.JSON(http.StatusTooManyRequests, gin.H{
                "error": "Rate limit exceeded",
            })
            c.Abort()
            return
        }
        
        c.Next()
    }
}
```

### With Rate Limit Headers

```go
// internal/middleware/rate_limit_headers.go
package middleware

import (
    "fmt"
    "net/http"
    "time"
    
    "golang.org/x/time/rate"
)

func RateLimitWithHeaders(limiter *rate.Limiter, limit int) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            reservation := limiter.Reserve()
            
            if !reservation.OK() {
                w.Header().Set("X-RateLimit-Limit", fmt.Sprintf("%d", limit))
                w.Header().Set("X-RateLimit-Remaining", "0")
                http.Error(w, "Rate limit exceeded", http.StatusTooManyRequests)
                return
            }
            
            delay := reservation.Delay()
            if delay > 0 {
                reservation.Cancel()
                w.Header().Set("X-RateLimit-Limit", fmt.Sprintf("%d", limit))
                w.Header().Set("X-RateLimit-Remaining", "0")
                w.Header().Set("Retry-After", fmt.Sprintf("%d", int(delay.Seconds())+1))
                http.Error(w, "Rate limit exceeded", http.StatusTooManyRequests)
                return
            }
            
            // Add rate limit headers
            w.Header().Set("X-RateLimit-Limit", fmt.Sprintf("%d", limit))
            remaining := int(limiter.Tokens())
            w.Header().Set("X-RateLimit-Remaining", fmt.Sprintf("%d", remaining))
            
            next.ServeHTTP(w, r)
        })
    }
}
```

---

## 5️⃣ Advanced Patterns

### Tiered Rate Limiting

```go
// internal/ratelimit/tiered.go
package ratelimit

import (
    "golang.org/x/time/rate"
)

type UserTier string

const (
    TierFree       UserTier = "free"
    TierBasic      UserTier = "basic"
    TierPremium    UserTier = "premium"
    TierEnterprise UserTier = "enterprise"
)

type TieredRateLimiter struct {
    limiters map[UserTier]*rate.Limiter
}

func NewTieredRateLimiter() *TieredRateLimiter {
    return &TieredRateLimiter{
        limiters: map[UserTier]*rate.Limiter{
            TierFree:       rate.NewLimiter(10, 20),     // 10 req/s, burst 20
            TierBasic:      rate.NewLimiter(50, 100),    // 50 req/s, burst 100
            TierPremium:    rate.NewLimiter(200, 400),   // 200 req/s, burst 400
            TierEnterprise: rate.NewLimiter(1000, 2000), // 1000 req/s, burst 2000
        },
    }
}

func (trl *TieredRateLimiter) Allow(tier UserTier) bool {
    limiter, exists := trl.limiters[tier]
    if !exists {
        limiter = trl.limiters[TierFree]
    }
    return limiter.Allow()
}
```

### Adaptive Rate Limiting

```go
// internal/ratelimit/adaptive.go
package ratelimit

import (
    "sync"
    "time"
    
    "golang.org/x/time/rate"
)

type AdaptiveRateLimiter struct {
    baseLimiter    *rate.Limiter
    errorCount     int
    successCount   int
    mu             sync.Mutex
    adjustInterval time.Duration
}

func NewAdaptiveRateLimiter(baseRate rate.Limit, burst int) *AdaptiveRateLimiter {
    arl := &AdaptiveRateLimiter{
        baseLimiter:    rate.NewLimiter(baseRate, burst),
        adjustInterval: time.Minute,
    }
    
    go arl.adjustRate()
    
    return arl
}

func (arl *AdaptiveRateLimiter) Allow() bool {
    return arl.baseLimiter.Allow()
}

func (arl *AdaptiveRateLimiter) RecordError() {
    arl.mu.Lock()
    defer arl.mu.Unlock()
    arl.errorCount++
}

func (arl *AdaptiveRateLimiter) RecordSuccess() {
    arl.mu.Lock()
    defer arl.mu.Unlock()
    arl.successCount++
}

func (arl *AdaptiveRateLimiter) adjustRate() {
    ticker := time.NewTicker(arl.adjustInterval)
    defer ticker.Stop()
    
    for range ticker.C {
        arl.mu.Lock()
        
        errorRate := float64(arl.errorCount) / float64(arl.errorCount+arl.successCount)
        
        currentLimit := arl.baseLimiter.Limit()
        
        if errorRate > 0.1 { // More than 10% errors
            // Decrease rate by 20%
            newLimit := currentLimit * 0.8
            arl.baseLimiter.SetLimit(newLimit)
        } else if errorRate < 0.01 { // Less than 1% errors
            // Increase rate by 10%
            newLimit := currentLimit * 1.1
            arl.baseLimiter.SetLimit(newLimit)
        }
        
        // Reset counters
        arl.errorCount = 0
        arl.successCount = 0
        
        arl.mu.Unlock()
    }
}
```

---

## 6️⃣ Production Setup

### Using tollbooth Library

```bash
go get github.com/didip/tollbooth/v7
```

```go
// cmd/api/main.go
package main

import (
    "net/http"
    "time"
    
    "github.com/didip/tollbooth/v7"
    "github.com/didip/tollbooth/v7/limiter"
)

func main() {
    lmt := tollbooth.NewLimiter(10, &limiter.ExpirableOptions{
        DefaultExpirationTTL: time.Hour,
    })
    
    // Set custom message
    lmt.SetMessage("You have reached maximum request limit")
    
    // Set headers
    lmt.SetMessageContentType("application/json")
    
    http.Handle("/api/", tollbooth.LimitFuncHandler(lmt, apiHandler))
    http.ListenAndServe(":8080", nil)
}

func apiHandler(w http.ResponseWriter, r *http.Request) {
    w.Write([]byte("API Response"))
}
```

### Complete Setup

```go
// cmd/api/main.go
package main

import (
    "log"
    "net/http"
    
    "github.com/go-chi/chi/v5"
    "myapp/internal/middleware"
    "myapp/internal/ratelimit"
)

func main() {
    r := chi.NewRouter()
    
    // Global rate limiter: 100 req/s per IP
    globalLimiter := ratelimit.NewUserRateLimiter(100, 200)
    r.Use(middleware.RateLimit(globalLimiter))
    
    // API routes
    r.Route("/api", func(r chi.Router) {
        // API rate limiter: 50 req/s per user
        apiLimiter := ratelimit.NewUserRateLimiter(50, 100)
        r.Use(middleware.RateLimit(apiLimiter))
        
        r.Get("/users", listUsersHandler)
        r.Post("/users", createUserHandler)
    })
    
    log.Fatal(http.ListenAndServe(":8080", r))
}
```

---

## 📋 Rate Limiting Checklist

### Junior ✅
- [ ] Basic token bucket
- [ ] Simple in-memory rate limiting
- [ ] Per-IP rate limiting

### Mid ✅
- [ ] Sliding window algorithm
- [ ] Per-user rate limiting
- [ ] Rate limit headers
- [ ] Redis-based rate limiting

### Senior ✅
- [ ] Tiered rate limiting
- [ ] Distributed rate limiting
- [ ] Graceful degradation
- [ ] Custom rate limit strategies

### Expert ✅
- [ ] Adaptive rate limiting
- [ ] Global + per-endpoint limits
- [ ] Rate limit analytics
- [ ] Cost-based rate limiting
