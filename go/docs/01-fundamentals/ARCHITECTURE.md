# 🏗️ ARCHITECTURE - Go Project Structure (Junior → Senior)

Dokumentasi lengkap tentang arsitektur dan struktur project Go.

---

## 🎯 Go Project Layout Standards

```
Ada 2 pendekatan umum:

1. Flat Structure (Simple apps)
   - Semua di root folder
   - Untuk learning/small projects

2. Standard Layout (Production apps)
   - Folder terstruktur
   - Scalable, maintainable
```

---

## 1️⃣ JUNIOR LEVEL - Flat Structure

### Minimal Project

```
myapp/
├── go.mod          # Module definition
├── go.sum          # Dependency checksums
├── main.go         # Entry point
├── handlers.go     # HTTP handlers
├── models.go       # Data structures
└── README.md
```

```go
// go.mod
module github.com/username/myapp

go 1.21

require (
    github.com/gin-gonic/gin v1.9.1
)
```

```go
// main.go
package main

import (
    "log"
    
    "github.com/gin-gonic/gin"
)

func main() {
    r := gin.Default()
    
    r.GET("/health", HealthHandler)
    r.GET("/users", GetUsersHandler)
    r.POST("/users", CreateUserHandler)
    
    log.Fatal(r.Run(":8080"))
}
```

```go
// models.go
package main

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
```

```go
// handlers.go
package main

import (
    "net/http"
    
    "github.com/gin-gonic/gin"
)

func HealthHandler(c *gin.Context) {
    c.JSON(http.StatusOK, Response{
        Success: true,
        Message: "OK",
    })
}

func GetUsersHandler(c *gin.Context) {
    users := []User{
        {ID: 1, Name: "John", Email: "john@example.com"},
        {ID: 2, Name: "Jane", Email: "jane@example.com"},
    }
    
    c.JSON(http.StatusOK, Response{
        Success: true,
        Data:    users,
    })
}

func CreateUserHandler(c *gin.Context) {
    var user User
    if err := c.ShouldBindJSON(&user); err != nil {
        c.JSON(http.StatusBadRequest, Response{
            Success: false,
            Message: err.Error(),
        })
        return
    }
    
    // Save to database...
    
    c.JSON(http.StatusCreated, Response{
        Success: true,
        Data:    user,
    })
}
```

---

## 2️⃣ MID LEVEL - Standard Layout

### Recommended Project Structure

```
myapp/
├── cmd/                    # Application entry points
│   └── api/
│       └── main.go
├── internal/               # Private application code
│   ├── config/
│   │   └── config.go
│   ├── handlers/
│   │   ├── health.go
│   │   ├── user.go
│   │   └── task.go
│   ├── models/
│   │   ├── user.go
│   │   └── task.go
│   ├── repository/
│   │   ├── user_repository.go
│   │   └── task_repository.go
│   ├── services/
│   │   ├── user_service.go
│   │   └── task_service.go
│   └── middleware/
│       ├── auth.go
│       └── logging.go
├── pkg/                    # Public packages (reusable)
│   ├── response/
│   │   └── response.go
│   └── validator/
│       └── validator.go
├── migrations/             # Database migrations
│   ├── 001_create_users.up.sql
│   └── 001_create_users.down.sql
├── scripts/                # Build/deploy scripts
│   └── migrate.sh
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── go.mod
├── go.sum
└── README.md
```

### Penjelasan Folder

```
cmd/            → Entry points (main.go)
                  Bisa multiple: cmd/api/, cmd/worker/, cmd/cli/

internal/       → Private code (tidak bisa di-import dari luar)
                  Ini CONVENTION dari Go!

pkg/            → Public packages (bisa di-import dari luar)
                  Untuk reusable utilities

internal/config/     → Configuration loading
internal/handlers/   → HTTP handlers (Controller di MVC)
internal/models/     → Data structures (Entity)
internal/repository/ → Database operations (Data Access)
internal/services/   → Business logic
internal/middleware/ → HTTP middleware
```

### Implementation Example

```go
// cmd/api/main.go
package main

import (
    "log"
    
    "github.com/username/myapp/internal/config"
    "github.com/username/myapp/internal/handlers"
    "github.com/username/myapp/internal/middleware"
    "github.com/username/myapp/internal/repository"
    "github.com/username/myapp/internal/services"
    
    "github.com/gin-gonic/gin"
)

func main() {
    // Load config
    cfg := config.Load()
    
    // Initialize database
    db := config.NewDatabase(cfg)
    
    // Initialize layers
    userRepo := repository.NewUserRepository(db)
    userService := services.NewUserService(userRepo)
    userHandler := handlers.NewUserHandler(userService)
    
    // Setup router
    r := gin.Default()
    
    // Middleware
    r.Use(middleware.Logger())
    r.Use(middleware.ErrorHandler())
    
    // Routes
    api := r.Group("/api/v1")
    {
        api.GET("/health", handlers.HealthCheck)
        
        users := api.Group("/users")
        {
            users.GET("", userHandler.List)
            users.GET("/:id", userHandler.Get)
            users.POST("", userHandler.Create)
            users.PUT("/:id", userHandler.Update)
            users.DELETE("/:id", userHandler.Delete)
        }
    }
    
    log.Printf("Server starting on port %s", cfg.Port)
    log.Fatal(r.Run(":" + cfg.Port))
}
```

```go
// internal/config/config.go
package config

import (
    "os"
    
    "github.com/joho/godotenv"
)

type Config struct {
    Port        string
    DatabaseURL string
    JWTSecret   string
    Environment string
}

func Load() *Config {
    godotenv.Load()
    
    return &Config{
        Port:        getEnv("PORT", "8080"),
        DatabaseURL: getEnv("DATABASE_URL", ""),
        JWTSecret:   getEnv("JWT_SECRET", "secret"),
        Environment: getEnv("ENVIRONMENT", "development"),
    }
}

func getEnv(key, defaultValue string) string {
    if value := os.Getenv(key); value != "" {
        return value
    }
    return defaultValue
}
```

```go
// internal/models/user.go
package models

import "time"

type User struct {
    ID        uint      `json:"id" gorm:"primaryKey"`
    Name      string    `json:"name" gorm:"size:100;not null"`
    Email     string    `json:"email" gorm:"uniqueIndex;not null"`
    Password  string    `json:"-" gorm:"not null"` // - = hide from JSON
    CreatedAt time.Time `json:"created_at"`
    UpdatedAt time.Time `json:"updated_at"`
}

// DTO (Data Transfer Object) for input
type CreateUserRequest struct {
    Name     string `json:"name" binding:"required,min=2,max=100"`
    Email    string `json:"email" binding:"required,email"`
    Password string `json:"password" binding:"required,min=6"`
}

type UpdateUserRequest struct {
    Name  string `json:"name" binding:"omitempty,min=2,max=100"`
    Email string `json:"email" binding:"omitempty,email"`
}
```

```go
// internal/repository/user_repository.go
package repository

import (
    "github.com/username/myapp/internal/models"
    "gorm.io/gorm"
)

type UserRepository interface {
    FindAll() ([]models.User, error)
    FindByID(id uint) (*models.User, error)
    FindByEmail(email string) (*models.User, error)
    Create(user *models.User) error
    Update(user *models.User) error
    Delete(id uint) error
}

type userRepository struct {
    db *gorm.DB
}

func NewUserRepository(db *gorm.DB) UserRepository {
    return &userRepository{db: db}
}

func (r *userRepository) FindAll() ([]models.User, error) {
    var users []models.User
    err := r.db.Find(&users).Error
    return users, err
}

func (r *userRepository) FindByID(id uint) (*models.User, error) {
    var user models.User
    err := r.db.First(&user, id).Error
    if err != nil {
        return nil, err
    }
    return &user, nil
}

func (r *userRepository) FindByEmail(email string) (*models.User, error) {
    var user models.User
    err := r.db.Where("email = ?", email).First(&user).Error
    if err != nil {
        return nil, err
    }
    return &user, nil
}

func (r *userRepository) Create(user *models.User) error {
    return r.db.Create(user).Error
}

func (r *userRepository) Update(user *models.User) error {
    return r.db.Save(user).Error
}

func (r *userRepository) Delete(id uint) error {
    return r.db.Delete(&models.User{}, id).Error
}
```

```go
// internal/services/user_service.go
package services

import (
    "errors"
    
    "github.com/username/myapp/internal/models"
    "github.com/username/myapp/internal/repository"
    "golang.org/x/crypto/bcrypt"
)

var (
    ErrUserNotFound = errors.New("user not found")
    ErrEmailExists  = errors.New("email already exists")
)

type UserService interface {
    GetAll() ([]models.User, error)
    GetByID(id uint) (*models.User, error)
    Create(req *models.CreateUserRequest) (*models.User, error)
    Update(id uint, req *models.UpdateUserRequest) (*models.User, error)
    Delete(id uint) error
}

type userService struct {
    repo repository.UserRepository
}

func NewUserService(repo repository.UserRepository) UserService {
    return &userService{repo: repo}
}

func (s *userService) GetAll() ([]models.User, error) {
    return s.repo.FindAll()
}

func (s *userService) GetByID(id uint) (*models.User, error) {
    user, err := s.repo.FindByID(id)
    if err != nil {
        return nil, ErrUserNotFound
    }
    return user, nil
}

func (s *userService) Create(req *models.CreateUserRequest) (*models.User, error) {
    // Check if email exists
    existing, _ := s.repo.FindByEmail(req.Email)
    if existing != nil {
        return nil, ErrEmailExists
    }
    
    // Hash password
    hashedPassword, err := bcrypt.GenerateFromPassword(
        []byte(req.Password), 
        bcrypt.DefaultCost,
    )
    if err != nil {
        return nil, err
    }
    
    user := &models.User{
        Name:     req.Name,
        Email:    req.Email,
        Password: string(hashedPassword),
    }
    
    if err := s.repo.Create(user); err != nil {
        return nil, err
    }
    
    return user, nil
}

func (s *userService) Update(id uint, req *models.UpdateUserRequest) (*models.User, error) {
    user, err := s.repo.FindByID(id)
    if err != nil {
        return nil, ErrUserNotFound
    }
    
    if req.Name != "" {
        user.Name = req.Name
    }
    if req.Email != "" {
        user.Email = req.Email
    }
    
    if err := s.repo.Update(user); err != nil {
        return nil, err
    }
    
    return user, nil
}

func (s *userService) Delete(id uint) error {
    _, err := s.repo.FindByID(id)
    if err != nil {
        return ErrUserNotFound
    }
    
    return s.repo.Delete(id)
}
```

```go
// internal/handlers/user.go
package handlers

import (
    "net/http"
    "strconv"
    
    "github.com/username/myapp/internal/models"
    "github.com/username/myapp/internal/services"
    "github.com/username/myapp/pkg/response"
    
    "github.com/gin-gonic/gin"
)

type UserHandler struct {
    service services.UserService
}

func NewUserHandler(service services.UserService) *UserHandler {
    return &UserHandler{service: service}
}

func (h *UserHandler) List(c *gin.Context) {
    users, err := h.service.GetAll()
    if err != nil {
        response.Error(c, http.StatusInternalServerError, err.Error())
        return
    }
    
    response.Success(c, http.StatusOK, "Users retrieved", users)
}

func (h *UserHandler) Get(c *gin.Context) {
    id, err := strconv.ParseUint(c.Param("id"), 10, 32)
    if err != nil {
        response.Error(c, http.StatusBadRequest, "Invalid ID")
        return
    }
    
    user, err := h.service.GetByID(uint(id))
    if err != nil {
        if err == services.ErrUserNotFound {
            response.Error(c, http.StatusNotFound, err.Error())
            return
        }
        response.Error(c, http.StatusInternalServerError, err.Error())
        return
    }
    
    response.Success(c, http.StatusOK, "User retrieved", user)
}

func (h *UserHandler) Create(c *gin.Context) {
    var req models.CreateUserRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        response.Error(c, http.StatusBadRequest, err.Error())
        return
    }
    
    user, err := h.service.Create(&req)
    if err != nil {
        if err == services.ErrEmailExists {
            response.Error(c, http.StatusConflict, err.Error())
            return
        }
        response.Error(c, http.StatusInternalServerError, err.Error())
        return
    }
    
    response.Success(c, http.StatusCreated, "User created", user)
}

func (h *UserHandler) Update(c *gin.Context) {
    id, err := strconv.ParseUint(c.Param("id"), 10, 32)
    if err != nil {
        response.Error(c, http.StatusBadRequest, "Invalid ID")
        return
    }
    
    var req models.UpdateUserRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        response.Error(c, http.StatusBadRequest, err.Error())
        return
    }
    
    user, err := h.service.Update(uint(id), &req)
    if err != nil {
        if err == services.ErrUserNotFound {
            response.Error(c, http.StatusNotFound, err.Error())
            return
        }
        response.Error(c, http.StatusInternalServerError, err.Error())
        return
    }
    
    response.Success(c, http.StatusOK, "User updated", user)
}

func (h *UserHandler) Delete(c *gin.Context) {
    id, err := strconv.ParseUint(c.Param("id"), 10, 32)
    if err != nil {
        response.Error(c, http.StatusBadRequest, "Invalid ID")
        return
    }
    
    if err := h.service.Delete(uint(id)); err != nil {
        if err == services.ErrUserNotFound {
            response.Error(c, http.StatusNotFound, err.Error())
            return
        }
        response.Error(c, http.StatusInternalServerError, err.Error())
        return
    }
    
    response.Success(c, http.StatusOK, "User deleted", nil)
}
```

```go
// pkg/response/response.go
package response

import "github.com/gin-gonic/gin"

type APIResponse struct {
    Success bool        `json:"success"`
    Message string      `json:"message"`
    Data    interface{} `json:"data,omitempty"`
    Error   string      `json:"error,omitempty"`
}

func Success(c *gin.Context, statusCode int, message string, data interface{}) {
    c.JSON(statusCode, APIResponse{
        Success: true,
        Message: message,
        Data:    data,
    })
}

func Error(c *gin.Context, statusCode int, message string) {
    c.JSON(statusCode, APIResponse{
        Success: false,
        Error:   message,
    })
}
```

---

## 3️⃣ MID-SENIOR LEVEL - Clean Architecture

### Dependency Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Clean Architecture                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   HTTP Request                                               │
│        │                                                     │
│        ▼                                                     │
│   ┌─────────────┐                                            │
│   │  Handlers   │  ← Presentation Layer (HTTP)               │
│   │ (Delivery)  │                                            │
│   └──────┬──────┘                                            │
│          │ depends on                                        │
│          ▼                                                   │
│   ┌─────────────┐                                            │
│   │  Services   │  ← Business Logic Layer                    │
│   │  (Usecase)  │                                            │
│   └──────┬──────┘                                            │
│          │ depends on                                        │
│          ▼                                                   │
│   ┌─────────────┐                                            │
│   │ Repository  │  ← Data Access Layer                       │
│   │   (Data)    │                                            │
│   └──────┬──────┘                                            │
│          │                                                   │
│          ▼                                                   │
│   ┌─────────────┐                                            │
│   │  Database   │  ← Infrastructure                          │
│   └─────────────┘                                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘

RULE: Dependencies point INWARD
      Inner layers don't know outer layers
```

### Folder Structure (Clean)

```
myapp/
├── cmd/
│   └── api/
│       └── main.go
├── internal/
│   ├── domain/              # Core business entities
│   │   ├── user.go
│   │   └── task.go
│   ├── usecase/             # Business logic
│   │   ├── user/
│   │   │   ├── interface.go
│   │   │   └── service.go
│   │   └── task/
│   │       ├── interface.go
│   │       └── service.go
│   ├── repository/          # Data access interface
│   │   ├── user/
│   │   │   ├── interface.go
│   │   │   └── postgres.go
│   │   └── task/
│   │       ├── interface.go
│   │       └── postgres.go
│   └── delivery/            # HTTP/gRPC handlers
│       └── http/
│           ├── router.go
│           ├── middleware/
│           └── handler/
│               ├── user.go
│               └── task.go
├── pkg/
└── ...
```

```go
// internal/domain/user.go
package domain

import (
    "errors"
    "time"
)

// Entity (Core business object)
type User struct {
    ID        uint
    Name      string
    Email     string
    Password  string
    CreatedAt time.Time
    UpdatedAt time.Time
}

// Value Objects
type Email string

func NewEmail(email string) (Email, error) {
    if email == "" {
        return "", errors.New("email cannot be empty")
    }
    // Add more validation...
    return Email(email), nil
}

// Domain Errors
var (
    ErrUserNotFound     = errors.New("user not found")
    ErrInvalidEmail     = errors.New("invalid email")
    ErrEmailExists      = errors.New("email already exists")
    ErrInvalidPassword  = errors.New("invalid password")
)
```

```go
// internal/usecase/user/interface.go
package user

import (
    "context"
    
    "github.com/username/myapp/internal/domain"
)

// Service interface (what the usecase can do)
type Service interface {
    GetAll(ctx context.Context) ([]domain.User, error)
    GetByID(ctx context.Context, id uint) (*domain.User, error)
    Create(ctx context.Context, req *CreateRequest) (*domain.User, error)
    Update(ctx context.Context, id uint, req *UpdateRequest) (*domain.User, error)
    Delete(ctx context.Context, id uint) error
}

// Repository interface (what the usecase needs from data layer)
type Repository interface {
    FindAll(ctx context.Context) ([]domain.User, error)
    FindByID(ctx context.Context, id uint) (*domain.User, error)
    FindByEmail(ctx context.Context, email string) (*domain.User, error)
    Create(ctx context.Context, user *domain.User) error
    Update(ctx context.Context, user *domain.User) error
    Delete(ctx context.Context, id uint) error
}

// DTOs
type CreateRequest struct {
    Name     string
    Email    string
    Password string
}

type UpdateRequest struct {
    Name  string
    Email string
}
```

---

## 4️⃣ SENIOR LEVEL - Dependency Injection

### Wire (Google Wire)

```go
// cmd/api/wire.go
//go:build wireinject
// +build wireinject

package main

import (
    "github.com/google/wire"
    
    "github.com/username/myapp/internal/config"
    "github.com/username/myapp/internal/delivery/http"
    userHandler "github.com/username/myapp/internal/delivery/http/handler"
    userRepo "github.com/username/myapp/internal/repository/user"
    userUsecase "github.com/username/myapp/internal/usecase/user"
)

func InitializeApp(cfg *config.Config) (*http.Server, error) {
    wire.Build(
        config.NewDatabase,
        
        // User
        userRepo.NewPostgresRepository,
        userUsecase.NewService,
        userHandler.NewHandler,
        
        // Task
        // ...
        
        http.NewServer,
    )
    
    return &http.Server{}, nil
}
```

### Manual DI (Simpler)

```go
// cmd/api/main.go
package main

import (
    "log"
    
    "github.com/username/myapp/internal/config"
    "github.com/username/myapp/internal/delivery/http"
    userHandler "github.com/username/myapp/internal/delivery/http/handler"
    userRepo "github.com/username/myapp/internal/repository/user"
    userUsecase "github.com/username/myapp/internal/usecase/user"
)

func main() {
    // Config
    cfg := config.Load()
    
    // Database
    db := config.NewDatabase(cfg)
    
    // User module
    userRepository := userRepo.NewPostgresRepository(db)
    userService := userUsecase.NewService(userRepository)
    userHandler := userHandler.NewHandler(userService)
    
    // Task module
    // ...
    
    // HTTP Server
    server := http.NewServer(cfg, userHandler /* , taskHandler */)
    
    log.Printf("Server starting on :%s", cfg.Port)
    log.Fatal(server.Run())
}
```

---

## 5️⃣ SENIOR LEVEL - Makefile

```makefile
# Makefile

.PHONY: help build run test clean migrate

# Variables
APP_NAME := myapp
BUILD_DIR := ./bin
MAIN_PATH := ./cmd/api

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build the application
	go build -o $(BUILD_DIR)/$(APP_NAME) $(MAIN_PATH)

run: ## Run the application
	go run $(MAIN_PATH)/main.go

dev: ## Run with hot reload (requires air)
	air

test: ## Run tests
	go test -v ./...

test-coverage: ## Run tests with coverage
	go test -v -cover -coverprofile=coverage.out ./...
	go tool cover -html=coverage.out -o coverage.html

lint: ## Run linter (requires golangci-lint)
	golangci-lint run

clean: ## Clean build artifacts
	rm -rf $(BUILD_DIR)
	rm -f coverage.out coverage.html

migrate-up: ## Run database migrations
	migrate -path migrations -database "$(DATABASE_URL)" up

migrate-down: ## Rollback database migrations
	migrate -path migrations -database "$(DATABASE_URL)" down 1

migrate-create: ## Create new migration (usage: make migrate-create name=create_users)
	migrate create -ext sql -dir migrations -seq $(name)

docker-build: ## Build Docker image
	docker build -t $(APP_NAME):latest .

docker-run: ## Run Docker container
	docker-compose up -d

docker-stop: ## Stop Docker container
	docker-compose down

swagger: ## Generate Swagger docs
	swag init -g cmd/api/main.go -o docs

.DEFAULT_GOAL := help
```

---

## 📊 Architecture Comparison

| Pattern | Complexity | Use Case |
|---------|------------|----------|
| **Flat** | Low | Learning, scripts, small tools |
| **Standard Layout** | Medium | Medium apps, startups |
| **Clean Architecture** | High | Enterprise, large teams |
| **Hexagonal** | High | Complex domains |

### Layer Responsibilities

| Layer | Responsibility | Go Package |
|-------|----------------|------------|
| Delivery | HTTP, gRPC, CLI | `internal/delivery/` |
| Usecase | Business logic | `internal/usecase/` |
| Repository | Data access | `internal/repository/` |
| Domain | Entities, rules | `internal/domain/` |

---

## 💡 Summary

| Level | Focus |
|-------|-------|
| **Junior** | Flat structure, basic handlers |
| **Mid** | Standard layout, layered architecture |
| **Mid-Senior** | Clean architecture, interfaces |
| **Senior** | DI, Wire, Makefile |
| **Expert** | Domain-driven design |

**Best Practices:**
- ✅ Start simple, refactor when needed
- ✅ Use `internal/` for private packages
- ✅ Depend on interfaces, not implementations
- ✅ Keep `main.go` thin (wire up dependencies only)
- ✅ Use Makefile for common tasks
- ❌ Don't over-engineer for small projects
- ❌ Don't copy-paste structure without understanding
