# 🔌 INTERFACES - Go Interface Patterns (Junior → Senior)

Dokumentasi lengkap tentang interface di Go - konsep fundamental yang membuat Go powerful.

---

## 🎯 Apa itu Interface?

```
Interface = Contract/Kontrak

Mendefinisikan "APA" yang bisa dilakukan object,
bukan "BAGAIMANA" melakukannya.

Di Go, interface adalah IMPLICIT:
- Tidak perlu keyword "implements"
- Jika type punya semua method dari interface, otomatis implement
```

---

## 1️⃣ JUNIOR LEVEL - Interface Basics

### Deklarasi Interface

```go
package main

import "fmt"

// Interface declaration
type Speaker interface {
    Speak() string
}

// Struct that implements Speaker (implicitly!)
type Dog struct {
    Name string
}

func (d Dog) Speak() string {
    return d.Name + " says: Woof!"
}

// Another struct that implements Speaker
type Cat struct {
    Name string
}

func (c Cat) Speak() string {
    return c.Name + " says: Meow!"
}

// Function that accepts any Speaker
func MakeSound(s Speaker) {
    fmt.Println(s.Speak())
}

func main() {
    dog := Dog{Name: "Buddy"}
    cat := Cat{Name: "Whiskers"}
    
    MakeSound(dog) // Buddy says: Woof!
    MakeSound(cat) // Whiskers says: Meow!
    
    // Array of interfaces
    animals := []Speaker{dog, cat}
    for _, animal := range animals {
        fmt.Println(animal.Speak())
    }
}
```

### Interface dengan Multiple Methods

```go
package main

import "fmt"

type Shape interface {
    Area() float64
    Perimeter() float64
}

type Rectangle struct {
    Width  float64
    Height float64
}

func (r Rectangle) Area() float64 {
    return r.Width * r.Height
}

func (r Rectangle) Perimeter() float64 {
    return 2 * (r.Width + r.Height)
}

type Circle struct {
    Radius float64
}

func (c Circle) Area() float64 {
    return 3.14159 * c.Radius * c.Radius
}

func (c Circle) Perimeter() float64 {
    return 2 * 3.14159 * c.Radius
}

func PrintShapeInfo(s Shape) {
    fmt.Printf("Area: %.2f, Perimeter: %.2f\n", s.Area(), s.Perimeter())
}

func main() {
    rect := Rectangle{Width: 10, Height: 5}
    circle := Circle{Radius: 7}
    
    PrintShapeInfo(rect)   // Area: 50.00, Perimeter: 30.00
    PrintShapeInfo(circle) // Area: 153.94, Perimeter: 43.98
}
```

### Empty Interface (interface{} atau any)

```go
package main

import "fmt"

// interface{} = accepts ANY type
func PrintAnything(v interface{}) {
    fmt.Printf("Value: %v, Type: %T\n", v, v)
}

// Go 1.18+: `any` is alias for interface{}
func PrintAny(v any) {
    fmt.Printf("Value: %v, Type: %T\n", v, v)
}

func main() {
    PrintAnything("Hello")     // Value: Hello, Type: string
    PrintAnything(42)          // Value: 42, Type: int
    PrintAnything(3.14)        // Value: 3.14, Type: float64
    PrintAnything(true)        // Value: true, Type: bool
    PrintAnything([]int{1, 2}) // Value: [1 2], Type: []int
}
```

---

## 2️⃣ MID LEVEL - Type Assertions & Type Switch

### Type Assertion

```go
package main

import "fmt"

func main() {
    var i interface{} = "hello"
    
    // Type assertion (can panic if wrong type)
    s := i.(string)
    fmt.Println(s) // hello
    
    // Safe type assertion (returns ok bool)
    s, ok := i.(string)
    if ok {
        fmt.Println("String value:", s)
    }
    
    // This would panic: n := i.(int)
    
    // Safe version
    n, ok := i.(int)
    if !ok {
        fmt.Println("Not an int")
    }
    fmt.Println(n) // 0 (zero value)
}
```

### Type Switch

```go
package main

import "fmt"

func DescribeType(i interface{}) {
    switch v := i.(type) {
    case int:
        fmt.Printf("Integer: %d\n", v)
    case string:
        fmt.Printf("String: %s\n", v)
    case float64:
        fmt.Printf("Float: %.2f\n", v)
    case bool:
        fmt.Printf("Boolean: %t\n", v)
    case []int:
        fmt.Printf("Int slice with %d elements\n", len(v))
    case nil:
        fmt.Println("Nil value")
    default:
        fmt.Printf("Unknown type: %T\n", v)
    }
}

func main() {
    DescribeType(42)             // Integer: 42
    DescribeType("hello")        // String: hello
    DescribeType(3.14)           // Float: 3.14
    DescribeType(true)           // Boolean: true
    DescribeType([]int{1, 2, 3}) // Int slice with 3 elements
    DescribeType(nil)            // Nil value
}
```

### Interface dengan Pointer Receiver

```go
package main

import "fmt"

type Counter interface {
    Increment()
    Value() int
}

type SimpleCounter struct {
    count int
}

// Pointer receiver - modifies the struct
func (c *SimpleCounter) Increment() {
    c.count++
}

func (c *SimpleCounter) Value() int {
    return c.count
}

func main() {
    // MUST use pointer because methods have pointer receiver
    counter := &SimpleCounter{}
    
    // This works
    var c Counter = counter
    c.Increment()
    c.Increment()
    fmt.Println(c.Value()) // 2
    
    // This would NOT compile:
    // var c Counter = SimpleCounter{} 
    // karena Increment() butuh pointer receiver
}
```

---

## 3️⃣ MID LEVEL - Common Go Interfaces

### io.Reader & io.Writer

```go
package main

import (
    "bytes"
    "fmt"
    "io"
    "os"
    "strings"
)

// io.Reader interface:
// type Reader interface {
//     Read(p []byte) (n int, err error)
// }

// io.Writer interface:
// type Writer interface {
//     Write(p []byte) (n int, err error)
// }

func main() {
    // ===== Reading =====
    
    // From string
    r1 := strings.NewReader("Hello from string")
    
    // From bytes
    r2 := bytes.NewReader([]byte("Hello from bytes"))
    
    // Read from any Reader
    buf := make([]byte, 1024)
    n, _ := r1.Read(buf)
    fmt.Println(string(buf[:n])) // Hello from string
    
    n, _ = r2.Read(buf)
    fmt.Println(string(buf[:n])) // Hello from bytes
    
    // ===== Writing =====
    
    // To bytes.Buffer
    var buffer bytes.Buffer
    buffer.Write([]byte("Hello "))
    buffer.WriteString("World")
    fmt.Println(buffer.String()) // Hello World
    
    // To stdout (os.Stdout implements io.Writer)
    io.WriteString(os.Stdout, "Direct to stdout\n")
    
    // ===== Copy between Reader and Writer =====
    source := strings.NewReader("Copy this text")
    var dest bytes.Buffer
    
    io.Copy(&dest, source)
    fmt.Println(dest.String()) // Copy this text
}
```

### Stringer Interface

```go
package main

import "fmt"

// fmt.Stringer interface:
// type Stringer interface {
//     String() string
// }

type Person struct {
    Name string
    Age  int
}

// Implement Stringer for custom print format
func (p Person) String() string {
    return fmt.Sprintf("%s (%d years old)", p.Name, p.Age)
}

type IPAddr [4]byte

func (ip IPAddr) String() string {
    return fmt.Sprintf("%d.%d.%d.%d", ip[0], ip[1], ip[2], ip[3])
}

func main() {
    person := Person{Name: "John", Age: 30}
    fmt.Println(person) // John (30 years old)
    
    ip := IPAddr{192, 168, 1, 1}
    fmt.Println(ip) // 192.168.1.1
}
```

### error Interface

```go
package main

import (
    "fmt"
)

// error interface:
// type error interface {
//     Error() string
// }

// Custom error type
type ValidationError struct {
    Field   string
    Message string
}

func (e ValidationError) Error() string {
    return fmt.Sprintf("validation failed on '%s': %s", e.Field, e.Message)
}

func ValidateUser(name, email string) error {
    if name == "" {
        return ValidationError{
            Field:   "name",
            Message: "cannot be empty",
        }
    }
    if email == "" {
        return ValidationError{
            Field:   "email",
            Message: "cannot be empty",
        }
    }
    return nil
}

func main() {
    err := ValidateUser("", "test@example.com")
    if err != nil {
        fmt.Println(err) // validation failed on 'name': cannot be empty
        
        // Type assertion to get more details
        if ve, ok := err.(ValidationError); ok {
            fmt.Printf("Field: %s\n", ve.Field)
            fmt.Printf("Message: %s\n", ve.Message)
        }
    }
}
```

### sort.Interface

```go
package main

import (
    "fmt"
    "sort"
)

// sort.Interface:
// type Interface interface {
//     Len() int
//     Less(i, j int) bool
//     Swap(i, j int)
// }

type Person struct {
    Name string
    Age  int
}

// Custom sort: ByAge
type ByAge []Person

func (a ByAge) Len() int           { return len(a) }
func (a ByAge) Less(i, j int) bool { return a[i].Age < a[j].Age }
func (a ByAge) Swap(i, j int)      { a[i], a[j] = a[j], a[i] }

// Custom sort: ByName
type ByName []Person

func (a ByName) Len() int           { return len(a) }
func (a ByName) Less(i, j int) bool { return a[i].Name < a[j].Name }
func (a ByName) Swap(i, j int)      { a[i], a[j] = a[j], a[i] }

func main() {
    people := []Person{
        {"Bob", 25},
        {"Alice", 30},
        {"Charlie", 20},
    }
    
    // Sort by age
    sort.Sort(ByAge(people))
    fmt.Println("By Age:", people)
    // By Age: [{Charlie 20} {Bob 25} {Alice 30}]
    
    // Sort by name
    sort.Sort(ByName(people))
    fmt.Println("By Name:", people)
    // By Name: [{Alice 30} {Bob 25} {Charlie 20}]
    
    // Go 1.8+: sort.Slice (easier!)
    sort.Slice(people, func(i, j int) bool {
        return people[i].Age < people[j].Age
    })
    fmt.Println("By Age (Slice):", people)
}
```

---

## 4️⃣ MID-SENIOR LEVEL - Interface Composition

### Interface Embedding

```go
package main

import (
    "fmt"
    "io"
)

// Composing interfaces
type Reader interface {
    Read(p []byte) (n int, err error)
}

type Writer interface {
    Write(p []byte) (n int, err error)
}

type Closer interface {
    Close() error
}

// Composed interface
type ReadWriter interface {
    Reader
    Writer
}

type ReadWriteCloser interface {
    Reader
    Writer
    Closer
}

// Real Go interfaces use this pattern:
// io.ReadWriter = io.Reader + io.Writer
// io.ReadWriteCloser = io.Reader + io.Writer + io.Closer

// Custom composed interface
type Repository interface {
    Finder
    Creator
    Updater
    Deleter
}

type Finder interface {
    FindByID(id uint) (interface{}, error)
    FindAll() ([]interface{}, error)
}

type Creator interface {
    Create(entity interface{}) error
}

type Updater interface {
    Update(entity interface{}) error
}

type Deleter interface {
    Delete(id uint) error
}
```

### Small Interfaces

```go
package main

// Go philosophy: Small, focused interfaces

// BAD: God interface
type UserService interface {
    GetByID(id uint) (*User, error)
    GetByEmail(email string) (*User, error)
    GetAll() ([]*User, error)
    Create(user *User) error
    Update(user *User) error
    Delete(id uint) error
    Login(email, password string) (*Token, error)
    Logout(token string) error
    ResetPassword(email string) error
    VerifyEmail(token string) error
    // 20 more methods...
}

// GOOD: Small, focused interfaces

type UserGetter interface {
    GetByID(id uint) (*User, error)
    GetByEmail(email string) (*User, error)
}

type UserCreator interface {
    Create(user *User) error
}

type UserUpdater interface {
    Update(user *User) error
}

type UserDeleter interface {
    Delete(id uint) error
}

type Authenticator interface {
    Login(email, password string) (*Token, error)
    Logout(token string) error
}

// Compose when needed
type UserRepository interface {
    UserGetter
    UserCreator
    UserUpdater
    UserDeleter
}
```

---

## 5️⃣ SENIOR LEVEL - Interface Best Practices

### Accept Interfaces, Return Structs

```go
package main

import "fmt"

// Interface for dependency
type Logger interface {
    Log(message string)
}

// Concrete implementation
type ConsoleLogger struct{}

func (l *ConsoleLogger) Log(message string) {
    fmt.Println("[LOG]", message)
}

// Another implementation
type FileLogger struct {
    filename string
}

func (l *FileLogger) Log(message string) {
    // Write to file...
    fmt.Printf("[FILE: %s] %s\n", l.filename, message)
}

// Service accepts interface, NOT concrete type
type UserService struct {
    logger Logger // interface, not *ConsoleLogger
}

// Constructor returns concrete type
func NewUserService(logger Logger) *UserService {
    return &UserService{logger: logger}
}

func (s *UserService) CreateUser(name string) {
    s.logger.Log(fmt.Sprintf("Creating user: %s", name))
    // ... create user logic
}

func main() {
    // Can inject any Logger implementation
    consoleLogger := &ConsoleLogger{}
    fileLogger := &FileLogger{filename: "app.log"}
    
    service1 := NewUserService(consoleLogger)
    service1.CreateUser("John") // [LOG] Creating user: John
    
    service2 := NewUserService(fileLogger)
    service2.CreateUser("Jane") // [FILE: app.log] Creating user: Jane
}
```

### Define Interfaces at Consumer Side

```go
// WRONG: Define interface in the package that implements it
// package database
// type UserRepository interface { ... }
// type userRepository struct { ... }

// CORRECT: Define interface in the package that USES it

// ===== package database =====
package database

type User struct {
    ID   uint
    Name string
}

// Just export the concrete type
type UserRepository struct {
    // db connection
}

func (r *UserRepository) FindByID(id uint) (*User, error) {
    // implementation
    return &User{ID: id, Name: "John"}, nil
}

func (r *UserRepository) Create(user *User) error {
    // implementation
    return nil
}

// ===== package userservice =====
package userservice

// Define interface HERE (where it's used)
type UserRepository interface {
    FindByID(id uint) (*User, error)
    Create(user *User) error
}

type UserService struct {
    repo UserRepository
}

func NewUserService(repo UserRepository) *UserService {
    return &UserService{repo: repo}
}

// Now database.UserRepository automatically satisfies
// userservice.UserRepository because Go interfaces are implicit!
```

### Interface Segregation

```go
package main

// Interface Segregation Principle
// Clients should not be forced to depend on interfaces they don't use

// BAD: One big interface
type Worker interface {
    Work()
    Eat()
    Sleep()
}

// Problem: Robot can Work but can't Eat or Sleep!

// GOOD: Segregated interfaces
type Workable interface {
    Work()
}

type Eatable interface {
    Eat()
}

type Sleepable interface {
    Sleep()
}

// Human implements all
type Human struct{}

func (h Human) Work()  { /* ... */ }
func (h Human) Eat()   { /* ... */ }
func (h Human) Sleep() { /* ... */ }

// Robot only implements what it can do
type Robot struct{}

func (r Robot) Work() { /* ... */ }

// Function only requires what it needs
func DoWork(w Workable) {
    w.Work()
}

func main() {
    human := Human{}
    robot := Robot{}
    
    DoWork(human) // Works!
    DoWork(robot) // Works!
}
```

---

## 6️⃣ SENIOR LEVEL - Mocking with Interfaces

### Unit Testing dengan Interface

```go
// user_service.go
package service

type UserRepository interface {
    FindByID(id uint) (*User, error)
    Create(user *User) error
}

type UserService struct {
    repo UserRepository
}

func NewUserService(repo UserRepository) *UserService {
    return &UserService{repo: repo}
}

func (s *UserService) GetUser(id uint) (*User, error) {
    return s.repo.FindByID(id)
}
```

```go
// user_service_test.go
package service

import (
    "errors"
    "testing"
)

// Mock implementation
type MockUserRepository struct {
    users map[uint]*User
    err   error
}

func NewMockUserRepository() *MockUserRepository {
    return &MockUserRepository{
        users: make(map[uint]*User),
    }
}

func (m *MockUserRepository) FindByID(id uint) (*User, error) {
    if m.err != nil {
        return nil, m.err
    }
    user, ok := m.users[id]
    if !ok {
        return nil, errors.New("user not found")
    }
    return user, nil
}

func (m *MockUserRepository) Create(user *User) error {
    if m.err != nil {
        return m.err
    }
    m.users[user.ID] = user
    return nil
}

// Helper to set mock data
func (m *MockUserRepository) WithUser(user *User) *MockUserRepository {
    m.users[user.ID] = user
    return m
}

func (m *MockUserRepository) WithError(err error) *MockUserRepository {
    m.err = err
    return m
}

// Tests
func TestUserService_GetUser_Success(t *testing.T) {
    // Arrange
    mockRepo := NewMockUserRepository().WithUser(&User{
        ID:   1,
        Name: "John",
    })
    service := NewUserService(mockRepo)
    
    // Act
    user, err := service.GetUser(1)
    
    // Assert
    if err != nil {
        t.Errorf("expected no error, got %v", err)
    }
    if user.Name != "John" {
        t.Errorf("expected name John, got %s", user.Name)
    }
}

func TestUserService_GetUser_NotFound(t *testing.T) {
    mockRepo := NewMockUserRepository()
    service := NewUserService(mockRepo)
    
    user, err := service.GetUser(999)
    
    if err == nil {
        t.Error("expected error, got nil")
    }
    if user != nil {
        t.Error("expected nil user")
    }
}
```

### Using testify/mock

```go
// go get github.com/stretchr/testify

package service

import (
    "testing"
    
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
)

// Mock using testify
type MockRepository struct {
    mock.Mock
}

func (m *MockRepository) FindByID(id uint) (*User, error) {
    args := m.Called(id)
    if args.Get(0) == nil {
        return nil, args.Error(1)
    }
    return args.Get(0).(*User), args.Error(1)
}

func (m *MockRepository) Create(user *User) error {
    args := m.Called(user)
    return args.Error(0)
}

func TestUserService_GetUser_WithTestify(t *testing.T) {
    // Arrange
    mockRepo := new(MockRepository)
    mockRepo.On("FindByID", uint(1)).Return(&User{ID: 1, Name: "John"}, nil)
    
    service := NewUserService(mockRepo)
    
    // Act
    user, err := service.GetUser(1)
    
    // Assert
    assert.NoError(t, err)
    assert.Equal(t, "John", user.Name)
    mockRepo.AssertExpectations(t)
}
```

---

## 📊 Interface Cheat Sheet

### Common Patterns

| Pattern | Description |
|---------|-------------|
| `interface{}` / `any` | Accept any type |
| `io.Reader` | Read bytes |
| `io.Writer` | Write bytes |
| `fmt.Stringer` | Custom string representation |
| `error` | Error handling |
| `sort.Interface` | Custom sorting |
| `http.Handler` | HTTP request handling |
| `json.Marshaler` | Custom JSON encoding |

### Interface Rules

| Rule | Explanation |
|------|-------------|
| Implicit | No `implements` keyword needed |
| Duck Typing | If it walks like a duck... |
| Pointer vs Value | Pointer receiver can't be called on value |
| nil interface | Interface is nil only if both type and value are nil |
| Small is better | Prefer 1-3 methods per interface |

### Zero Value

```go
var i interface{}
fmt.Println(i == nil) // true

var s fmt.Stringer // nil
fmt.Println(s == nil) // true

var p *bytes.Buffer // nil pointer
var s2 fmt.Stringer = p
fmt.Println(s2 == nil) // FALSE! (type is not nil)
```

---

## 💡 Summary

| Level | Focus |
|-------|-------|
| **Junior** | Basic interface syntax, implicit implementation |
| **Mid** | Type assertions, common interfaces (io, fmt) |
| **Mid-Senior** | Interface composition, embedding |
| **Senior** | Accept interfaces/return structs, segregation |
| **Expert** | Mocking, testing, dependency injection |

**Best Practices:**
- ✅ Keep interfaces small (1-3 methods)
- ✅ Define interfaces at consumer side
- ✅ Accept interfaces, return concrete types
- ✅ Use interface for dependency injection
- ✅ Use interface for testability (mocking)
- ❌ Don't create interfaces until you need abstraction
- ❌ Don't put interface in same package as implementation
