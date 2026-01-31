# 🚀 GETTING STARTED - Go/Golang (Pemula → Senior)

Dokumentasi lengkap untuk memulai belajar Go dari nol hingga mahir.

---

## 🎯 Kenapa Belajar Go?

```
┌─────────────────────────────────────────────────────────────┐
│                    Why Go?                                   │
├─────────────────────────────────────────────────────────────┤
│  ✅ Fast compilation (seconds, not minutes)                 │
│  ✅ Built-in concurrency (goroutines)                       │
│  ✅ Simple syntax (easy to learn)                           │
│  ✅ Single binary (no dependencies)                         │
│  ✅ Strong typing (catch errors early)                      │
│  ✅ Great standard library                                  │
│  ✅ Used by: Google, Uber, Docker, Kubernetes               │
└─────────────────────────────────────────────────────────────┘
```

**Go vs Other Languages:**
| Feature | Go | Python | Java | Node.js |
|---------|-----|--------|------|---------|
| Speed | ⚡ Very Fast | 🐌 Slow | ⚡ Fast | 🏃 Medium |
| Typing | Static | Dynamic | Static | Dynamic |
| Concurrency | Built-in | Library | Library | Event Loop |
| Binary | Single file | Interpreter | JVM | Runtime |
| Learning Curve | Easy | Very Easy | Hard | Easy |

---

## 1️⃣ PEMULA - Instalasi & Setup

### Install Go

```bash
# Linux (Ubuntu/Debian)
wget https://go.dev/dl/go1.21.5.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz

# Tambah ke PATH (~/.bashrc atau ~/.zshrc)
export PATH=$PATH:/usr/local/go/bin
export GOPATH=$HOME/go
export PATH=$PATH:$GOPATH/bin

# Reload shell
source ~/.bashrc

# Verify installation
go version
# Output: go version go1.21.5 linux/amd64
```

```bash
# Mac (dengan Homebrew)
brew install go

# Windows
# Download dari https://go.dev/dl/ dan install
```

### VS Code Setup

```bash
# Install Go extension
# 1. Buka VS Code
# 2. Ctrl+Shift+X → Search "Go" → Install (by Go Team at Google)
# 3. Ctrl+Shift+P → "Go: Install/Update Tools" → Select all → OK
```

### Project Pertama

```bash
# Buat folder project
mkdir -p ~/projects/hello-go
cd ~/projects/hello-go

# Initialize Go module
go mod init github.com/username/hello-go
# Ini membuat file go.mod (seperti package.json di Node.js)
```

```go
// main.go
package main

import "fmt"

func main() {
    fmt.Println("Hello, World!")
}
```

```bash
# Jalankan
go run main.go
# Output: Hello, World!

# Build ke binary
go build -o hello
./hello
# Output: Hello, World!
```

---

## 2️⃣ PEMULA - Syntax Dasar

### Variables

```go
package main

import "fmt"

func main() {
    // ──────────────────────────────────────
    // Deklarasi dengan var
    // ──────────────────────────────────────
    var name string = "John"
    var age int = 25
    var isActive bool = true
    
    // Type inference (Go otomatis tahu tipenya)
    var city = "Jakarta"  // string
    var score = 95.5      // float64
    
    // ──────────────────────────────────────
    // Short declaration := (paling umum dipakai)
    // ──────────────────────────────────────
    country := "Indonesia"  // string
    year := 2024            // int
    price := 99.99          // float64
    
    // Multiple variables
    var x, y, z int = 1, 2, 3
    a, b, c := "one", "two", "three"
    
    // ──────────────────────────────────────
    // Constants
    // ──────────────────────────────────────
    const PI = 3.14159
    const AppName = "MyApp"
    
    fmt.Println(name, age, isActive)
    fmt.Println(city, score, country, year, price)
    fmt.Println(x, y, z, a, b, c)
    fmt.Println(PI, AppName)
}
```

### Data Types

```go
package main

import "fmt"

func main() {
    // ──────────────────────────────────────
    // Basic Types
    // ──────────────────────────────────────
    
    // Integer
    var i int = 42        // Platform-dependent (32/64 bit)
    var i8 int8 = 127     // -128 to 127
    var i16 int16 = 32767
    var i32 int32 = 2147483647
    var i64 int64 = 9223372036854775807
    
    // Unsigned Integer
    var u uint = 42
    var u8 uint8 = 255    // 0 to 255 (byte)
    var u16 uint16 = 65535
    
    // Float
    var f32 float32 = 3.14
    var f64 float64 = 3.14159265359  // Default untuk decimal
    
    // String
    var s string = "Hello, Go!"
    
    // Boolean
    var b bool = true
    
    // ──────────────────────────────────────
    // Zero Values (default value jika tidak diisi)
    // ──────────────────────────────────────
    var defaultInt int       // 0
    var defaultFloat float64 // 0.0
    var defaultString string // "" (empty string)
    var defaultBool bool     // false
    
    fmt.Println(i, i8, i16, i32, i64)
    fmt.Println(u, u8, u16)
    fmt.Println(f32, f64)
    fmt.Println(s, b)
    fmt.Println(defaultInt, defaultFloat, defaultString, defaultBool)
}
```

### Control Flow

```go
package main

import "fmt"

func main() {
    // ──────────────────────────────────────
    // If-Else
    // ──────────────────────────────────────
    age := 20
    
    if age >= 18 {
        fmt.Println("Adult")
    } else if age >= 13 {
        fmt.Println("Teenager")
    } else {
        fmt.Println("Child")
    }
    
    // If dengan statement (variable scope hanya di dalam if)
    if score := 85; score >= 80 {
        fmt.Println("Grade: A")
    }
    
    // ──────────────────────────────────────
    // Switch
    // ──────────────────────────────────────
    day := "Monday"
    
    switch day {
    case "Monday", "Tuesday", "Wednesday", "Thursday", "Friday":
        fmt.Println("Weekday")
    case "Saturday", "Sunday":
        fmt.Println("Weekend")
    default:
        fmt.Println("Unknown")
    }
    
    // Switch tanpa expression (seperti if-else chain)
    score := 85
    switch {
    case score >= 90:
        fmt.Println("A")
    case score >= 80:
        fmt.Println("B")
    case score >= 70:
        fmt.Println("C")
    default:
        fmt.Println("F")
    }
    
    // ──────────────────────────────────────
    // For Loop (Go hanya punya for, tidak ada while)
    // ──────────────────────────────────────
    
    // Standard for
    for i := 0; i < 5; i++ {
        fmt.Println(i)
    }
    
    // For seperti while
    count := 0
    for count < 5 {
        fmt.Println(count)
        count++
    }
    
    // Infinite loop
    // for {
    //     fmt.Println("Forever")
    //     break  // Harus ada break!
    // }
    
    // For dengan range (untuk slice, map, string)
    fruits := []string{"apple", "banana", "cherry"}
    for index, fruit := range fruits {
        fmt.Printf("Index %d: %s\n", index, fruit)
    }
    
    // Ignore index
    for _, fruit := range fruits {
        fmt.Println(fruit)
    }
}
```

### Functions

```go
package main

import "fmt"

// ──────────────────────────────────────
// Basic function
// ──────────────────────────────────────
func sayHello() {
    fmt.Println("Hello!")
}

// ──────────────────────────────────────
// Function dengan parameter
// ──────────────────────────────────────
func greet(name string) {
    fmt.Printf("Hello, %s!\n", name)
}

// ──────────────────────────────────────
// Function dengan return value
// ──────────────────────────────────────
func add(a, b int) int {
    return a + b
}

// ──────────────────────────────────────
// Multiple return values (SANGAT UMUM di Go)
// ──────────────────────────────────────
func divide(a, b float64) (float64, error) {
    if b == 0 {
        return 0, fmt.Errorf("cannot divide by zero")
    }
    return a / b, nil
}

// ──────────────────────────────────────
// Named return values
// ──────────────────────────────────────
func calculate(a, b int) (sum, diff int) {
    sum = a + b
    diff = a - b
    return  // Naked return
}

// ──────────────────────────────────────
// Variadic function (flexible arguments)
// ──────────────────────────────────────
func sum(numbers ...int) int {
    total := 0
    for _, n := range numbers {
        total += n
    }
    return total
}

func main() {
    sayHello()
    greet("John")
    
    result := add(5, 3)
    fmt.Println("5 + 3 =", result)
    
    // Handle multiple return values
    quotient, err := divide(10, 2)
    if err != nil {
        fmt.Println("Error:", err)
    } else {
        fmt.Println("10 / 2 =", quotient)
    }
    
    // Ignore one return value dengan _
    quotient2, _ := divide(20, 4)
    fmt.Println("20 / 4 =", quotient2)
    
    s, d := calculate(10, 3)
    fmt.Printf("Sum: %d, Diff: %d\n", s, d)
    
    fmt.Println("Sum:", sum(1, 2, 3, 4, 5))
}
```

---

## 3️⃣ PEMULA - Data Structures

### Arrays & Slices

```go
package main

import "fmt"

func main() {
    // ──────────────────────────────────────
    // Array (fixed size) - Jarang dipakai langsung
    // ──────────────────────────────────────
    var arr [5]int = [5]int{1, 2, 3, 4, 5}
    arr2 := [3]string{"a", "b", "c"}
    arr3 := [...]int{1, 2, 3}  // Size dari elements
    
    fmt.Println(arr, arr2, arr3)
    fmt.Println("Length:", len(arr))
    fmt.Println("First element:", arr[0])
    
    // ──────────────────────────────────────
    // Slice (dynamic size) - PALING SERING DIPAKAI
    // ──────────────────────────────────────
    
    // Create slice
    slice1 := []int{1, 2, 3, 4, 5}
    slice2 := make([]int, 5)      // Length 5, all zeros
    slice3 := make([]int, 5, 10)  // Length 5, capacity 10
    
    fmt.Println(slice1, slice2, slice3)
    fmt.Println("Length:", len(slice1), "Capacity:", cap(slice1))
    
    // Append elements
    slice1 = append(slice1, 6)
    slice1 = append(slice1, 7, 8, 9)
    fmt.Println("After append:", slice1)
    
    // Slice dari slice
    subSlice := slice1[2:5]  // Index 2, 3, 4
    fmt.Println("Sub slice [2:5]:", subSlice)
    
    // Copy slice
    dest := make([]int, len(slice1))
    copy(dest, slice1)
    fmt.Println("Copied:", dest)
    
    // ──────────────────────────────────────
    // Common slice operations
    // ──────────────────────────────────────
    
    // Remove element at index
    s := []int{1, 2, 3, 4, 5}
    i := 2  // Remove index 2 (value 3)
    s = append(s[:i], s[i+1:]...)
    fmt.Println("After remove index 2:", s)  // [1 2 4 5]
    
    // Insert element at index
    s2 := []int{1, 2, 4, 5}
    idx := 2
    val := 3
    s2 = append(s2[:idx], append([]int{val}, s2[idx:]...)...)
    fmt.Println("After insert 3 at index 2:", s2)  // [1 2 3 4 5]
}
```

### Maps

```go
package main

import "fmt"

func main() {
    // ──────────────────────────────────────
    // Create Map
    // ──────────────────────────────────────
    
    // Method 1: make
    m := make(map[string]int)
    m["one"] = 1
    m["two"] = 2
    m["three"] = 3
    
    // Method 2: literal
    user := map[string]string{
        "name":  "John",
        "email": "john@example.com",
        "city":  "Jakarta",
    }
    
    fmt.Println(m)
    fmt.Println(user)
    
    // ──────────────────────────────────────
    // Access & Modify
    // ──────────────────────────────────────
    
    // Get value
    name := user["name"]
    fmt.Println("Name:", name)
    
    // Check if key exists
    email, exists := user["email"]
    if exists {
        fmt.Println("Email:", email)
    }
    
    // Key not found returns zero value
    phone := user["phone"]  // Returns "" (empty string)
    fmt.Println("Phone:", phone)
    
    // Better way to check
    if phone, ok := user["phone"]; ok {
        fmt.Println("Phone:", phone)
    } else {
        fmt.Println("Phone not found")
    }
    
    // Update value
    user["city"] = "Bandung"
    
    // Delete key
    delete(user, "city")
    
    // ──────────────────────────────────────
    // Iterate Map
    // ──────────────────────────────────────
    for key, value := range user {
        fmt.Printf("%s: %s\n", key, value)
    }
    
    // Only keys
    for key := range user {
        fmt.Println("Key:", key)
    }
    
    // ──────────────────────────────────────
    // Nested Map
    // ──────────────────────────────────────
    users := map[string]map[string]string{
        "user1": {
            "name":  "John",
            "email": "john@example.com",
        },
        "user2": {
            "name":  "Jane",
            "email": "jane@example.com",
        },
    }
    
    fmt.Println(users["user1"]["name"])  // John
}
```

### Structs

```go
package main

import "fmt"

// ──────────────────────────────────────
// Define Struct
// ──────────────────────────────────────
type User struct {
    ID        int
    Name      string
    Email     string
    Age       int
    IsActive  bool
}

// ──────────────────────────────────────
// Struct with tags (untuk JSON, DB, dll)
// ──────────────────────────────────────
type Task struct {
    ID          int    `json:"id"`
    Title       string `json:"title"`
    Description string `json:"description,omitempty"`
    Status      string `json:"status"`
    Priority    int    `json:"priority"`
}

// ──────────────────────────────────────
// Method pada Struct
// ──────────────────────────────────────
func (u User) FullInfo() string {
    return fmt.Sprintf("%s (%s) - Age: %d", u.Name, u.Email, u.Age)
}

// Method dengan pointer receiver (bisa modify struct)
func (u *User) SetEmail(email string) {
    u.Email = email
}

func (u *User) Birthday() {
    u.Age++
}

// ──────────────────────────────────────
// Constructor pattern (Go tidak punya class)
// ──────────────────────────────────────
func NewUser(id int, name, email string, age int) *User {
    return &User{
        ID:       id,
        Name:     name,
        Email:    email,
        Age:      age,
        IsActive: true,
    }
}

func main() {
    // Create struct - Method 1
    var user1 User
    user1.ID = 1
    user1.Name = "John"
    user1.Email = "john@example.com"
    user1.Age = 25
    user1.IsActive = true
    
    // Create struct - Method 2 (recommended)
    user2 := User{
        ID:       2,
        Name:     "Jane",
        Email:    "jane@example.com",
        Age:      30,
        IsActive: true,
    }
    
    // Create struct - Method 3 (dengan constructor)
    user3 := NewUser(3, "Bob", "bob@example.com", 28)
    
    // Access fields
    fmt.Println(user1.Name)
    fmt.Println(user2.Email)
    fmt.Println(user3.Age)
    
    // Call methods
    fmt.Println(user1.FullInfo())
    
    user2.SetEmail("jane.new@example.com")
    fmt.Println(user2.Email)
    
    user3.Birthday()
    fmt.Println("New age:", user3.Age)
    
    // ──────────────────────────────────────
    // Embedded Struct (Composition)
    // ──────────────────────────────────────
    type Address struct {
        Street  string
        City    string
        Country string
    }
    
    type Person struct {
        Name    string
        Age     int
        Address // Embedded (bukan Address Address)
    }
    
    person := Person{
        Name: "John",
        Age:  25,
        Address: Address{
            Street:  "Jl. Sudirman",
            City:    "Jakarta",
            Country: "Indonesia",
        },
    }
    
    // Access embedded fields langsung
    fmt.Println(person.City)     // Jakarta (shortcut)
    fmt.Println(person.Address.City)  // Jakarta (full path)
}
```

---

## 4️⃣ PEMULA-MENENGAH - Pointers

```go
package main

import "fmt"

func main() {
    // ──────────────────────────────────────
    // Pointer Basics
    // ──────────────────────────────────────
    
    x := 10
    
    // & = address of (get pointer)
    ptr := &x
    
    fmt.Println("Value of x:", x)        // 10
    fmt.Println("Address of x:", ptr)    // 0xc000018088 (contoh)
    fmt.Println("Value at ptr:", *ptr)   // 10 (dereference)
    
    // * = dereference (get value from pointer)
    *ptr = 20  // Modify value melalui pointer
    fmt.Println("New value of x:", x)    // 20
    
    // ──────────────────────────────────────
    // Pointer dengan Function
    // ──────────────────────────────────────
    
    // Pass by value (copy)
    num := 100
    doubleValue(num)
    fmt.Println("After doubleValue:", num)  // 100 (tidak berubah)
    
    // Pass by pointer (reference)
    doublePointer(&num)
    fmt.Println("After doublePointer:", num)  // 200 (berubah!)
    
    // ──────────────────────────────────────
    // Pointer dengan Struct
    // ──────────────────────────────────────
    
    type User struct {
        Name string
        Age  int
    }
    
    user := User{Name: "John", Age: 25}
    userPtr := &user
    
    // Akses field via pointer (Go otomatis dereference)
    userPtr.Age = 30  // Sama dengan (*userPtr).Age = 30
    fmt.Println(user.Age)  // 30
    
    // ──────────────────────────────────────
    // new() - allocate memory, return pointer
    // ──────────────────────────────────────
    
    numPtr := new(int)  // Pointer ke int dengan value 0
    *numPtr = 42
    fmt.Println(*numPtr)  // 42
    
    userPtr2 := new(User)  // Pointer ke User dengan zero values
    userPtr2.Name = "Jane"
    fmt.Println(userPtr2.Name)  // Jane
}

func doubleValue(n int) {
    n = n * 2  // Modify copy, original tidak berubah
}

func doublePointer(n *int) {
    *n = *n * 2  // Modify original
}
```

**Kapan pakai pointer?**
```go
// ✅ Pakai pointer ketika:
// 1. Ingin modify data original
// 2. Struct besar (hindari copy)
// 3. Data bisa nil

// ❌ Tidak perlu pointer untuk:
// 1. int, float, bool kecil
// 2. Slice, map, channel (sudah reference)
```

---

## 5️⃣ PEMULA-MENENGAH - Error Handling

```go
package main

import (
    "errors"
    "fmt"
)

// ──────────────────────────────────────
// Go tidak punya exceptions!
// Error handling dengan return value
// ──────────────────────────────────────

func divide(a, b float64) (float64, error) {
    if b == 0 {
        return 0, errors.New("cannot divide by zero")
    }
    return a / b, nil
}

// Custom error dengan fmt.Errorf
func findUser(id int) (string, error) {
    if id <= 0 {
        return "", fmt.Errorf("invalid user id: %d", id)
    }
    if id > 100 {
        return "", fmt.Errorf("user not found: %d", id)
    }
    return "John Doe", nil
}

// Custom Error Type
type ValidationError struct {
    Field   string
    Message string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("%s: %s", e.Field, e.Message)
}

func validateAge(age int) error {
    if age < 0 {
        return &ValidationError{
            Field:   "age",
            Message: "cannot be negative",
        }
    }
    if age > 150 {
        return &ValidationError{
            Field:   "age",
            Message: "unrealistic age",
        }
    }
    return nil
}

func main() {
    // ──────────────────────────────────────
    // Basic error handling
    // ──────────────────────────────────────
    
    result, err := divide(10, 2)
    if err != nil {
        fmt.Println("Error:", err)
        return
    }
    fmt.Println("Result:", result)
    
    // Error case
    result2, err := divide(10, 0)
    if err != nil {
        fmt.Println("Error:", err)  // Error: cannot divide by zero
    } else {
        fmt.Println("Result:", result2)
    }
    
    // ──────────────────────────────────────
    // Multiple error handling
    // ──────────────────────────────────────
    
    user, err := findUser(-1)
    if err != nil {
        fmt.Println("Error:", err)  // Error: invalid user id: -1
    } else {
        fmt.Println("User:", user)
    }
    
    // ──────────────────────────────────────
    // Custom error type
    // ──────────────────────────────────────
    
    err = validateAge(-5)
    if err != nil {
        // Type assertion untuk get custom error
        if ve, ok := err.(*ValidationError); ok {
            fmt.Printf("Validation error - Field: %s, Message: %s\n", 
                ve.Field, ve.Message)
        }
    }
    
    // ──────────────────────────────────────
    // errors.Is dan errors.As (Go 1.13+)
    // ──────────────────────────────────────
    
    var ErrNotFound = errors.New("not found")
    var ErrUnauthorized = errors.New("unauthorized")
    
    err = fmt.Errorf("user query failed: %w", ErrNotFound)  // Wrap error
    
    if errors.Is(err, ErrNotFound) {
        fmt.Println("Handle not found error")
    }
    
    // errors.As untuk custom error types
    var valErr *ValidationError
    err = validateAge(200)
    if errors.As(err, &valErr) {
        fmt.Println("Validation failed:", valErr.Field)
    }
}
```

---

## 📊 Quick Reference

### Go vs Python Comparison

| Konsep | Python | Go |
|--------|--------|-----|
| Variable | `name = "John"` | `name := "John"` |
| Function | `def add(a, b):` | `func add(a, b int) int` |
| If | `if x > 0:` | `if x > 0 {` |
| For | `for i in range(5):` | `for i := 0; i < 5; i++ {` |
| List/Array | `arr = [1, 2, 3]` | `arr := []int{1, 2, 3}` |
| Dict/Map | `d = {"a": 1}` | `m := map[string]int{"a": 1}` |
| Class/Struct | `class User:` | `type User struct {` |
| Error | `raise Exception` | `return error` |
| Import | `import os` | `import "os"` |

### Cheat Sheet

```go
// Variable
name := "John"
var age int = 25

// Function
func add(a, b int) int {
    return a + b
}

// Multiple return
func divide(a, b int) (int, error) {
    if b == 0 {
        return 0, errors.New("divide by zero")
    }
    return a / b, nil
}

// Struct
type User struct {
    Name string
    Age  int
}

// Method
func (u *User) Birthday() {
    u.Age++
}

// Slice
nums := []int{1, 2, 3}
nums = append(nums, 4)

// Map
m := map[string]int{"a": 1}
m["b"] = 2
delete(m, "a")

// Error handling
result, err := someFunc()
if err != nil {
    return err
}
```

---

## 💡 Summary

| Level | Topik |
|-------|-------|
| **Pemula** | Variables, Types, Control Flow |
| **Pemula** | Functions, Arrays, Slices, Maps |
| **Pemula** | Structs, Methods |
| **Pemula-Menengah** | Pointers, Error Handling |
| **Menengah** | Interfaces, Goroutines (next docs) |

**Tips untuk Pemula:**
- ✅ Mulai dengan syntax dasar
- ✅ Selalu handle error (`if err != nil`)
- ✅ Pakai `:=` untuk deklarasi singkat
- ✅ Pelajari slice, bukan array
- ✅ Eksperimen di Go Playground: https://go.dev/play/

**Next Steps:**
1. Baca ARCHITECTURE.md → Project structure
2. Baca INTERFACES.md → Polymorphism
3. Baca CONCURRENCY.md → Goroutines
