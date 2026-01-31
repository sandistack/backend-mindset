# 🧪 TESTING - Testing di Go (Junior → Senior)

Dokumentasi lengkap tentang testing di Go - unit tests, integration tests, dan mocking.

---

## 🎯 Testing di Go

```
Go punya built-in testing framework:
- testing package
- go test command
- Benchmarking
- Coverage reports

Testing Pyramid:
        /\
       /  \      E2E Tests (few)
      /----\
     /      \    Integration Tests
    /--------\
   /          \  Unit Tests (many)
  /------------\
```

---

## 1️⃣ JUNIOR LEVEL - Unit Test Basics

### File Naming Convention

```
myfile.go       → Source file
myfile_test.go  → Test file (MUST end with _test.go)
```

### Basic Test

```go
// calculator.go
package calculator

func Add(a, b int) int {
    return a + b
}

func Subtract(a, b int) int {
    return a - b
}

func Divide(a, b int) (int, error) {
    if b == 0 {
        return 0, errors.New("cannot divide by zero")
    }
    return a / b, nil
}
```

```go
// calculator_test.go
package calculator

import (
    "testing"
)

func TestAdd(t *testing.T) {
    result := Add(2, 3)
    expected := 5
    
    if result != expected {
        t.Errorf("Add(2, 3) = %d; want %d", result, expected)
    }
}

func TestSubtract(t *testing.T) {
    result := Subtract(10, 3)
    expected := 7
    
    if result != expected {
        t.Errorf("Subtract(10, 3) = %d; want %d", result, expected)
    }
}

func TestDivide(t *testing.T) {
    result, err := Divide(10, 2)
    
    if err != nil {
        t.Errorf("unexpected error: %v", err)
    }
    
    if result != 5 {
        t.Errorf("Divide(10, 2) = %d; want 5", result)
    }
}

func TestDivideByZero(t *testing.T) {
    _, err := Divide(10, 0)
    
    if err == nil {
        t.Error("expected error for division by zero")
    }
}
```

### Running Tests

```bash
# Run all tests in current package
go test

# Run all tests with verbose output
go test -v

# Run specific test
go test -run TestAdd

# Run tests in all packages
go test ./...

# Run with coverage
go test -cover

# Generate coverage report
go test -coverprofile=coverage.out
go tool cover -html=coverage.out
```

---

## 2️⃣ MID LEVEL - Table-Driven Tests

### Table-Driven Pattern

```go
// calculator_test.go
package calculator

import "testing"

func TestAddTableDriven(t *testing.T) {
    tests := []struct {
        name     string
        a, b     int
        expected int
    }{
        {"positive numbers", 2, 3, 5},
        {"negative numbers", -2, -3, -5},
        {"mixed numbers", -2, 3, 1},
        {"zero", 0, 0, 0},
        {"with zero", 5, 0, 5},
    }
    
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            result := Add(tt.a, tt.b)
            if result != tt.expected {
                t.Errorf("Add(%d, %d) = %d; want %d", 
                    tt.a, tt.b, result, tt.expected)
            }
        })
    }
}

func TestDivideTableDriven(t *testing.T) {
    tests := []struct {
        name      string
        a, b      int
        expected  int
        expectErr bool
    }{
        {"normal division", 10, 2, 5, false},
        {"integer division", 7, 2, 3, false},
        {"divide by zero", 10, 0, 0, true},
        {"negative result", -10, 2, -5, false},
    }
    
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            result, err := Divide(tt.a, tt.b)
            
            if tt.expectErr {
                if err == nil {
                    t.Error("expected error, got nil")
                }
                return
            }
            
            if err != nil {
                t.Errorf("unexpected error: %v", err)
                return
            }
            
            if result != tt.expected {
                t.Errorf("Divide(%d, %d) = %d; want %d",
                    tt.a, tt.b, result, tt.expected)
            }
        })
    }
}
```

---

## 3️⃣ MID LEVEL - Testing with testify

### Install testify

```bash
go get github.com/stretchr/testify
```

### Using assert and require

```go
package calculator

import (
    "testing"
    
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

func TestAddWithTestify(t *testing.T) {
    result := Add(2, 3)
    
    // assert continues even if failed
    assert.Equal(t, 5, result)
    assert.NotEqual(t, 0, result)
    
    // require stops test if failed
    require.Equal(t, 5, result)
}

func TestDivideWithTestify(t *testing.T) {
    t.Run("success", func(t *testing.T) {
        result, err := Divide(10, 2)
        
        require.NoError(t, err)
        assert.Equal(t, 5, result)
    })
    
    t.Run("divide by zero", func(t *testing.T) {
        _, err := Divide(10, 0)
        
        require.Error(t, err)
        assert.Contains(t, err.Error(), "divide by zero")
    })
}

func TestSliceWithTestify(t *testing.T) {
    result := []int{1, 2, 3}
    
    assert.Len(t, result, 3)
    assert.Contains(t, result, 2)
    assert.ElementsMatch(t, []int{3, 1, 2}, result)
}

func TestMapWithTestify(t *testing.T) {
    result := map[string]int{"a": 1, "b": 2}
    
    assert.Len(t, result, 2)
    assert.Contains(t, result, "a")
    assert.Equal(t, 1, result["a"])
}
```

---

## 4️⃣ MID LEVEL - HTTP Handler Testing

### Testing Gin Handlers

```go
// handler.go
package handler

import (
    "net/http"
    
    "github.com/gin-gonic/gin"
)

type User struct {
    ID    uint   `json:"id"`
    Name  string `json:"name"`
    Email string `json:"email"`
}

func GetUser(c *gin.Context) {
    id := c.Param("id")
    
    if id == "0" {
        c.JSON(http.StatusNotFound, gin.H{"error": "user not found"})
        return
    }
    
    user := User{ID: 1, Name: "John", Email: "john@example.com"}
    c.JSON(http.StatusOK, gin.H{"data": user})
}

func CreateUser(c *gin.Context) {
    var user User
    if err := c.ShouldBindJSON(&user); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }
    
    user.ID = 1
    c.JSON(http.StatusCreated, gin.H{"data": user})
}
```

```go
// handler_test.go
package handler

import (
    "bytes"
    "encoding/json"
    "net/http"
    "net/http/httptest"
    "testing"
    
    "github.com/gin-gonic/gin"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

// Setup test router
func setupRouter() *gin.Engine {
    gin.SetMode(gin.TestMode)
    r := gin.New()
    r.GET("/users/:id", GetUser)
    r.POST("/users", CreateUser)
    return r
}

func TestGetUser_Success(t *testing.T) {
    router := setupRouter()
    
    w := httptest.NewRecorder()
    req, _ := http.NewRequest("GET", "/users/1", nil)
    router.ServeHTTP(w, req)
    
    assert.Equal(t, http.StatusOK, w.Code)
    
    var response map[string]User
    err := json.Unmarshal(w.Body.Bytes(), &response)
    require.NoError(t, err)
    
    assert.Equal(t, "John", response["data"].Name)
}

func TestGetUser_NotFound(t *testing.T) {
    router := setupRouter()
    
    w := httptest.NewRecorder()
    req, _ := http.NewRequest("GET", "/users/0", nil)
    router.ServeHTTP(w, req)
    
    assert.Equal(t, http.StatusNotFound, w.Code)
    
    var response map[string]string
    json.Unmarshal(w.Body.Bytes(), &response)
    
    assert.Equal(t, "user not found", response["error"])
}

func TestCreateUser_Success(t *testing.T) {
    router := setupRouter()
    
    user := User{Name: "Jane", Email: "jane@example.com"}
    body, _ := json.Marshal(user)
    
    w := httptest.NewRecorder()
    req, _ := http.NewRequest("POST", "/users", bytes.NewBuffer(body))
    req.Header.Set("Content-Type", "application/json")
    router.ServeHTTP(w, req)
    
    assert.Equal(t, http.StatusCreated, w.Code)
    
    var response map[string]User
    json.Unmarshal(w.Body.Bytes(), &response)
    
    assert.Equal(t, uint(1), response["data"].ID)
    assert.Equal(t, "Jane", response["data"].Name)
}

func TestCreateUser_BadRequest(t *testing.T) {
    router := setupRouter()
    
    w := httptest.NewRecorder()
    req, _ := http.NewRequest("POST", "/users", bytes.NewBufferString("invalid json"))
    req.Header.Set("Content-Type", "application/json")
    router.ServeHTTP(w, req)
    
    assert.Equal(t, http.StatusBadRequest, w.Code)
}
```

---

## 5️⃣ SENIOR LEVEL - Mocking with Interfaces

### Service with Dependency

```go
// repository/user_repository.go
package repository

type User struct {
    ID    uint
    Name  string
    Email string
}

type UserRepository interface {
    FindByID(id uint) (*User, error)
    Create(user *User) error
    Update(user *User) error
    Delete(id uint) error
}
```

```go
// service/user_service.go
package service

import (
    "errors"
    
    "github.com/username/myapp/repository"
)

var ErrUserNotFound = errors.New("user not found")

type UserService struct {
    repo repository.UserRepository
}

func NewUserService(repo repository.UserRepository) *UserService {
    return &UserService{repo: repo}
}

func (s *UserService) GetUser(id uint) (*repository.User, error) {
    user, err := s.repo.FindByID(id)
    if err != nil {
        return nil, err
    }
    if user == nil {
        return nil, ErrUserNotFound
    }
    return user, nil
}

func (s *UserService) CreateUser(name, email string) (*repository.User, error) {
    user := &repository.User{
        Name:  name,
        Email: email,
    }
    
    if err := s.repo.Create(user); err != nil {
        return nil, err
    }
    
    return user, nil
}
```

### Manual Mock

```go
// service/user_service_test.go
package service

import (
    "errors"
    "testing"
    
    "github.com/stretchr/testify/assert"
    "github.com/username/myapp/repository"
)

// Mock implementation
type MockUserRepository struct {
    users    map[uint]*repository.User
    createFn func(user *repository.User) error
    findFn   func(id uint) (*repository.User, error)
}

func NewMockUserRepository() *MockUserRepository {
    return &MockUserRepository{
        users: make(map[uint]*repository.User),
    }
}

func (m *MockUserRepository) FindByID(id uint) (*repository.User, error) {
    if m.findFn != nil {
        return m.findFn(id)
    }
    user, ok := m.users[id]
    if !ok {
        return nil, nil
    }
    return user, nil
}

func (m *MockUserRepository) Create(user *repository.User) error {
    if m.createFn != nil {
        return m.createFn(user)
    }
    user.ID = uint(len(m.users) + 1)
    m.users[user.ID] = user
    return nil
}

func (m *MockUserRepository) Update(user *repository.User) error {
    return nil
}

func (m *MockUserRepository) Delete(id uint) error {
    return nil
}

// Tests
func TestGetUser_Success(t *testing.T) {
    mockRepo := NewMockUserRepository()
    mockRepo.users[1] = &repository.User{ID: 1, Name: "John", Email: "john@example.com"}
    
    service := NewUserService(mockRepo)
    
    user, err := service.GetUser(1)
    
    assert.NoError(t, err)
    assert.Equal(t, "John", user.Name)
}

func TestGetUser_NotFound(t *testing.T) {
    mockRepo := NewMockUserRepository()
    service := NewUserService(mockRepo)
    
    user, err := service.GetUser(999)
    
    assert.Error(t, err)
    assert.Equal(t, ErrUserNotFound, err)
    assert.Nil(t, user)
}

func TestGetUser_RepositoryError(t *testing.T) {
    mockRepo := NewMockUserRepository()
    mockRepo.findFn = func(id uint) (*repository.User, error) {
        return nil, errors.New("database error")
    }
    
    service := NewUserService(mockRepo)
    
    user, err := service.GetUser(1)
    
    assert.Error(t, err)
    assert.Nil(t, user)
}

func TestCreateUser_Success(t *testing.T) {
    mockRepo := NewMockUserRepository()
    service := NewUserService(mockRepo)
    
    user, err := service.CreateUser("Jane", "jane@example.com")
    
    assert.NoError(t, err)
    assert.Equal(t, "Jane", user.Name)
    assert.Equal(t, uint(1), user.ID)
}
```

### Using testify/mock

```go
package service

import (
    "testing"
    
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
    "github.com/username/myapp/repository"
)

type MockRepository struct {
    mock.Mock
}

func (m *MockRepository) FindByID(id uint) (*repository.User, error) {
    args := m.Called(id)
    if args.Get(0) == nil {
        return nil, args.Error(1)
    }
    return args.Get(0).(*repository.User), args.Error(1)
}

func (m *MockRepository) Create(user *repository.User) error {
    args := m.Called(user)
    return args.Error(0)
}

func (m *MockRepository) Update(user *repository.User) error {
    args := m.Called(user)
    return args.Error(0)
}

func (m *MockRepository) Delete(id uint) error {
    args := m.Called(id)
    return args.Error(0)
}

func TestGetUserWithMock(t *testing.T) {
    mockRepo := new(MockRepository)
    
    // Setup expectation
    expectedUser := &repository.User{ID: 1, Name: "John"}
    mockRepo.On("FindByID", uint(1)).Return(expectedUser, nil)
    
    service := NewUserService(mockRepo)
    
    user, err := service.GetUser(1)
    
    assert.NoError(t, err)
    assert.Equal(t, "John", user.Name)
    
    // Verify expectations
    mockRepo.AssertExpectations(t)
    mockRepo.AssertCalled(t, "FindByID", uint(1))
}
```

---

## 6️⃣ SENIOR LEVEL - Integration Testing

### Database Integration Test

```go
// integration_test.go
package integration

import (
    "context"
    "testing"
    
    "github.com/stretchr/testify/suite"
    "github.com/testcontainers/testcontainers-go"
    "github.com/testcontainers/testcontainers-go/wait"
    "gorm.io/driver/postgres"
    "gorm.io/gorm"
)

type IntegrationTestSuite struct {
    suite.Suite
    db        *gorm.DB
    container testcontainers.Container
}

func (s *IntegrationTestSuite) SetupSuite() {
    ctx := context.Background()
    
    // Start PostgreSQL container
    req := testcontainers.ContainerRequest{
        Image:        "postgres:15",
        ExposedPorts: []string{"5432/tcp"},
        Env: map[string]string{
            "POSTGRES_USER":     "test",
            "POSTGRES_PASSWORD": "test",
            "POSTGRES_DB":       "testdb",
        },
        WaitingFor: wait.ForListeningPort("5432/tcp"),
    }
    
    container, err := testcontainers.GenericContainer(ctx, testcontainers.GenericContainerRequest{
        ContainerRequest: req,
        Started:          true,
    })
    s.Require().NoError(err)
    s.container = container
    
    // Get connection string
    host, _ := container.Host(ctx)
    port, _ := container.MappedPort(ctx, "5432")
    
    dsn := fmt.Sprintf("host=%s port=%s user=test password=test dbname=testdb sslmode=disable",
        host, port.Port())
    
    // Connect to database
    db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
    s.Require().NoError(err)
    s.db = db
    
    // Migrate
    s.db.AutoMigrate(&User{})
}

func (s *IntegrationTestSuite) TearDownSuite() {
    if s.container != nil {
        s.container.Terminate(context.Background())
    }
}

func (s *IntegrationTestSuite) SetupTest() {
    // Clean database before each test
    s.db.Exec("TRUNCATE TABLE users RESTART IDENTITY CASCADE")
}

func (s *IntegrationTestSuite) TestCreateUser() {
    repo := NewUserRepository(s.db)
    service := NewUserService(repo)
    
    user, err := service.CreateUser("John", "john@example.com")
    
    s.NoError(err)
    s.Equal("John", user.Name)
    s.NotZero(user.ID)
    
    // Verify in database
    var count int64
    s.db.Model(&User{}).Count(&count)
    s.Equal(int64(1), count)
}

func (s *IntegrationTestSuite) TestGetUser() {
    // Seed data
    s.db.Create(&User{Name: "Jane", Email: "jane@example.com"})
    
    repo := NewUserRepository(s.db)
    service := NewUserService(repo)
    
    user, err := service.GetUser(1)
    
    s.NoError(err)
    s.Equal("Jane", user.Name)
}

func TestIntegrationSuite(t *testing.T) {
    if testing.Short() {
        t.Skip("Skipping integration tests in short mode")
    }
    suite.Run(t, new(IntegrationTestSuite))
}
```

### Run Integration Tests

```bash
# Run all tests
go test ./...

# Skip integration tests
go test -short ./...

# Run only integration tests
go test -run Integration ./...
```

---

## 7️⃣ EXPERT LEVEL - Benchmarking

### Benchmark Tests

```go
// calculator_test.go
package calculator

import "testing"

func BenchmarkAdd(b *testing.B) {
    for i := 0; i < b.N; i++ {
        Add(100, 200)
    }
}

func BenchmarkFibonacci(b *testing.B) {
    for i := 0; i < b.N; i++ {
        Fibonacci(20)
    }
}

// Benchmark with different inputs
func BenchmarkFibonacciTable(b *testing.B) {
    benchmarks := []struct {
        name string
        n    int
    }{
        {"Fib10", 10},
        {"Fib20", 20},
        {"Fib30", 30},
    }
    
    for _, bm := range benchmarks {
        b.Run(bm.name, func(b *testing.B) {
            for i := 0; i < b.N; i++ {
                Fibonacci(bm.n)
            }
        })
    }
}

// Benchmark with memory allocation
func BenchmarkSliceAppend(b *testing.B) {
    b.ReportAllocs() // Report memory allocations
    
    for i := 0; i < b.N; i++ {
        var slice []int
        for j := 0; j < 1000; j++ {
            slice = append(slice, j)
        }
    }
}

func BenchmarkSlicePrealloc(b *testing.B) {
    b.ReportAllocs()
    
    for i := 0; i < b.N; i++ {
        slice := make([]int, 0, 1000)
        for j := 0; j < 1000; j++ {
            slice = append(slice, j)
        }
    }
}
```

### Run Benchmarks

```bash
# Run benchmarks
go test -bench=.

# Run with memory allocation stats
go test -bench=. -benchmem

# Run specific benchmark
go test -bench=BenchmarkAdd

# Compare benchmarks
go test -bench=. -count=10 > old.txt
# Make changes
go test -bench=. -count=10 > new.txt
benchstat old.txt new.txt
```

---

## 8️⃣ EXPERT LEVEL - Test Coverage

### Coverage Commands

```bash
# Show coverage percentage
go test -cover

# Generate coverage profile
go test -coverprofile=coverage.out

# View coverage in browser
go tool cover -html=coverage.out

# View coverage in terminal
go tool cover -func=coverage.out

# Set coverage threshold in CI
go test -coverprofile=coverage.out
COVERAGE=$(go tool cover -func=coverage.out | grep total | awk '{print $3}' | sed 's/%//')
if (( $(echo "$COVERAGE < 80" | bc -l) )); then
    echo "Coverage is below 80%"
    exit 1
fi
```

### Coverage Report

```go
// Generate HTML coverage report
// go test -coverprofile=coverage.out
// go tool cover -html=coverage.out -o coverage.html

/*
Output example:
ok      github.com/username/myapp/service   0.015s  coverage: 85.5% of statements
*/
```

---

## 📊 Testing Cheat Sheet

### Test Types

| Type | Purpose | Speed | Dependencies |
|------|---------|-------|--------------|
| Unit | Test single function | Fast | Mocks |
| Integration | Test with real DB | Medium | Docker |
| E2E | Test full system | Slow | Full stack |

### testify Assert Methods

| Method | Description |
|--------|-------------|
| `Equal(t, expected, actual)` | Check equality |
| `NotEqual(t, a, b)` | Check not equal |
| `Nil(t, obj)` | Check nil |
| `NotNil(t, obj)` | Check not nil |
| `True(t, condition)` | Check true |
| `False(t, condition)` | Check false |
| `Error(t, err)` | Check error exists |
| `NoError(t, err)` | Check no error |
| `Contains(t, slice, element)` | Check contains |
| `Len(t, slice, length)` | Check length |

### Test File Structure

```
project/
├── service/
│   ├── user_service.go
│   └── user_service_test.go      # Unit tests
├── integration/
│   └── user_integration_test.go  # Integration tests
└── e2e/
    └── api_e2e_test.go           # E2E tests
```

---

## 💡 Summary

| Level | Focus |
|-------|-------|
| **Junior** | Basic tests, assertions |
| **Mid** | Table-driven tests, testify |
| **Mid-Senior** | HTTP handler tests |
| **Senior** | Mocking, interface testing |
| **Expert** | Integration tests, benchmarking |

**Best Practices:**
- ✅ Write tests before/with code (TDD)
- ✅ Use table-driven tests
- ✅ Mock external dependencies
- ✅ Aim for 80%+ coverage
- ✅ Test edge cases
- ✅ Use meaningful test names
- ❌ Don't test implementation details
- ❌ Don't skip error cases
- ❌ Don't depend on test order
