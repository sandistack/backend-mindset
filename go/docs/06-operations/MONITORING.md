# 📊 Monitoring & Observability di Go

## Kenapa Penting?

Monitoring untuk:
- ✅ Track system health
- ✅ Detect issues early
- ✅ Performance analysis
- ✅ Debugging production

---

## 📚 Daftar Isi

1. [Prometheus Metrics](#1️⃣-prometheus-metrics)
2. [Health Checks](#2️⃣-health-checks)
3. [Logging](#3️⃣-logging)
4. [Profiling (pprof)](#4️⃣-profiling-pprof)
5. [Distributed Tracing](#5️⃣-distributed-tracing)
6. [Production Setup](#6️⃣-production-setup)

---

## 1️⃣ Prometheus Metrics

### Installation

```bash
go get github.com/prometheus/client_golang/prometheus
go get github.com/prometheus/client_golang/prometheus/promhttp
```

### Basic Metrics

```go
// internal/metrics/metrics.go
package metrics

import (
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
)

var (
    // Counter - monotonically increasing
    RequestsTotal = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "http_requests_total",
            Help: "Total number of HTTP requests",
        },
        []string{"method", "endpoint", "status"},
    )
    
    // Histogram - distribution of values
    RequestDuration = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "http_request_duration_seconds",
            Help:    "HTTP request latency in seconds",
            Buckets: prometheus.DefBuckets,
        },
        []string{"method", "endpoint"},
    )
    
    // Gauge - value that can go up or down
    ActiveConnections = promauto.NewGauge(
        prometheus.GaugeOpts{
            Name: "active_connections",
            Help: "Number of active connections",
        },
    )
    
    // Summary - similar to histogram
    ResponseSize = promauto.NewSummaryVec(
        prometheus.SummaryOpts{
            Name:       "http_response_size_bytes",
            Help:       "HTTP response size in bytes",
            Objectives: map[float64]float64{0.5: 0.05, 0.9: 0.01, 0.99: 0.001},
        },
        []string{"endpoint"},
    )
)
```

### Metrics Middleware

```go
// internal/middleware/metrics.go
package middleware

import (
    "net/http"
    "strconv"
    "time"
    
    "myapp/internal/metrics"
)

func PrometheusMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        
        // Increment active connections
        metrics.ActiveConnections.Inc()
        defer metrics.ActiveConnections.Dec()
        
        // Wrap ResponseWriter to capture status code
        wrw := &responseWriter{ResponseWriter: w, statusCode: http.StatusOK}
        
        next.ServeHTTP(wrw, r)
        
        // Record metrics
        duration := time.Since(start).Seconds()
        status := strconv.Itoa(wrw.statusCode)
        
        metrics.RequestsTotal.WithLabelValues(r.Method, r.URL.Path, status).Inc()
        metrics.RequestDuration.WithLabelValues(r.Method, r.URL.Path).Observe(duration)
        metrics.ResponseSize.WithLabelValues(r.URL.Path).Observe(float64(wrw.bytesWritten))
    })
}

type responseWriter struct {
    http.ResponseWriter
    statusCode   int
    bytesWritten int
}

func (rw *responseWriter) WriteHeader(code int) {
    rw.statusCode = code
    rw.ResponseWriter.WriteHeader(code)
}

func (rw *responseWriter) Write(b []byte) (int, error) {
    n, err := rw.ResponseWriter.Write(b)
    rw.bytesWritten += n
    return n, err
}
```

### Exposing Metrics

```go
// cmd/api/main.go
package main

import (
    "log"
    "net/http"
    
    "github.com/go-chi/chi/v5"
    "github.com/prometheus/client_golang/prometheus/promhttp"
    
    "myapp/internal/middleware"
)

func main() {
    r := chi.NewRouter()
    
    // Apply metrics middleware
    r.Use(middleware.PrometheusMiddleware)
    
    // Expose metrics endpoint
    r.Handle("/metrics", promhttp.Handler())
    
    // API routes
    r.Get("/api/users", listUsersHandler)
    r.Post("/api/users", createUserHandler)
    
    log.Println("Server starting on :8080")
    log.Fatal(http.ListenAndServe(":8080", r))
}
```

### Custom Metrics

```go
// internal/metrics/custom.go
package metrics

import (
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
)

var (
    // Database metrics
    DBQueryDuration = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "db_query_duration_seconds",
            Help:    "Database query latency",
            Buckets: []float64{.001, .005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5},
        },
        []string{"query_type"},
    )
    
    DBConnectionsOpen = promauto.NewGauge(
        prometheus.GaugeOpts{
            Name: "db_connections_open",
            Help: "Number of open database connections",
        },
    )
    
    // Cache metrics
    CacheHits = promauto.NewCounter(
        prometheus.CounterOpts{
            Name: "cache_hits_total",
            Help: "Total number of cache hits",
        },
    )
    
    CacheMisses = promauto.NewCounter(
        prometheus.CounterOpts{
            Name: "cache_misses_total",
            Help: "Total number of cache misses",
        },
    )
    
    // Background job metrics
    JobsProcessed = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "jobs_processed_total",
            Help: "Total number of jobs processed",
        },
        []string{"job_type", "status"},
    )
    
    JobDuration = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "job_duration_seconds",
            Help:    "Job processing duration",
            Buckets: prometheus.ExponentialBuckets(0.1, 2, 10),
        },
        []string{"job_type"},
    )
)

// Usage in repository
func (r *UserRepository) GetByID(ctx context.Context, id int) (*User, error) {
    start := time.Now()
    defer func() {
        DBQueryDuration.WithLabelValues("select").Observe(time.Since(start).Seconds())
    }()
    
    // Query database...
}

// Usage in cache
func (c *Cache) Get(key string) (interface{}, bool) {
    value, found := c.cache.Get(key)
    
    if found {
        CacheHits.Inc()
    } else {
        CacheMisses.Inc()
    }
    
    return value, found
}
```

---

## 2️⃣ Health Checks

### Basic Health Check

```go
// internal/health/health.go
package health

import (
    "context"
    "encoding/json"
    "net/http"
    "time"
)

type Status string

const (
    StatusUp   Status = "UP"
    StatusDown Status = "DOWN"
)

type HealthCheck struct {
    Status    Status                 `json:"status"`
    Timestamp time.Time              `json:"timestamp"`
    Checks    map[string]CheckResult `json:"checks"`
}

type CheckResult struct {
    Status  Status `json:"status"`
    Message string `json:"message,omitempty"`
}

type Checker interface {
    Check(ctx context.Context) CheckResult
}

type Handler struct {
    checkers map[string]Checker
}

func NewHandler() *Handler {
    return &Handler{
        checkers: make(map[string]Checker),
    }
}

func (h *Handler) Register(name string, checker Checker) {
    h.checkers[name] = checker
}

func (h *Handler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
    ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
    defer cancel()
    
    health := HealthCheck{
        Status:    StatusUp,
        Timestamp: time.Now(),
        Checks:    make(map[string]CheckResult),
    }
    
    for name, checker := range h.checkers {
        result := checker.Check(ctx)
        health.Checks[name] = result
        
        if result.Status == StatusDown {
            health.Status = StatusDown
        }
    }
    
    statusCode := http.StatusOK
    if health.Status == StatusDown {
        statusCode = http.StatusServiceUnavailable
    }
    
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(statusCode)
    json.NewEncoder(w).Encode(health)
}
```

### Database Health Check

```go
// internal/health/database.go
package health

import (
    "context"
    "database/sql"
)

type DatabaseChecker struct {
    db *sql.DB
}

func NewDatabaseChecker(db *sql.DB) *DatabaseChecker {
    return &DatabaseChecker{db: db}
}

func (c *DatabaseChecker) Check(ctx context.Context) CheckResult {
    if err := c.db.PingContext(ctx); err != nil {
        return CheckResult{
            Status:  StatusDown,
            Message: err.Error(),
        }
    }
    
    return CheckResult{Status: StatusUp}
}
```

### Redis Health Check

```go
// internal/health/redis.go
package health

import (
    "context"
    
    "github.com/go-redis/redis/v8"
)

type RedisChecker struct {
    client *redis.Client
}

func NewRedisChecker(client *redis.Client) *RedisChecker {
    return &RedisChecker{client: client}
}

func (c *RedisChecker) Check(ctx context.Context) CheckResult {
    if err := c.client.Ping(ctx).Err(); err != nil {
        return CheckResult{
            Status:  StatusDown,
            Message: err.Error(),
        }
    }
    
    return CheckResult{Status: StatusUp}
}
```

### Setup

```go
// cmd/api/main.go
func main() {
    // Initialize dependencies
    db := setupDatabase()
    cache := setupRedis()
    
    // Setup health checks
    healthHandler := health.NewHandler()
    healthHandler.Register("database", health.NewDatabaseChecker(db))
    healthHandler.Register("redis", health.NewRedisChecker(cache))
    
    // Routes
    http.Handle("/health", healthHandler)
    http.Handle("/health/live", http.HandlerFunc(livenessHandler))
    http.Handle("/health/ready", http.HandlerFunc(readinessHandler))
}

func livenessHandler(w http.ResponseWriter, r *http.Request) {
    // Check if app is alive (always return 200)
    w.WriteHeader(http.StatusOK)
    w.Write([]byte("OK"))
}

func readinessHandler(w http.ResponseWriter, r *http.Request) {
    // Check if app is ready to serve traffic
    // Check database, cache, etc.
}
```

---

## 3️⃣ Logging

### Structured Logging with zerolog

```bash
go get github.com/rs/zerolog/log
```

```go
// internal/logger/logger.go
package logger

import (
    "os"
    "time"
    
    "github.com/rs/zerolog"
    "github.com/rs/zerolog/log"
)

func Setup(level string, pretty bool) {
    // Parse level
    logLevel, err := zerolog.ParseLevel(level)
    if err != nil {
        logLevel = zerolog.InfoLevel
    }
    
    zerolog.SetGlobalLevel(logLevel)
    
    // Pretty print for development
    if pretty {
        log.Logger = log.Output(zerolog.ConsoleWriter{
            Out:        os.Stdout,
            TimeFormat: time.RFC3339,
        })
    }
    
    // Add caller info
    log.Logger = log.With().Caller().Logger()
}

// Usage
func init() {
    Setup("info", true)
}
```

### Logging Middleware

```go
// internal/middleware/logging.go
package middleware

import (
    "net/http"
    "time"
    
    "github.com/rs/zerolog/log"
)

func Logging(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        
        // Get request ID from context
        requestID := GetRequestID(r.Context())
        
        // Create logger with context
        logger := log.With().
            Str("request_id", requestID).
            Str("method", r.Method).
            Str("path", r.URL.Path).
            Str("remote_addr", r.RemoteAddr).
            Logger()
        
        logger.Info().Msg("Request started")
        
        // Wrap response writer
        wrw := &responseWriter{ResponseWriter: w, statusCode: http.StatusOK}
        
        next.ServeHTTP(wrw, r)
        
        duration := time.Since(start)
        
        logger.Info().
            Int("status", wrw.statusCode).
            Dur("duration", duration).
            Int("bytes", wrw.bytesWritten).
            Msg("Request completed")
    })
}
```

### Application Logging

```go
// internal/service/user_service.go
package service

import (
    "context"
    
    "github.com/rs/zerolog/log"
)

func (s *UserService) CreateUser(ctx context.Context, req *CreateUserRequest) (*User, error) {
    logger := log.With().
        Str("email", req.Email).
        Logger()
    
    logger.Info().Msg("Creating user")
    
    // Business logic...
    
    if err != nil {
        logger.Error().
            Err(err).
            Msg("Failed to create user")
        return nil, err
    }
    
    logger.Info().
        Int("user_id", user.ID).
        Msg("User created successfully")
    
    return user, nil
}
```

---

## 4️⃣ Profiling (pprof)

### Enable pprof

```go
// cmd/api/main.go
package main

import (
    "net/http"
    _ "net/http/pprof"
)

func main() {
    // Start pprof server
    go func() {
        log.Println("pprof server starting on :6060")
        log.Println(http.ListenAndServe("localhost:6060", nil))
    }()
    
    // Main application...
}
```

### Profiling Endpoints

```
http://localhost:6060/debug/pprof/          # Index page
http://localhost:6060/debug/pprof/heap      # Heap profile
http://localhost:6060/debug/pprof/goroutine # Goroutine profile
http://localhost:6060/debug/pprof/profile   # CPU profile (30s)
http://localhost:6060/debug/pprof/trace     # Execution trace
```

### CLI Profiling

```bash
# CPU profiling (30 seconds)
go tool pprof http://localhost:6060/debug/pprof/profile

# Heap profiling
go tool pprof http://localhost:6060/debug/pprof/heap

# Goroutine profiling
go tool pprof http://localhost:6060/debug/pprof/goroutine

# Interactive commands in pprof
(pprof) top        # Top functions by CPU/memory
(pprof) list main  # Show source code
(pprof) web        # Generate graph (requires graphviz)
```

### Custom Profiling

```go
// internal/profiler/profiler.go
package profiler

import (
    "os"
    "runtime"
    "runtime/pprof"
    "time"
)

func StartCPUProfile(filename string) func() {
    f, err := os.Create(filename)
    if err != nil {
        panic(err)
    }
    
    pprof.StartCPUProfile(f)
    
    return func() {
        pprof.StopCPUProfile()
        f.Close()
    }
}

func WriteHeapProfile(filename string) error {
    f, err := os.Create(filename)
    if err != nil {
        return err
    }
    defer f.Close()
    
    runtime.GC()
    return pprof.WriteHeapProfile(f)
}

// Usage
func main() {
    // CPU profiling
    stop := profiler.StartCPUProfile("cpu.prof")
    defer stop()
    
    // Run application...
    
    // Heap profiling
    profiler.WriteHeapProfile("heap.prof")
}
```

---

## 5️⃣ Distributed Tracing

### OpenTelemetry Setup

```bash
go get go.opentelemetry.io/otel
go get go.opentelemetry.io/otel/exporters/jaeger
go get go.opentelemetry.io/otel/sdk/trace
```

```go
// internal/tracing/tracer.go
package tracing

import (
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/exporters/jaeger"
    "go.opentelemetry.io/otel/sdk/resource"
    tracesdk "go.opentelemetry.io/otel/sdk/trace"
    semconv "go.opentelemetry.io/otel/semconv/v1.4.0"
)

func InitTracer(serviceName, jaegerURL string) (*tracesdk.TracerProvider, error) {
    exp, err := jaeger.New(jaeger.WithCollectorEndpoint(jaeger.WithEndpoint(jaegerURL)))
    if err != nil {
        return nil, err
    }
    
    tp := tracesdk.NewTracerProvider(
        tracesdk.WithBatcher(exp),
        tracesdk.WithResource(resource.NewWithAttributes(
            semconv.SchemaURL,
            semconv.ServiceNameKey.String(serviceName),
        )),
    )
    
    otel.SetTracerProvider(tp)
    
    return tp, nil
}
```

### Tracing Middleware

```go
// internal/middleware/tracing.go
package middleware

import (
    "net/http"
    
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/attribute"
)

func Tracing(next http.Handler) http.Handler {
    tracer := otel.Tracer("http-server")
    
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        ctx, span := tracer.Start(r.Context(), r.URL.Path)
        defer span.End()
        
        span.SetAttributes(
            attribute.String("http.method", r.Method),
            attribute.String("http.url", r.URL.String()),
            attribute.String("http.user_agent", r.UserAgent()),
        )
        
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}
```

---

## 6️⃣ Production Setup

### Complete Observability Stack

```go
// cmd/api/main.go
package main

import (
    "context"
    "log"
    "net/http"
    
    "github.com/go-chi/chi/v5"
    "github.com/prometheus/client_golang/prometheus/promhttp"
    
    "myapp/internal/health"
    "myapp/internal/logger"
    "myapp/internal/middleware"
    "myapp/internal/tracing"
)

func main() {
    // Setup logging
    logger.Setup("info", false)
    
    // Setup tracing
    tp, err := tracing.InitTracer("myapp", "http://jaeger:14268/api/traces")
    if err != nil {
        log.Fatal(err)
    }
    defer tp.Shutdown(context.Background())
    
    // Setup health checks
    healthHandler := health.NewHandler()
    healthHandler.Register("database", health.NewDatabaseChecker(db))
    healthHandler.Register("redis", health.NewRedisChecker(cache))
    
    // Setup router
    r := chi.NewRouter()
    
    // Apply middleware
    r.Use(middleware.RequestID)
    r.Use(middleware.Logging)
    r.Use(middleware.PrometheusMiddleware)
    r.Use(middleware.Tracing)
    
    // Observability endpoints
    r.Handle("/metrics", promhttp.Handler())
    r.Handle("/health", healthHandler)
    
    // API routes
    r.Route("/api", func(r chi.Router) {
        r.Get("/users", listUsersHandler)
        r.Post("/users", createUserHandler)
    })
    
    log.Println("Server starting on :8080")
    log.Fatal(http.ListenAndServe(":8080", r))
}
```

---

## 📋 Monitoring Checklist

### Junior ✅
- [ ] Basic health check endpoint
- [ ] Simple request logging
- [ ] pprof enabled

### Mid ✅
- [ ] Prometheus metrics
- [ ] Structured logging
- [ ] Database health checks
- [ ] Request/response metrics

### Senior ✅
- [ ] Custom business metrics
- [ ] Distributed tracing
- [ ] Error rate monitoring
- [ ] Performance profiling

### Expert ✅
- [ ] Full observability stack (metrics + logs + traces)
- [ ] Alerting rules
- [ ] SLO/SLA monitoring
- [ ] Performance regression detection
