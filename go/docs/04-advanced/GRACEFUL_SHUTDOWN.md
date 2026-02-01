# 🛑 Graceful Shutdown di Go

## Kenapa Penting?

Graceful shutdown untuk:
- ✅ Complete in-flight requests
- ✅ Close connections properly
- ✅ Save state
- ✅ Prevent data loss

---

## 📚 Daftar Isi

1. [Signal Handling](#1️⃣-signal-handling)
2. [HTTP Server Shutdown](#2️⃣-http-server-shutdown)
3. [Worker Shutdown](#3️⃣-worker-shutdown)
4. [Database Connection Cleanup](#4️⃣-database-connection-cleanup)
5. [Complete Example](#5️⃣-complete-example)
6. [Production Patterns](#6️⃣-production-patterns)

---

## 1️⃣ Signal Handling

### Basic Signal Handling

```go
// cmd/api/main.go
package main

import (
    "fmt"
    "os"
    "os/signal"
    "syscall"
    "time"
)

func main() {
    // Create channel to receive OS signals
    quit := make(chan os.Signal, 1)
    
    // Notify channel on SIGINT (Ctrl+C) or SIGTERM
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    
    // Run application
    go runApp()
    
    // Block until signal received
    sig := <-quit
    fmt.Printf("Received signal: %v\n", sig)
    
    // Cleanup
    cleanup()
    
    fmt.Println("Application stopped")
}

func runApp() {
    for {
        fmt.Println("App running...")
        time.Sleep(time.Second)
    }
}

func cleanup() {
    fmt.Println("Cleaning up...")
    time.Sleep(2 * time.Second)
}
```

### Multiple Signals

```go
// cmd/api/main.go
package main

import (
    "fmt"
    "os"
    "os/signal"
    "syscall"
)

func main() {
    sigChan := make(chan os.Signal, 1)
    
    // Catch different signals
    signal.Notify(sigChan,
        syscall.SIGINT,  // Ctrl+C
        syscall.SIGTERM, // kill
        syscall.SIGQUIT, // quit
        syscall.SIGHUP,  // reload config
    )
    
    for {
        sig := <-sigChan
        
        switch sig {
        case syscall.SIGINT, syscall.SIGTERM:
            fmt.Println("Shutting down...")
            shutdown()
            return
            
        case syscall.SIGHUP:
            fmt.Println("Reloading configuration...")
            reloadConfig()
            
        case syscall.SIGQUIT:
            fmt.Println("Quitting without cleanup...")
            os.Exit(0)
        }
    }
}
```

---

## 2️⃣ HTTP Server Shutdown

### Basic HTTP Shutdown

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
    // Create HTTP server
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
    
    // Create shutdown context with timeout
    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()
    
    // Graceful shutdown
    if err := server.Shutdown(ctx); err != nil {
        log.Fatalf("Server forced to shutdown: %v", err)
    }
    
    log.Println("Server stopped gracefully")
}

func setupRoutes() http.Handler {
    mux := http.NewServeMux()
    
    mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        // Simulate slow request
        time.Sleep(5 * time.Second)
        w.Write([]byte("Hello, World!"))
    })
    
    mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
        w.Write([]byte("OK"))
    })
    
    return mux
}
```

### With Health Check

```go
// cmd/api/main.go
package main

import (
    "context"
    "log"
    "net/http"
    "os"
    "os/signal"
    "sync/atomic"
    "syscall"
    "time"
)

type Server struct {
    httpServer *http.Server
    isHealthy  atomic.Bool
}

func NewServer() *Server {
    s := &Server{
        httpServer: &http.Server{
            Addr:    ":8080",
            Handler: nil,
        },
    }
    
    s.isHealthy.Store(true)
    s.httpServer.Handler = s.setupRoutes()
    
    return s
}

func (s *Server) setupRoutes() http.Handler {
    mux := http.NewServeMux()
    
    mux.HandleFunc("/health", s.healthCheck)
    mux.HandleFunc("/", s.handleRequest)
    
    return mux
}

func (s *Server) healthCheck(w http.ResponseWriter, r *http.Request) {
    if s.isHealthy.Load() {
        w.WriteHeader(http.StatusOK)
        w.Write([]byte("OK"))
    } else {
        w.WriteHeader(http.StatusServiceUnavailable)
        w.Write([]byte("Shutting down"))
    }
}

func (s *Server) handleRequest(w http.ResponseWriter, r *http.Request) {
    time.Sleep(3 * time.Second)
    w.Write([]byte("Request completed"))
}

func (s *Server) Start() {
    go func() {
        log.Println("Server starting on :8080")
        if err := s.httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
            log.Fatalf("Server error: %v", err)
        }
    }()
}

func (s *Server) Shutdown() {
    log.Println("Shutting down server...")
    
    // Mark unhealthy immediately
    s.isHealthy.Store(false)
    
    // Wait for load balancer to detect (health check interval)
    log.Println("Waiting for load balancer to detect...")
    time.Sleep(5 * time.Second)
    
    // Graceful shutdown with timeout
    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()
    
    if err := s.httpServer.Shutdown(ctx); err != nil {
        log.Printf("Server forced to shutdown: %v", err)
    }
    
    log.Println("Server stopped")
}

func main() {
    server := NewServer()
    server.Start()
    
    // Wait for signal
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit
    
    server.Shutdown()
}
```

---

## 3️⃣ Worker Shutdown

### Basic Worker Shutdown

```go
// internal/worker/worker.go
package worker

import (
    "context"
    "fmt"
    "log"
    "time"
)

type Worker struct {
    name string
    jobs <-chan int
}

func NewWorker(name string, jobs <-chan int) *Worker {
    return &Worker{
        name: name,
        jobs: jobs,
    }
}

func (w *Worker) Start(ctx context.Context) {
    log.Printf("%s started\n", w.name)
    
    for {
        select {
        case <-ctx.Done():
            log.Printf("%s stopping...\n", w.name)
            return
            
        case job, ok := <-w.jobs:
            if !ok {
                log.Printf("%s: jobs channel closed\n", w.name)
                return
            }
            
            w.processJob(ctx, job)
        }
    }
}

func (w *Worker) processJob(ctx context.Context, job int) {
    select {
    case <-ctx.Done():
        log.Printf("%s: job %d canceled\n", w.name, job)
        return
    default:
        log.Printf("%s: processing job %d\n", w.name, job)
        time.Sleep(2 * time.Second)
        log.Printf("%s: completed job %d\n", w.name, job)
    }
}
```

### Worker Pool with Graceful Shutdown

```go
// internal/worker/pool.go
package worker

import (
    "context"
    "log"
    "sync"
)

type WorkerPool struct {
    numWorkers int
    jobs       chan int
    wg         sync.WaitGroup
}

func NewWorkerPool(numWorkers int) *WorkerPool {
    return &WorkerPool{
        numWorkers: numWorkers,
        jobs:       make(chan int, 100),
    }
}

func (p *WorkerPool) Start(ctx context.Context) {
    for i := 0; i < p.numWorkers; i++ {
        p.wg.Add(1)
        worker := NewWorker(fmt.Sprintf("Worker-%d", i), p.jobs)
        go func() {
            defer p.wg.Done()
            worker.Start(ctx)
        }()
    }
}

func (p *WorkerPool) Submit(job int) {
    p.jobs <- job
}

func (p *WorkerPool) Shutdown() {
    log.Println("Closing jobs channel...")
    close(p.jobs)
    
    log.Println("Waiting for workers to finish...")
    p.wg.Wait()
    
    log.Println("All workers stopped")
}

// Usage
func main() {
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()
    
    pool := NewWorkerPool(3)
    pool.Start(ctx)
    
    // Submit jobs
    for i := 0; i < 10; i++ {
        pool.Submit(i)
    }
    
    // Wait for signal
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit
    
    // Graceful shutdown
    cancel()           // Cancel context to stop accepting new jobs
    pool.Shutdown()    // Wait for in-flight jobs to complete
}
```

---

## 4️⃣ Database Connection Cleanup

### Database Cleanup

```go
// internal/database/db.go
package database

import (
    "context"
    "database/sql"
    "log"
    "time"
    
    _ "github.com/lib/pq"
)

type Database struct {
    db *sql.DB
}

func NewDatabase(dsn string) (*Database, error) {
    db, err := sql.Open("postgres", dsn)
    if err != nil {
        return nil, err
    }
    
    if err := db.Ping(); err != nil {
        return nil, err
    }
    
    // Set connection pool settings
    db.SetMaxOpenConns(25)
    db.SetMaxIdleConns(5)
    db.SetConnMaxLifetime(5 * time.Minute)
    
    return &Database{db: db}, nil
}

func (d *Database) Close() error {
    log.Println("Closing database connections...")
    
    // Close all connections
    if err := d.db.Close(); err != nil {
        log.Printf("Error closing database: %v", err)
        return err
    }
    
    log.Println("Database connections closed")
    return nil
}

func (d *Database) Shutdown(ctx context.Context) error {
    log.Println("Shutting down database...")
    
    // Wait for ongoing transactions
    done := make(chan error, 1)
    go func() {
        done <- d.Close()
    }()
    
    select {
    case err := <-done:
        return err
    case <-ctx.Done():
        log.Println("Database shutdown timeout")
        return ctx.Err()
    }
}
```

### Redis Cleanup

```go
// internal/cache/redis.go
package cache

import (
    "context"
    "log"
    
    "github.com/go-redis/redis/v8"
)

type RedisCache struct {
    client *redis.Client
}

func NewRedisCache(addr string) *RedisCache {
    client := redis.NewClient(&redis.Options{
        Addr: addr,
    })
    
    return &RedisCache{client: client}
}

func (r *RedisCache) Close() error {
    log.Println("Closing Redis connection...")
    
    if err := r.client.Close(); err != nil {
        log.Printf("Error closing Redis: %v", err)
        return err
    }
    
    log.Println("Redis connection closed")
    return nil
}

func (r *RedisCache) Shutdown(ctx context.Context) error {
    log.Println("Shutting down Redis...")
    
    done := make(chan error, 1)
    go func() {
        done <- r.Close()
    }()
    
    select {
    case err := <-done:
        return err
    case <-ctx.Done():
        return ctx.Err()
    }
}
```

---

## 5️⃣ Complete Example

### Full Application Shutdown

```go
// cmd/api/main.go
package main

import (
    "context"
    "log"
    "net/http"
    "os"
    "os/signal"
    "sync"
    "syscall"
    "time"
    
    "myapp/internal/cache"
    "myapp/internal/database"
    "myapp/internal/worker"
)

type Application struct {
    server *http.Server
    db     *database.Database
    cache  *cache.RedisCache
    pool   *worker.WorkerPool
}

func NewApplication() (*Application, error) {
    // Initialize database
    db, err := database.NewDatabase("postgres://...")
    if err != nil {
        return nil, err
    }
    
    // Initialize cache
    cache := cache.NewRedisCache("localhost:6379")
    
    // Initialize worker pool
    pool := worker.NewWorkerPool(5)
    
    // Create HTTP server
    server := &http.Server{
        Addr:    ":8080",
        Handler: setupRoutes(db, cache),
    }
    
    return &Application{
        server: server,
        db:     db,
        cache:  cache,
        pool:   pool,
    }, nil
}

func (app *Application) Start(ctx context.Context) {
    // Start HTTP server
    go func() {
        log.Println("Starting HTTP server on :8080")
        if err := app.server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
            log.Fatalf("HTTP server error: %v", err)
        }
    }()
    
    // Start worker pool
    app.pool.Start(ctx)
    
    log.Println("Application started")
}

func (app *Application) Shutdown() {
    log.Println("Starting graceful shutdown...")
    
    // Create shutdown context with timeout
    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()
    
    var wg sync.WaitGroup
    
    // Shutdown HTTP server
    wg.Add(1)
    go func() {
        defer wg.Done()
        log.Println("Shutting down HTTP server...")
        if err := app.server.Shutdown(ctx); err != nil {
            log.Printf("HTTP server shutdown error: %v", err)
        }
    }()
    
    // Shutdown worker pool
    wg.Add(1)
    go func() {
        defer wg.Done()
        log.Println("Shutting down worker pool...")
        app.pool.Shutdown()
    }()
    
    // Wait for HTTP and workers to finish
    wg.Wait()
    
    // Shutdown database
    wg.Add(1)
    go func() {
        defer wg.Done()
        if err := app.db.Shutdown(ctx); err != nil {
            log.Printf("Database shutdown error: %v", err)
        }
    }()
    
    // Shutdown cache
    wg.Add(1)
    go func() {
        defer wg.Done()
        if err := app.cache.Shutdown(ctx); err != nil {
            log.Printf("Cache shutdown error: %v", err)
        }
    }()
    
    wg.Wait()
    
    log.Println("Graceful shutdown completed")
}

func main() {
    app, err := NewApplication()
    if err != nil {
        log.Fatalf("Failed to initialize application: %v", err)
    }
    
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()
    
    app.Start(ctx)
    
    // Wait for interrupt signal
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit
    
    cancel() // Cancel context
    app.Shutdown()
}
```

---

## 6️⃣ Production Patterns

### Shutdown Manager

```go
// internal/shutdown/manager.go
package shutdown

import (
    "context"
    "log"
    "sync"
    "time"
)

type Shutdownable interface {
    Shutdown(ctx context.Context) error
}

type Manager struct {
    components []Shutdownable
    timeout    time.Duration
}

func NewManager(timeout time.Duration) *Manager {
    return &Manager{
        components: []Shutdownable{},
        timeout:    timeout,
    }
}

func (m *Manager) Register(component Shutdownable) {
    m.components = append(m.components, component)
}

func (m *Manager) Shutdown() error {
    ctx, cancel := context.WithTimeout(context.Background(), m.timeout)
    defer cancel()
    
    var wg sync.WaitGroup
    errors := make(chan error, len(m.components))
    
    for _, component := range m.components {
        wg.Add(1)
        go func(c Shutdownable) {
            defer wg.Done()
            if err := c.Shutdown(ctx); err != nil {
                errors <- err
            }
        }(component)
    }
    
    wg.Wait()
    close(errors)
    
    // Collect errors
    var errs []error
    for err := range errors {
        errs = append(errs, err)
        log.Printf("Shutdown error: %v", err)
    }
    
    if len(errs) > 0 {
        return fmt.Errorf("shutdown completed with %d errors", len(errs))
    }
    
    return nil
}
```

### Usage

```go
func main() {
    // Create components
    server := NewHTTPServer()
    db := NewDatabase()
    cache := NewCache()
    
    // Create shutdown manager
    shutdownManager := shutdown.NewManager(30 * time.Second)
    shutdownManager.Register(server)
    shutdownManager.Register(db)
    shutdownManager.Register(cache)
    
    // Start components...
    
    // Wait for signal
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit
    
    // Graceful shutdown
    if err := shutdownManager.Shutdown(); err != nil {
        log.Printf("Shutdown error: %v", err)
    }
}
```

---

## 📋 Graceful Shutdown Checklist

### Junior ✅
- [ ] Basic signal handling (SIGINT, SIGTERM)
- [ ] HTTP server shutdown
- [ ] Close database connections

### Mid ✅
- [ ] Worker pool shutdown
- [ ] Context-based cancellation
- [ ] Shutdown timeout
- [ ] Wait for in-flight requests

### Senior ✅
- [ ] Health check during shutdown
- [ ] Parallel component shutdown
- [ ] Error handling during shutdown
- [ ] Graceful degradation

### Expert ✅
- [ ] Shutdown manager pattern
- [ ] Dependency-ordered shutdown
- [ ] Metrics collection during shutdown
- [ ] Zero-downtime deployments
