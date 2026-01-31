# 📚 Go Documentation - Learning Path

Dokumentasi lengkap Go/Golang dari Junior sampai Senior level.

---

## 🎯 Overview

Dokumentasi ini dirancang untuk programmer yang ingin mempelajari Go dari dasar hingga advanced level. Setiap dokumen berisi penjelasan bertahap dari **Junior → Mid → Senior → Expert**.

---

## 📖 Daftar Dokumentasi

### 📁 01-fundamentals/ - Dasar-dasar Go

| File | Deskripsi | Level |
|------|-----------|-------|
| [GETTING_STARTED.md](01-fundamentals/GETTING_STARTED.md) | Instalasi, syntax dasar, variabel, tipe data, control flow, functions, structs, pointers, error handling | ⭐ Junior → Mid |
| [ARCHITECTURE.md](01-fundamentals/ARCHITECTURE.md) | Project structure, Standard Layout, Clean Architecture, Dependency Injection, Makefile | ⭐⭐ Mid → Senior |
| [INTERFACES.md](01-fundamentals/INTERFACES.md) | Interface basics, type assertions, common interfaces (io.Reader, Stringer, error), composition, mocking | ⭐⭐ Mid → Senior |
| [HTTP_API.md](01-fundamentals/HTTP_API.md) | net/http, Gin framework, CRUD operations, middleware, validation, graceful shutdown | ⭐⭐ Mid → Senior |

### 📁 02-database/ - Database Operations

| File | Deskripsi | Level |
|------|-----------|-------|
| [DATABASE.md](02-database/DATABASE.md) | database/sql, GORM, relationships, transactions, hooks, repository pattern, connection pooling | ⭐⭐ Mid → Expert |
| [PAGINATION.md](02-database/PAGINATION.md) | Offset pagination, cursor pagination, filtering, sorting, query builder pattern | ⭐⭐ Mid → Senior |

### 📁 03-authentication/ - Auth & Security

| File | Deskripsi | Level |
|------|-----------|-------|
| [AUTH.md](03-authentication/AUTH.md) | Password hashing (bcrypt), JWT, token pairs, auth handlers, middleware, RBAC, permissions | ⭐⭐ Mid → Expert |
| [SECURITY.md](03-authentication/SECURITY.md) | Input validation, SQL injection, XSS, CORS, rate limiting, security headers, CSRF, secrets management | ⭐⭐⭐ Senior → Expert |

### 📁 04-advanced/ - Advanced Topics

| File | Deskripsi | Level |
|------|-----------|-------|
| [CONCURRENCY.md](04-advanced/CONCURRENCY.md) | Goroutines, channels, select, sync package (WaitGroup, Mutex, RWMutex, Once), worker pools, pipelines, context | ⭐⭐⭐ Senior → Expert |

### 📁 05-testing/ - Testing

| File | Deskripsi | Level |
|------|-----------|-------|
| [TESTS.md](05-testing/TESTS.md) | Unit testing, table-driven tests, testify, HTTP handler testing, mocking, integration tests, benchmarking | ⭐⭐ Mid → Expert |

### 📁 06-operations/ - Operations

| File | Deskripsi | Level |
|------|-----------|-------|
| [LOGGING.md](06-operations/LOGGING.md) | Standard log, Zap, Zerolog, structured logging, request logging, correlation, log rotation | ⭐⭐ Mid → Expert |
| [DEPLOYMENT.md](06-operations/DEPLOYMENT.md) | Building, Docker, configuration, health checks, graceful shutdown, Kubernetes, CI/CD | ⭐⭐⭐ Senior → Expert |

---

## 🗺️ Learning Path

### 🟢 Pemula (1-3 bulan)

```
GETTING_STARTED.md → INTERFACES.md → HTTP_API.md
```

**Fokus:**
1. Syntax dasar Go
2. Tipe data dan control flow
3. Functions dan methods
4. Structs dan pointers
5. Error handling
6. Interface basics
7. Basic HTTP server

### 🟡 Intermediate (3-6 bulan)

```
ARCHITECTURE.md → DATABASE.md → AUTH.md → TESTS.md
```

**Fokus:**
1. Project structure
2. Clean architecture
3. GORM dan database operations
4. JWT authentication
5. Middleware patterns
6. Unit testing

### 🟠 Advanced (6-12 bulan)

```
CONCURRENCY.md → SECURITY.md → PAGINATION.md → LOGGING.md
```

**Fokus:**
1. Goroutines dan channels
2. Security best practices
3. Pagination patterns
4. Structured logging

### 🔴 Expert (12+ bulan)

```
DEPLOYMENT.md → All advanced sections
```

**Fokus:**
1. Docker & Kubernetes
2. CI/CD pipelines
3. Performance optimization
4. Distributed systems

---

## 📦 Libraries yang Digunakan

### Web Framework
- **Gin** - High-performance HTTP web framework

### Database
- **GORM** - ORM untuk Go
- **database/sql** - Standard library

### Authentication
- **golang-jwt/jwt** - JWT implementation
- **bcrypt** - Password hashing

### Logging
- **Zap** - Uber's structured logging
- **Zerolog** - Zero allocation logger

### Testing
- **testify** - Testing toolkit

### Security
- **bluemonday** - HTML sanitizer
- **go-redis** - Redis client

---

## 🚀 Quick Start

### 1. Install Go

```bash
# Download dari https://go.dev/dl/
# Atau dengan package manager

# macOS
brew install go

# Ubuntu/Debian
sudo apt install golang-go

# Verify
go version
```

### 2. Setup Project

```bash
mkdir myproject
cd myproject
go mod init github.com/username/myproject
```

### 3. Struktur Project Minimal

```
myproject/
├── cmd/
│   └── api/
│       └── main.go
├── internal/
│   ├── handler/
│   ├── service/
│   └── repository/
├── go.mod
└── go.sum
```

### 4. Hello World API

```go
// cmd/api/main.go
package main

import (
    "net/http"
    
    "github.com/gin-gonic/gin"
)

func main() {
    r := gin.Default()
    
    r.GET("/", func(c *gin.Context) {
        c.JSON(http.StatusOK, gin.H{
            "message": "Hello, World!",
        })
    })
    
    r.Run(":8080")
}
```

```bash
go mod tidy
go run ./cmd/api
```

---

## 📝 Konvensi Dokumentasi

### Level Markers
- **Junior** ⭐ - Konsep dasar
- **Mid** ⭐⭐ - Intermediate patterns
- **Senior** ⭐⭐⭐ - Advanced topics
- **Expert** ⭐⭐⭐⭐ - Production-grade

### Code Examples
Setiap section memiliki code examples yang bisa langsung di-copy dan dijalankan.

### Best Practices
Setiap dokumen memiliki summary dengan ✅ DO dan ❌ DON'T.

---

## 🔗 Resources

### Official
- [Go Documentation](https://go.dev/doc/)
- [Go by Example](https://gobyexample.com/)
- [Effective Go](https://go.dev/doc/effective_go)

### Libraries
- [Gin Documentation](https://gin-gonic.com/docs/)
- [GORM Documentation](https://gorm.io/docs/)
- [Zap Logger](https://pkg.go.dev/go.uber.org/zap)

### Learning
- [Go Tour](https://go.dev/tour/)
- [Go Playground](https://go.dev/play/)
- [Gophercises](https://gophercises.com/)

---

## 🎓 Tips Belajar

1. **Praktik Langsung** - Jangan hanya baca, ketik kodenya
2. **Buat Project** - Implementasikan konsep dalam project nyata
3. **Baca Source Code** - Pelajari library open source
4. **Review Code** - Minta feedback dari developer lain
5. **Dokumentasikan** - Tulis apa yang kamu pelajari

---

## 📊 Perbandingan dengan Django

| Konsep | Django | Go |
|--------|--------|-----|
| Web Framework | Django/DRF | Gin/Echo/Chi |
| ORM | Django ORM | GORM |
| Migrations | Django Migrate | golang-migrate |
| Auth | Django Auth | Custom JWT |
| Async | Celery | Goroutines |
| Testing | pytest/unittest | testing/testify |

---

**Happy Learning! 🚀**

*"Simplicity is the ultimate sophistication." - Go Philosophy*
