# 📁 STRUKTUR FOLDER - Go Project Structure

Best practices untuk mengorganisir project Go dari small hingga large scale.

---

## 🎯 Overview

```
Go memiliki konvensi yang cukup ketat untuk struktur folder.
Standard yang paling populer mengikuti "Standard Go Project Layout".
```

---

## 1️⃣ SMALL PROJECT (Simple CLI/Library)

Untuk project kecil atau library:

```
my_project/
├── go.mod
├── go.sum
├── main.go                     # Entry point
├── README.md
├── .gitignore
│
├── config.go                   # Configuration
├── handler.go                  # HTTP handlers (jika API)
├── model.go                    # Data models
├── service.go                  # Business logic
├── repository.go               # Database access
│
└── utils/                      # Utility functions
    └── helpers.go
```

Untuk library sederhana:

```
my_library/
├── go.mod
├── go.sum
├── README.md
├── LICENSE
├── .gitignore
│
├── library.go                  # Main library code
├── library_test.go             # Tests
├── options.go                  # Options/config
└── errors.go                   # Custom errors
```

---

## 2️⃣ MEDIUM PROJECT (Standard API)

Untuk REST API dengan beberapa domain:

```
my_api/
├── go.mod
├── go.sum
├── README.md
├── Makefile
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
│
├── cmd/                        # Application entry points
│   └── api/
│       └── main.go             # API server entry
│
├── internal/                   # Private application code
│   ├── config/
│   │   └── config.go           # Configuration loading
│   │
│   ├── handler/                # HTTP handlers
│   │   ├── handler.go          # Handler struct
│   │   ├── user_handler.go
│   │   ├── product_handler.go
│   │   └── middleware.go
│   │
│   ├── model/                  # Domain models
│   │   ├── user.go
│   │   ├── product.go
│   │   └── order.go
│   │
│   ├── repository/             # Database layer
│   │   ├── repository.go       # Interface definitions
│   │   ├── user_repository.go
│   │   └── product_repository.go
│   │
│   ├── service/                # Business logic
│   │   ├── user_service.go
│   │   └── product_service.go
│   │
│   └── dto/                    # Data Transfer Objects
│       ├── request.go
│       └── response.go
│
├── pkg/                        # Public reusable packages
│   ├── validator/
│   │   └── validator.go
│   ├── logger/
│   │   └── logger.go
│   └── database/
│       └── postgres.go
│
├── migrations/                 # Database migrations
│   ├── 001_create_users.up.sql
│   └── 001_create_users.down.sql
│
├── scripts/                    # Build/deploy scripts
│   └── deploy.sh
│
└── docs/                       # Documentation
    └── api.md
```

---

## 3️⃣ LARGE PROJECT (Enterprise/Microservice)

Untuk project besar dengan multiple services:

```
my_project/
├── go.mod
├── go.sum
├── go.work                     # Go workspace (monorepo)
├── README.md
├── Makefile
├── .env.example
├── .gitignore
├── docker-compose.yml
│
├── cmd/                        # Application entry points
│   ├── api/
│   │   └── main.go             # REST API server
│   ├── grpc/
│   │   └── main.go             # gRPC server
│   ├── worker/
│   │   └── main.go             # Background worker
│   └── migrate/
│       └── main.go             # Migration tool
│
├── internal/                   # Private application code
│   │
│   ├── app/                    # Application setup
│   │   ├── app.go              # App struct & initialization
│   │   └── routes.go           # Route registration
│   │
│   ├── config/
│   │   ├── config.go
│   │   └── database.go
│   │
│   ├── domain/                 # Domain layer (entities)
│   │   ├── user/
│   │   │   ├── entity.go       # User entity
│   │   │   ├── repository.go   # Repository interface
│   │   │   └── service.go      # Service interface
│   │   ├── product/
│   │   │   └── ...
│   │   ├── order/
│   │   │   └── ...
│   │   └── errors.go           # Domain errors
│   │
│   ├── usecase/                # Use case layer (application logic)
│   │   ├── user/
│   │   │   ├── usecase.go      # Use case implementation
│   │   │   └── usecase_test.go
│   │   ├── product/
│   │   │   └── ...
│   │   └── order/
│   │       └── ...
│   │
│   ├── repository/             # Repository implementations
│   │   ├── postgres/
│   │   │   ├── user_repository.go
│   │   │   ├── product_repository.go
│   │   │   └── order_repository.go
│   │   └── redis/
│   │       └── cache_repository.go
│   │
│   ├── delivery/               # Delivery layer (API handlers)
│   │   ├── http/
│   │   │   ├── handler/
│   │   │   │   ├── user_handler.go
│   │   │   │   └── product_handler.go
│   │   │   ├── middleware/
│   │   │   │   ├── auth.go
│   │   │   │   ├── cors.go
│   │   │   │   └── logging.go
│   │   │   ├── router/
│   │   │   │   └── router.go
│   │   │   └── dto/
│   │   │       ├── request/
│   │   │       │   └── user_request.go
│   │   │       └── response/
│   │   │           └── user_response.go
│   │   └── grpc/
│   │       ├── handler/
│   │       │   └── user_handler.go
│   │       └── proto/
│   │           └── user.proto
│   │
│   ├── infrastructure/         # External services
│   │   ├── database/
│   │   │   ├── postgres.go
│   │   │   └── redis.go
│   │   ├── cache/
│   │   │   └── redis_cache.go
│   │   ├── queue/
│   │   │   └── rabbitmq.go
│   │   └── external/
│   │       ├── payment.go
│   │       └── email.go
│   │
│   └── worker/                 # Background workers
│       ├── email_worker.go
│       └── notification_worker.go
│
├── pkg/                        # Public reusable packages
│   ├── logger/
│   │   ├── logger.go
│   │   └── zap.go
│   ├── validator/
│   │   └── validator.go
│   ├── response/
│   │   └── response.go
│   ├── errors/
│   │   └── errors.go
│   ├── utils/
│   │   ├── string.go
│   │   └── time.go
│   └── auth/
│       ├── jwt.go
│       └── password.go
│
├── api/                        # API definitions
│   ├── openapi/
│   │   └── openapi.yaml        # OpenAPI spec
│   └── proto/
│       └── user.proto          # Protobuf definitions
│
├── migrations/
│   ├── 001_create_users.up.sql
│   ├── 001_create_users.down.sql
│   ├── 002_create_products.up.sql
│   └── 002_create_products.down.sql
│
├── scripts/
│   ├── build.sh
│   ├── deploy.sh
│   └── generate.sh
│
├── deployments/                # Deployment configs
│   ├── docker/
│   │   ├── Dockerfile.api
│   │   └── Dockerfile.worker
│   └── k8s/
│       ├── deployment.yaml
│       └── service.yaml
│
├── test/                       # Additional test resources
│   ├── fixtures/
│   │   └── users.json
│   ├── integration/
│   │   └── api_test.go
│   └── e2e/
│       └── flow_test.go
│
├── docs/
│   ├── api/
│   ├── architecture/
│   └── deployment/
│
└── .github/
    └── workflows/
        ├── ci.yml
        └── deploy.yml
```

---

## 4️⃣ CLEAN ARCHITECTURE STRUCTURE

Mengikuti Clean Architecture principles:

```
internal/
├── domain/                     # Enterprise Business Rules (Entities)
│   ├── user.go                 # Entity
│   ├── product.go
│   └── errors.go
│
├── usecase/                    # Application Business Rules
│   ├── user/
│   │   ├── interface.go        # Port (interface)
│   │   ├── usecase.go          # Implementation
│   │   └── usecase_test.go
│   └── product/
│       └── ...
│
├── adapter/                    # Interface Adapters
│   ├── controller/             # HTTP handlers
│   │   └── user_controller.go
│   ├── presenter/              # Response formatting
│   │   └── user_presenter.go
│   └── repository/             # Repository implementation
│       └── user_repository.go
│
└── infrastructure/             # Frameworks & Drivers
    ├── database/
    ├── cache/
    └── external/
```

---

## 5️⃣ HEXAGONAL ARCHITECTURE STRUCTURE

Mengikuti Hexagonal (Ports & Adapters) pattern:

```
internal/
├── core/                       # Core domain
│   ├── domain/                 # Entities & value objects
│   │   ├── user.go
│   │   └── product.go
│   ├── port/                   # Interfaces (ports)
│   │   ├── input/              # Primary/driving ports
│   │   │   ├── user_service.go
│   │   │   └── product_service.go
│   │   └── output/             # Secondary/driven ports
│   │       ├── user_repository.go
│   │       └── cache.go
│   └── service/                # Use case implementations
│       ├── user_service.go
│       └── product_service.go
│
└── adapter/                    # Adapters
    ├── primary/                # Primary/driving adapters
    │   ├── http/
    │   │   └── user_handler.go
    │   └── grpc/
    │       └── user_handler.go
    └── secondary/              # Secondary/driven adapters
        ├── postgres/
        │   └── user_repository.go
        └── redis/
            └── cache.go
```

---

## 6️⃣ FOLDER EXPLANATION

### `cmd/`
Entry points untuk aplikasi. Setiap subdirectory adalah executable.

```go
// cmd/api/main.go
package main

import (
    "myapp/internal/app"
)

func main() {
    application := app.New()
    application.Run()
}
```

### `internal/`
Private application code. Package di sini tidak bisa di-import dari project lain.

### `pkg/`
Public reusable packages. Bisa di-import dari project lain.

```go
// Contoh import dari project lain
import "github.com/username/myapp/pkg/logger"
```

### `api/`
API definitions: OpenAPI specs, protobuf files, GraphQL schemas.

### `migrations/`
Database migration files.

---

## 7️⃣ COMMON PATTERNS

### Repository Pattern

```
internal/
├── domain/
│   └── user/
│       ├── entity.go           # type User struct
│       └── repository.go       # type Repository interface
│
└── repository/
    └── postgres/
        └── user_repository.go  # Implementation
```

```go
// internal/domain/user/repository.go
package user

type Repository interface {
    FindByID(ctx context.Context, id string) (*User, error)
    FindAll(ctx context.Context) ([]*User, error)
    Create(ctx context.Context, user *User) error
    Update(ctx context.Context, user *User) error
    Delete(ctx context.Context, id string) error
}
```

### Service Pattern

```go
// internal/service/user_service.go
package service

type UserService struct {
    repo   user.Repository
    cache  cache.Cache
    logger logger.Logger
}

func NewUserService(repo user.Repository, cache cache.Cache, logger logger.Logger) *UserService {
    return &UserService{
        repo:   repo,
        cache:  cache,
        logger: logger,
    }
}
```

---

## 8️⃣ FILE NAMING CONVENTIONS

| Type | Convention | Example |
|------|------------|---------|
| Package | lowercase, short | `user`, `auth`, `utils` |
| File | lowercase, snake_case | `user_service.go`, `jwt_auth.go` |
| Test file | _test suffix | `user_service_test.go` |
| Interface | -er suffix (jika bisa) | `Reader`, `Writer`, `Repository` |
| Struct | PascalCase | `UserService`, `Config` |
| Private | lowercase | `parseToken`, `validateInput` |

---

## 9️⃣ MAKEFILE EXAMPLE

```makefile
# Makefile
.PHONY: build run test lint clean

# Variables
APP_NAME=myapp
BUILD_DIR=./bin

# Build
build:
	go build -o $(BUILD_DIR)/$(APP_NAME) ./cmd/api

# Run
run:
	go run ./cmd/api

# Test
test:
	go test -v -race -cover ./...

# Test with coverage
test-coverage:
	go test -coverprofile=coverage.out ./...
	go tool cover -html=coverage.out

# Lint
lint:
	golangci-lint run

# Generate (swagger, protobuf, etc)
generate:
	go generate ./...

# Migration
migrate-up:
	migrate -path migrations -database "$(DATABASE_URL)" up

migrate-down:
	migrate -path migrations -database "$(DATABASE_URL)" down 1

# Docker
docker-build:
	docker build -t $(APP_NAME) .

docker-run:
	docker-compose up -d

# Clean
clean:
	rm -rf $(BUILD_DIR)
	rm -f coverage.out
```

---

## 📊 Comparison Table

| Aspect | Small | Medium | Large |
|--------|-------|--------|-------|
| cmd/ | ❌ | ✅ | ✅ |
| internal/ | ❌ | ✅ | ✅ |
| pkg/ | ❌ | Optional | ✅ |
| domain layer | ❌ | Optional | ✅ |
| Clean/Hex Architecture | ❌ | Optional | ✅ |
| Multiple services | ❌ | ❌ | ✅ |
| gRPC | ❌ | Optional | ✅ |

---

## 💡 Best Practices

### ✅ DO

- Gunakan `internal/` untuk private code
- Flat structure untuk project kecil
- Interface di package yang menggunakan
- Test di package yang sama (xxx_test.go)
- Dependency injection via constructor

### ❌ DON'T

- Jangan `src/` folder (bukan Go convention)
- Jangan nested terlalu dalam (max 3-4 level)
- Jangan circular dependencies
- Jangan global state
- Jangan init() untuk side effects

---

## 🔗 Related Docs

- [BASICS.md](01-fundamentals/BASICS.md) - Go basics
- [HTTP.md](02-web/HTTP.md) - HTTP server patterns
- [CLEAN_ARCH.md](04-architecture/CLEAN_ARCH.md) - Clean architecture
