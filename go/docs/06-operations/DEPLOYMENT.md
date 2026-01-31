# 🚀 DEPLOYMENT - Deployment Go Application (Junior → Senior)

Dokumentasi lengkap tentang deployment Go application - dari build hingga production.

---

## 🎯 Go Deployment

```
Deployment Stages:
Build → Package → Deploy → Monitor

Go Advantages:
- Single binary (no dependencies)
- Cross-compilation
- Fast startup
- Low memory footprint
```

---

## 1️⃣ JUNIOR LEVEL - Building Go Applications

### Basic Build

```bash
# Build for current OS
go build -o myapp main.go

# Build with specific output
go build -o bin/myapp ./cmd/api

# Run directly
go run main.go

# Build and run
go build -o myapp && ./myapp
```

### Build Flags

```bash
# Remove debug info (smaller binary)
go build -ldflags="-s -w" -o myapp main.go

# Inject version at build time
go build -ldflags="-X main.Version=1.0.0 -X main.BuildTime=$(date -u +%Y%m%d%H%M%S)" -o myapp main.go
```

```go
// main.go
package main

import "fmt"

var (
    Version   = "dev"
    BuildTime = "unknown"
)

func main() {
    fmt.Printf("Version: %s, Built: %s\n", Version, BuildTime)
}
```

### Cross-Compilation

```bash
# Build for Linux
GOOS=linux GOARCH=amd64 go build -o myapp-linux main.go

# Build for Windows
GOOS=windows GOARCH=amd64 go build -o myapp.exe main.go

# Build for macOS
GOOS=darwin GOARCH=amd64 go build -o myapp-mac main.go

# Build for ARM (Raspberry Pi)
GOOS=linux GOARCH=arm go build -o myapp-arm main.go

# Build for ARM64 (Apple Silicon, AWS Graviton)
GOOS=linux GOARCH=arm64 go build -o myapp-arm64 main.go
```

---

## 2️⃣ MID LEVEL - Docker Deployment

### Simple Dockerfile

```dockerfile
# Build stage
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source
COPY . .

# Build
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o main ./cmd/api

# Run stage
FROM alpine:3.19

WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/main .

# Copy configs if needed
# COPY --from=builder /app/config ./config

EXPOSE 8080

CMD ["./main"]
```

### Multi-Stage with Cache

```dockerfile
# syntax=docker/dockerfile:1.4

# Build stage
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Install dependencies first (cached)
COPY go.mod go.sum ./
RUN --mount=type=cache,target=/go/pkg/mod \
    go mod download

# Copy source and build
COPY . .
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o main ./cmd/api

# Final stage
FROM gcr.io/distroless/static-debian11

WORKDIR /app

COPY --from=builder /app/main .

USER nonroot:nonroot

EXPOSE 8080

ENTRYPOINT ["./main"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    environment:
      - APP_ENV=production
      - DATABASE_URL=postgres://user:pass@db:5432/myapp?sslmode=disable
      - REDIS_URL=redis://redis:6379
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=myapp
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d myapp"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

---

## 3️⃣ MID-SENIOR LEVEL - Configuration Management

### Environment Variables

```go
// config/config.go
package config

import (
    "os"
    "strconv"
    "time"
)

type Config struct {
    App      AppConfig
    Database DatabaseConfig
    Redis    RedisConfig
    JWT      JWTConfig
}

type AppConfig struct {
    Name        string
    Env         string
    Port        int
    Debug       bool
    GracefulTimeout time.Duration
}

type DatabaseConfig struct {
    Host     string
    Port     int
    User     string
    Password string
    Name     string
    SSLMode  string
    MaxConns int
}

type RedisConfig struct {
    Host     string
    Port     int
    Password string
    DB       int
}

type JWTConfig struct {
    Secret    string
    ExpiresIn time.Duration
}

func Load() *Config {
    return &Config{
        App: AppConfig{
            Name:            getEnv("APP_NAME", "myapp"),
            Env:             getEnv("APP_ENV", "development"),
            Port:            getEnvAsInt("APP_PORT", 8080),
            Debug:           getEnvAsBool("APP_DEBUG", true),
            GracefulTimeout: getEnvAsDuration("APP_GRACEFUL_TIMEOUT", 30*time.Second),
        },
        Database: DatabaseConfig{
            Host:     getEnv("DB_HOST", "localhost"),
            Port:     getEnvAsInt("DB_PORT", 5432),
            User:     getEnv("DB_USER", "postgres"),
            Password: getEnv("DB_PASSWORD", ""),
            Name:     getEnv("DB_NAME", "myapp"),
            SSLMode:  getEnv("DB_SSLMODE", "disable"),
            MaxConns: getEnvAsInt("DB_MAX_CONNS", 25),
        },
        Redis: RedisConfig{
            Host:     getEnv("REDIS_HOST", "localhost"),
            Port:     getEnvAsInt("REDIS_PORT", 6379),
            Password: getEnv("REDIS_PASSWORD", ""),
            DB:       getEnvAsInt("REDIS_DB", 0),
        },
        JWT: JWTConfig{
            Secret:    getEnv("JWT_SECRET", "secret"),
            ExpiresIn: getEnvAsDuration("JWT_EXPIRES_IN", 24*time.Hour),
        },
    }
}

func getEnv(key, defaultValue string) string {
    if value := os.Getenv(key); value != "" {
        return value
    }
    return defaultValue
}

func getEnvAsInt(key string, defaultValue int) int {
    if value := os.Getenv(key); value != "" {
        if i, err := strconv.Atoi(value); err == nil {
            return i
        }
    }
    return defaultValue
}

func getEnvAsBool(key string, defaultValue bool) bool {
    if value := os.Getenv(key); value != "" {
        if b, err := strconv.ParseBool(value); err == nil {
            return b
        }
    }
    return defaultValue
}

func getEnvAsDuration(key string, defaultValue time.Duration) time.Duration {
    if value := os.Getenv(key); value != "" {
        if d, err := time.ParseDuration(value); err == nil {
            return d
        }
    }
    return defaultValue
}
```

### Using Viper

```bash
go get github.com/spf13/viper
```

```go
package config

import (
    "github.com/spf13/viper"
)

func LoadWithViper() (*Config, error) {
    viper.SetConfigName("config")
    viper.SetConfigType("yaml")
    viper.AddConfigPath(".")
    viper.AddConfigPath("./config")
    
    // Environment variables
    viper.AutomaticEnv()
    viper.SetEnvPrefix("APP")
    
    // Defaults
    viper.SetDefault("app.port", 8080)
    viper.SetDefault("app.env", "development")
    
    if err := viper.ReadInConfig(); err != nil {
        if _, ok := err.(viper.ConfigFileNotFoundError); !ok {
            return nil, err
        }
    }
    
    var config Config
    if err := viper.Unmarshal(&config); err != nil {
        return nil, err
    }
    
    return &config, nil
}
```

```yaml
# config.yaml
app:
  name: myapp
  port: 8080
  env: production
  debug: false

database:
  host: localhost
  port: 5432
  user: postgres
  password: secret
  name: myapp

redis:
  host: localhost
  port: 6379
```

---

## 4️⃣ SENIOR LEVEL - Health Checks

### Health Check Endpoints

```go
// handler/health.go
package handler

import (
    "net/http"
    "time"
    
    "github.com/gin-gonic/gin"
    "gorm.io/gorm"
    "github.com/redis/go-redis/v9"
)

type HealthHandler struct {
    db    *gorm.DB
    redis *redis.Client
}

func NewHealthHandler(db *gorm.DB, redis *redis.Client) *HealthHandler {
    return &HealthHandler{db: db, redis: redis}
}

type HealthResponse struct {
    Status    string            `json:"status"`
    Timestamp time.Time         `json:"timestamp"`
    Version   string            `json:"version"`
    Services  map[string]string `json:"services"`
}

// Liveness probe - is the app running?
func (h *HealthHandler) Liveness(c *gin.Context) {
    c.JSON(http.StatusOK, gin.H{
        "status":    "alive",
        "timestamp": time.Now(),
    })
}

// Readiness probe - is the app ready to receive traffic?
func (h *HealthHandler) Readiness(c *gin.Context) {
    services := make(map[string]string)
    status := http.StatusOK
    
    // Check database
    sqlDB, err := h.db.DB()
    if err != nil {
        services["database"] = "unhealthy: " + err.Error()
        status = http.StatusServiceUnavailable
    } else if err = sqlDB.Ping(); err != nil {
        services["database"] = "unhealthy: " + err.Error()
        status = http.StatusServiceUnavailable
    } else {
        services["database"] = "healthy"
    }
    
    // Check Redis
    ctx := c.Request.Context()
    if _, err := h.redis.Ping(ctx).Result(); err != nil {
        services["redis"] = "unhealthy: " + err.Error()
        status = http.StatusServiceUnavailable
    } else {
        services["redis"] = "healthy"
    }
    
    overallStatus := "healthy"
    if status != http.StatusOK {
        overallStatus = "unhealthy"
    }
    
    c.JSON(status, HealthResponse{
        Status:    overallStatus,
        Timestamp: time.Now(),
        Version:   Version,
        Services:  services,
    })
}

// Startup probe - has the app started successfully?
func (h *HealthHandler) Startup(c *gin.Context) {
    // Check if all dependencies are initialized
    if h.db == nil || h.redis == nil {
        c.JSON(http.StatusServiceUnavailable, gin.H{
            "status": "starting",
        })
        return
    }
    
    c.JSON(http.StatusOK, gin.H{
        "status": "started",
    })
}
```

### Register Health Routes

```go
// router/router.go
func SetupRouter(db *gorm.DB, redis *redis.Client) *gin.Engine {
    r := gin.New()
    
    healthHandler := handler.NewHealthHandler(db, redis)
    
    // Health check endpoints (no auth)
    r.GET("/health", healthHandler.Liveness)
    r.GET("/health/live", healthHandler.Liveness)
    r.GET("/health/ready", healthHandler.Readiness)
    r.GET("/health/startup", healthHandler.Startup)
    
    // ... other routes
    
    return r
}
```

---

## 5️⃣ SENIOR LEVEL - Graceful Shutdown

### Complete Graceful Shutdown

```go
// cmd/api/main.go
package main

import (
    "context"
    "net/http"
    "os"
    "os/signal"
    "syscall"
    "time"
    
    "github.com/rs/zerolog/log"
)

func main() {
    // Load config
    cfg := config.Load()
    
    // Initialize dependencies
    db := database.Connect(cfg.Database)
    redis := redis.NewClient(cfg.Redis)
    
    // Setup router
    router := SetupRouter(db, redis)
    
    // Create server
    server := &http.Server{
        Addr:         fmt.Sprintf(":%d", cfg.App.Port),
        Handler:      router,
        ReadTimeout:  10 * time.Second,
        WriteTimeout: 30 * time.Second,
        IdleTimeout:  60 * time.Second,
    }
    
    // Channel for shutdown signals
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    
    // Start server in goroutine
    go func() {
        log.Info().Msgf("Starting server on port %d", cfg.App.Port)
        if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
            log.Fatal().Err(err).Msg("Server failed to start")
        }
    }()
    
    // Wait for shutdown signal
    <-quit
    log.Info().Msg("Shutting down server...")
    
    // Create shutdown context with timeout
    ctx, cancel := context.WithTimeout(context.Background(), cfg.App.GracefulTimeout)
    defer cancel()
    
    // Shutdown server
    if err := server.Shutdown(ctx); err != nil {
        log.Error().Err(err).Msg("Server forced to shutdown")
    }
    
    // Close database connection
    if sqlDB, err := db.DB(); err == nil {
        sqlDB.Close()
    }
    
    // Close Redis connection
    redis.Close()
    
    log.Info().Msg("Server exited properly")
}
```

### With Background Workers

```go
package main

import (
    "context"
    "sync"
)

type App struct {
    server     *http.Server
    db         *gorm.DB
    redis      *redis.Client
    workers    []Worker
    wg         sync.WaitGroup
}

type Worker interface {
    Start(ctx context.Context)
    Stop()
}

func (app *App) Start() {
    ctx, cancel := context.WithCancel(context.Background())
    
    // Start workers
    for _, worker := range app.workers {
        app.wg.Add(1)
        go func(w Worker) {
            defer app.wg.Done()
            w.Start(ctx)
        }(worker)
    }
    
    // Start server
    go func() {
        if err := app.server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
            log.Fatal().Err(err).Msg("Server failed")
        }
    }()
    
    // Wait for shutdown
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit
    
    log.Info().Msg("Shutting down...")
    
    // Cancel worker context
    cancel()
    
    // Shutdown server
    shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer shutdownCancel()
    
    app.server.Shutdown(shutdownCtx)
    
    // Wait for workers to finish
    app.wg.Wait()
    
    // Cleanup
    app.cleanup()
    
    log.Info().Msg("Shutdown complete")
}

func (app *App) cleanup() {
    if sqlDB, err := app.db.DB(); err == nil {
        sqlDB.Close()
    }
    app.redis.Close()
}
```

---

## 6️⃣ EXPERT LEVEL - Kubernetes Deployment

### Kubernetes Manifests

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-api
  labels:
    app: myapp-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp-api
  template:
    metadata:
      labels:
        app: myapp-api
    spec:
      containers:
        - name: api
          image: myapp:latest
          ports:
            - containerPort: 8080
          env:
            - name: APP_ENV
              value: production
            - name: DB_HOST
              valueFrom:
                secretKeyRef:
                  name: myapp-secrets
                  key: db-host
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: myapp-secrets
                  key: db-password
          resources:
            requests:
              memory: "64Mi"
              cpu: "50m"
            limits:
              memory: "256Mi"
              cpu: "200m"
          livenessProbe:
            httpGet:
              path: /health/live
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 5
          startupProbe:
            httpGet:
              path: /health/startup
              port: 8080
            failureThreshold: 30
            periodSeconds: 10
      terminationGracePeriodSeconds: 30
---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp-api
spec:
  selector:
    app: myapp-api
  ports:
    - port: 80
      targetPort: 8080
  type: ClusterIP
---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
    - hosts:
        - api.myapp.com
      secretName: myapp-tls
  rules:
    - host: api.myapp.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: myapp-api
                port:
                  number: 80
```

### ConfigMap and Secrets

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: myapp-config
data:
  APP_ENV: production
  APP_PORT: "8080"
  LOG_LEVEL: info
---
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: myapp-secrets
type: Opaque
stringData:
  db-host: postgres.database.svc.cluster.local
  db-password: supersecret
  jwt-secret: myjwtsecret
```

### Horizontal Pod Autoscaler

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: myapp-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

---

## 7️⃣ EXPERT LEVEL - CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Build and Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Go
        uses: actions/setup-go@v5
        with:
          go-version: '1.21'
      
      - name: Cache Go modules
        uses: actions/cache@v3
        with:
          path: ~/go/pkg/mod
          key: ${{ runner.os }}-go-${{ hashFiles('**/go.sum') }}
          restore-keys: |
            ${{ runner.os }}-go-
      
      - name: Run tests
        run: go test -v -race -coverprofile=coverage.out ./...
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.out

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha,prefix=
            type=raw,value=latest
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up kubectl
        uses: azure/setup-kubectl@v3
      
      - name: Configure kubectl
        run: |
          echo "${{ secrets.KUBE_CONFIG }}" | base64 -d > kubeconfig.yaml
          export KUBECONFIG=kubeconfig.yaml
      
      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/myapp-api \
            api=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          kubectl rollout status deployment/myapp-api
```

---

## 8️⃣ EXPERT LEVEL - Makefile

### Complete Makefile

```makefile
# Makefile
.PHONY: all build run test clean docker deploy

# Variables
APP_NAME := myapp
VERSION := $(shell git describe --tags --always --dirty)
BUILD_TIME := $(shell date -u +%Y%m%d%H%M%S)
LDFLAGS := -ldflags "-s -w -X main.Version=$(VERSION) -X main.BuildTime=$(BUILD_TIME)"

# Default target
all: build

# Build binary
build:
	@echo "Building $(APP_NAME)..."
	go build $(LDFLAGS) -o bin/$(APP_NAME) ./cmd/api

# Build for all platforms
build-all:
	@echo "Building for all platforms..."
	GOOS=linux GOARCH=amd64 go build $(LDFLAGS) -o bin/$(APP_NAME)-linux-amd64 ./cmd/api
	GOOS=linux GOARCH=arm64 go build $(LDFLAGS) -o bin/$(APP_NAME)-linux-arm64 ./cmd/api
	GOOS=darwin GOARCH=amd64 go build $(LDFLAGS) -o bin/$(APP_NAME)-darwin-amd64 ./cmd/api
	GOOS=darwin GOARCH=arm64 go build $(LDFLAGS) -o bin/$(APP_NAME)-darwin-arm64 ./cmd/api
	GOOS=windows GOARCH=amd64 go build $(LDFLAGS) -o bin/$(APP_NAME)-windows-amd64.exe ./cmd/api

# Run locally
run:
	go run ./cmd/api

# Run with hot reload
dev:
	air

# Run tests
test:
	go test -v -race ./...

# Run tests with coverage
test-coverage:
	go test -v -race -coverprofile=coverage.out ./...
	go tool cover -html=coverage.out -o coverage.html

# Run linter
lint:
	golangci-lint run

# Format code
fmt:
	go fmt ./...
	goimports -w .

# Tidy dependencies
tidy:
	go mod tidy
	go mod verify

# Clean build artifacts
clean:
	rm -rf bin/
	rm -f coverage.out coverage.html

# Docker build
docker-build:
	docker build -t $(APP_NAME):$(VERSION) .
	docker tag $(APP_NAME):$(VERSION) $(APP_NAME):latest

# Docker run
docker-run:
	docker run -p 8080:8080 $(APP_NAME):latest

# Docker compose up
up:
	docker-compose up -d

# Docker compose down
down:
	docker-compose down

# Database migrate
migrate-up:
	migrate -path migrations -database "$(DATABASE_URL)" up

migrate-down:
	migrate -path migrations -database "$(DATABASE_URL)" down 1

migrate-create:
	migrate create -ext sql -dir migrations -seq $(name)

# Generate swagger docs
swagger:
	swag init -g cmd/api/main.go -o docs

# Generate mocks
mocks:
	mockgen -source=internal/repository/user_repository.go -destination=mocks/user_repository_mock.go

# Help
help:
	@echo "Available targets:"
	@echo "  build         - Build the application"
	@echo "  build-all     - Build for all platforms"
	@echo "  run           - Run the application"
	@echo "  dev           - Run with hot reload"
	@echo "  test          - Run tests"
	@echo "  test-coverage - Run tests with coverage"
	@echo "  lint          - Run linter"
	@echo "  fmt           - Format code"
	@echo "  clean         - Clean build artifacts"
	@echo "  docker-build  - Build Docker image"
	@echo "  docker-run    - Run Docker container"
	@echo "  up            - Start with docker-compose"
	@echo "  down          - Stop docker-compose"
	@echo "  migrate-up    - Run database migrations"
	@echo "  migrate-down  - Rollback last migration"
	@echo "  swagger       - Generate swagger docs"
```

---

## 📊 Deployment Checklist

### Pre-Deployment

| Item | Description |
|------|-------------|
| ✅ Tests passing | All unit/integration tests pass |
| ✅ Linting clean | No linter warnings |
| ✅ Security scan | No vulnerabilities in deps |
| ✅ Config review | Environment variables set |
| ✅ Database migrations | Ready to apply |

### Production Ready

| Feature | Implementation |
|---------|----------------|
| Health checks | `/health/live`, `/health/ready` |
| Graceful shutdown | Signal handling |
| Logging | Structured JSON logs |
| Metrics | Prometheus endpoint |
| Error handling | Proper error responses |
| Rate limiting | Prevent abuse |
| CORS | Configured properly |

---

## 💡 Summary

| Level | Focus |
|-------|-------|
| **Junior** | Basic build, cross-compilation |
| **Mid** | Docker, docker-compose |
| **Mid-Senior** | Config management, Viper |
| **Senior** | Health checks, graceful shutdown |
| **Expert** | Kubernetes, CI/CD, Makefile |

**Best Practices:**
- ✅ Use multi-stage Docker builds
- ✅ Implement health checks
- ✅ Graceful shutdown with timeout
- ✅ Environment-based configuration
- ✅ Automated CI/CD pipeline
- ✅ Version injection at build time
- ❌ Don't hardcode secrets
- ❌ Don't run as root in containers
- ❌ Don't skip readiness probes
