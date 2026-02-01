# 🏎️ Race Conditions & Data Races di Go

## Kenapa Penting?

Race conditions bisa menyebabkan:
- ❌ Data corruption
- ❌ Unpredictable behavior
- ❌ Hard-to-debug bugs
- ❌ Security vulnerabilities

---

## 📚 Daftar Isi

1. [Apa itu Race Condition?](#1️⃣-apa-itu-race-condition)
2. [Race Detector](#2️⃣-race-detector)
3. [sync/atomic Package](#3️⃣-syncatomic-package)
4. [Common Race Patterns](#4️⃣-common-race-patterns)
5. [Prevention Strategies](#5️⃣-prevention-strategies)
6. [Real-World Examples](#6️⃣-real-world-examples)

---

## 1️⃣ Apa itu Race Condition?

### Definition

```
Data Race terjadi ketika:
1. Dua atau lebih goroutines mengakses memori yang sama
2. Setidaknya satu akses adalah WRITE
3. Tidak ada synchronization

Race Condition = Bug yang terjadi karena timing/ordering goroutines
```

### Simple Example

```go
// ❌ RACE CONDITION!
package main

import (
    "fmt"
    "sync"
)

func main() {
    counter := 0
    var wg sync.WaitGroup
    
    for i := 0; i < 1000; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            counter++ // ❌ Race! Multiple goroutines read-modify-write
        }()
    }
    
    wg.Wait()
    fmt.Println("Counter:", counter) // Expected: 1000, Actual: varies (e.g., 987, 952, 1000)
}
```

### Why It Happens

```
counter++ is NOT atomic. It's actually 3 operations:

1. READ:  temp = counter    (read current value)
2. ADD:   temp = temp + 1   (increment)
3. WRITE: counter = temp    (write back)

When 2 goroutines do this simultaneously:

Goroutine A          Goroutine B          counter
-----------          -----------          -------
READ (0)                                     0
                     READ (0)                0
ADD (1)                                      0
                     ADD (1)                 0
WRITE (1)                                    1
                     WRITE (1)               1  ← Lost update!

Both incremented, but counter only went from 0 → 1
```

---

## 2️⃣ Race Detector

### Menjalankan Race Detector

```bash
# Run with race detector
go run -race main.go

# Test with race detector
go test -race ./...

# Build with race detector
go build -race -o myapp

# Run tests with race detection
go test -race -v ./...
```

### Output Race Detector

```go
// main.go
package main

import (
    "sync"
)

func main() {
    counter := 0
    var wg sync.WaitGroup
    
    for i := 0; i < 100; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            counter++
        }()
    }
    
    wg.Wait()
}
```

```bash
$ go run -race main.go

==================
WARNING: DATA RACE
Read at 0x00c0000b4010 by goroutine 8:
  main.main.func1()
      /path/to/main.go:15 +0x4e

Previous write at 0x00c0000b4010 by goroutine 7:
  main.main.func1()
      /path/to/main.go:15 +0x64

Goroutine 8 (running) created at:
  main.main()
      /path/to/main.go:13 +0x88

Goroutine 7 (finished) created at:
  main.main()
      /path/to/main.go:13 +0x88
==================
Found 1 data race(s)
exit status 66
```

### CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Go
        uses: actions/setup-go@v4
        with:
          go-version: '1.21'
      
      - name: Test with Race Detector
        run: go test -race -v ./...
```

---

## 3️⃣ sync/atomic Package

### Atomic Counter

```go
package main

import (
    "fmt"
    "sync"
    "sync/atomic"
)

func main() {
    var counter int64 = 0 // Must use int32, int64, uint32, uint64
    var wg sync.WaitGroup
    
    for i := 0; i < 1000; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            atomic.AddInt64(&counter, 1) // ✅ Atomic increment
        }()
    }
    
    wg.Wait()
    fmt.Println("Counter:", counter) // Always 1000
}
```

### Atomic Operations

```go
package main

import (
    "fmt"
    "sync/atomic"
)

func main() {
    var value int64 = 0
    
    // Add
    atomic.AddInt64(&value, 10)
    fmt.Println("After Add:", value) // 10
    
    // Store
    atomic.StoreInt64(&value, 100)
    fmt.Println("After Store:", value) // 100
    
    // Load
    current := atomic.LoadInt64(&value)
    fmt.Println("Load:", current) // 100
    
    // Swap
    old := atomic.SwapInt64(&value, 200)
    fmt.Println("Swap - Old:", old, "New:", value) // Old: 100, New: 200
    
    // Compare and Swap (CAS)
    swapped := atomic.CompareAndSwapInt64(&value, 200, 300)
    fmt.Println("CAS success:", swapped, "Value:", value) // true, 300
    
    swapped = atomic.CompareAndSwapInt64(&value, 200, 400) // Won't swap
    fmt.Println("CAS success:", swapped, "Value:", value) // false, 300
}
```

### atomic.Value (Store Any Type)

```go
package main

import (
    "fmt"
    "sync"
    "sync/atomic"
)

type Config struct {
    MaxConnections int
    Timeout        int
}

var configValue atomic.Value

func main() {
    // Initial config
    config := &Config{MaxConnections: 10, Timeout: 30}
    configValue.Store(config)
    
    var wg sync.WaitGroup
    
    // Readers
    for i := 0; i < 10; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()
            cfg := configValue.Load().(*Config)
            fmt.Printf("Reader %d: MaxConn=%d\n", id, cfg.MaxConnections)
        }(i)
    }
    
    // Writer (update config)
    wg.Add(1)
    go func() {
        defer wg.Done()
        newConfig := &Config{MaxConnections: 20, Timeout: 60}
        configValue.Store(newConfig)
        fmt.Println("Config updated")
    }()
    
    wg.Wait()
}
```

### atomic.Bool, atomic.Int64, atomic.Pointer (Go 1.19+)

```go
package main

import (
    "fmt"
    "sync"
    "sync/atomic"
)

func main() {
    // atomic.Bool
    var isRunning atomic.Bool
    isRunning.Store(true)
    fmt.Println("Running:", isRunning.Load()) // true
    
    // atomic.Int64
    var counter atomic.Int64
    counter.Add(10)
    counter.Add(5)
    fmt.Println("Counter:", counter.Load()) // 15
    
    // atomic.Pointer
    type User struct {
        Name string
    }
    
    var currentUser atomic.Pointer[User]
    currentUser.Store(&User{Name: "Alice"})
    fmt.Println("User:", currentUser.Load().Name) // Alice
    
    // Swap
    oldUser := currentUser.Swap(&User{Name: "Bob"})
    fmt.Println("Old:", oldUser.Name, "New:", currentUser.Load().Name)
}
```

---

## 4️⃣ Common Race Patterns

### Pattern 1: Map Concurrent Access

```go
// ❌ RACE CONDITION
package main

import "sync"

func main() {
    m := make(map[string]int)
    var wg sync.WaitGroup
    
    for i := 0; i < 100; i++ {
        wg.Add(1)
        go func(n int) {
            defer wg.Done()
            m["key"] = n // ❌ Concurrent map write!
        }(i)
    }
    
    wg.Wait()
}
// panic: concurrent map writes
```

```go
// ✅ SOLUTION 1: sync.Mutex
package main

import "sync"

func main() {
    m := make(map[string]int)
    var mu sync.Mutex
    var wg sync.WaitGroup
    
    for i := 0; i < 100; i++ {
        wg.Add(1)
        go func(n int) {
            defer wg.Done()
            mu.Lock()
            m["key"] = n
            mu.Unlock()
        }(i)
    }
    
    wg.Wait()
}
```

```go
// ✅ SOLUTION 2: sync.Map
package main

import "sync"

func main() {
    var m sync.Map
    var wg sync.WaitGroup
    
    for i := 0; i < 100; i++ {
        wg.Add(1)
        go func(n int) {
            defer wg.Done()
            m.Store("key", n) // ✅ Thread-safe
        }(i)
    }
    
    wg.Wait()
    
    value, _ := m.Load("key")
    println("Value:", value.(int))
}
```

### Pattern 2: Slice Append

```go
// ❌ RACE CONDITION
package main

import "sync"

func main() {
    var results []int
    var wg sync.WaitGroup
    
    for i := 0; i < 100; i++ {
        wg.Add(1)
        go func(n int) {
            defer wg.Done()
            results = append(results, n) // ❌ Race!
        }(i)
    }
    
    wg.Wait()
    println("Length:", len(results)) // Unpredictable
}
```

```go
// ✅ SOLUTION 1: Mutex
package main

import "sync"

func main() {
    var results []int
    var mu sync.Mutex
    var wg sync.WaitGroup
    
    for i := 0; i < 100; i++ {
        wg.Add(1)
        go func(n int) {
            defer wg.Done()
            mu.Lock()
            results = append(results, n)
            mu.Unlock()
        }(i)
    }
    
    wg.Wait()
    println("Length:", len(results)) // Always 100
}
```

```go
// ✅ SOLUTION 2: Channel
package main

import "sync"

func main() {
    resultCh := make(chan int, 100)
    var wg sync.WaitGroup
    
    for i := 0; i < 100; i++ {
        wg.Add(1)
        go func(n int) {
            defer wg.Done()
            resultCh <- n
        }(i)
    }
    
    // Collect results in single goroutine
    go func() {
        wg.Wait()
        close(resultCh)
    }()
    
    var results []int
    for r := range resultCh {
        results = append(results, r)
    }
    
    println("Length:", len(results)) // Always 100
}
```

### Pattern 3: Check-then-Act

```go
// ❌ RACE CONDITION: Check-then-Act
package main

import "sync"

type SafeCounter struct {
    value int
    mu    sync.Mutex
}

func (c *SafeCounter) IncrementIfLessThan(limit int) {
    c.mu.Lock()
    current := c.value
    c.mu.Unlock() // ❌ Released lock between check and act!
    
    if current < limit {
        c.mu.Lock()
        c.value++ // ❌ Race! Value might have changed
        c.mu.Unlock()
    }
}
```

```go
// ✅ SOLUTION: Keep lock during entire operation
package main

import "sync"

type SafeCounter struct {
    value int
    mu    sync.Mutex
}

func (c *SafeCounter) IncrementIfLessThan(limit int) bool {
    c.mu.Lock()
    defer c.mu.Unlock()
    
    if c.value < limit {
        c.value++
        return true
    }
    return false
}
```

### Pattern 4: Lazy Initialization

```go
// ❌ RACE CONDITION
package main

import "sync"

type Service struct{}

var instance *Service

func GetInstance() *Service {
    if instance == nil { // ❌ Race: multiple goroutines can pass this check
        instance = &Service{}
    }
    return instance
}
```

```go
// ✅ SOLUTION: sync.Once
package main

import "sync"

type Service struct{}

var (
    instance *Service
    once     sync.Once
)

func GetInstance() *Service {
    once.Do(func() {
        instance = &Service{}
    })
    return instance
}
```

### Pattern 5: Shared State in Struct

```go
// ❌ RACE CONDITION
package main

import (
    "sync"
    "time"
)

type Stats struct {
    Requests int
    Errors   int
}

func main() {
    stats := &Stats{}
    var wg sync.WaitGroup
    
    for i := 0; i < 100; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            stats.Requests++ // ❌ Race
            if time.Now().UnixNano()%2 == 0 {
                stats.Errors++ // ❌ Race
            }
        }()
    }
    
    wg.Wait()
}
```

```go
// ✅ SOLUTION: Embed mutex or use atomic
package main

import (
    "sync"
    "sync/atomic"
    "time"
)

// Option 1: Embed Mutex
type Stats struct {
    mu       sync.Mutex
    Requests int
    Errors   int
}

func (s *Stats) RecordRequest() {
    s.mu.Lock()
    defer s.mu.Unlock()
    s.Requests++
}

func (s *Stats) RecordError() {
    s.mu.Lock()
    defer s.mu.Unlock()
    s.Errors++
}

// Option 2: Atomic
type AtomicStats struct {
    Requests atomic.Int64
    Errors   atomic.Int64
}

func main() {
    stats := &AtomicStats{}
    var wg sync.WaitGroup
    
    for i := 0; i < 100; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            stats.Requests.Add(1) // ✅ Atomic
            if time.Now().UnixNano()%2 == 0 {
                stats.Errors.Add(1) // ✅ Atomic
            }
        }()
    }
    
    wg.Wait()
    println("Requests:", stats.Requests.Load())
    println("Errors:", stats.Errors.Load())
}
```

---

## 5️⃣ Prevention Strategies

### Strategy 1: Avoid Shared State

```go
// ❌ Shared state
func processItems(items []int, result *int) {
    for _, item := range items {
        *result += item // Shared state
    }
}

// ✅ Return value instead
func processItems(items []int) int {
    sum := 0
    for _, item := range items {
        sum += item
    }
    return sum
}

// ✅ Use channels to collect results
func processItemsConcurrent(items []int) int {
    resultCh := make(chan int)
    
    go func() {
        sum := 0
        for _, item := range items {
            sum += item
        }
        resultCh <- sum
    }()
    
    return <-resultCh
}
```

### Strategy 2: Confine Data to Single Goroutine

```go
// ✅ Each goroutine owns its data
func processConcurrent(items [][]int) []int {
    results := make(chan int, len(items))
    
    for _, batch := range items {
        go func(data []int) { // Each goroutine owns 'data'
            sum := 0
            for _, n := range data {
                sum += n
            }
            results <- sum
        }(batch)
    }
    
    var totals []int
    for i := 0; i < len(items); i++ {
        totals = append(totals, <-results)
    }
    
    return totals
}
```

### Strategy 3: Use Channels for Communication

```go
// ✅ "Don't communicate by sharing memory; share memory by communicating"
package main

type Counter struct {
    value int
    inc   chan struct{}
    get   chan int
}

func NewCounter() *Counter {
    c := &Counter{
        inc: make(chan struct{}),
        get: make(chan int),
    }
    
    go c.run()
    
    return c
}

func (c *Counter) run() {
    for {
        select {
        case <-c.inc:
            c.value++
        case c.get <- c.value:
        }
    }
}

func (c *Counter) Increment() {
    c.inc <- struct{}{}
}

func (c *Counter) Value() int {
    return <-c.get
}

func main() {
    counter := NewCounter()
    
    // Safe to use from multiple goroutines
    for i := 0; i < 100; i++ {
        go counter.Increment()
    }
    
    // Wait a bit and read
    time.Sleep(100 * time.Millisecond)
    println("Value:", counter.Value())
}
```

### Strategy 4: Use sync Package

```go
// ✅ Use appropriate sync primitives
package main

import "sync"

type SafeMap struct {
    mu   sync.RWMutex
    data map[string]int
}

func NewSafeMap() *SafeMap {
    return &SafeMap{
        data: make(map[string]int),
    }
}

func (m *SafeMap) Get(key string) (int, bool) {
    m.mu.RLock()
    defer m.mu.RUnlock()
    val, ok := m.data[key]
    return val, ok
}

func (m *SafeMap) Set(key string, value int) {
    m.mu.Lock()
    defer m.mu.Unlock()
    m.data[key] = value
}

func (m *SafeMap) Delete(key string) {
    m.mu.Lock()
    defer m.mu.Unlock()
    delete(m.data, key)
}
```

---

## 6️⃣ Real-World Examples

### Thread-Safe Rate Limiter

```go
package main

import (
    "sync"
    "sync/atomic"
    "time"
)

type RateLimiter struct {
    tokens    atomic.Int64
    maxTokens int64
    refillRate time.Duration
    mu        sync.Mutex
    lastRefill time.Time
}

func NewRateLimiter(maxTokens int64, refillRate time.Duration) *RateLimiter {
    rl := &RateLimiter{
        maxTokens:  maxTokens,
        refillRate: refillRate,
        lastRefill: time.Now(),
    }
    rl.tokens.Store(maxTokens)
    return rl
}

func (rl *RateLimiter) Allow() bool {
    rl.refill()
    
    for {
        current := rl.tokens.Load()
        if current <= 0 {
            return false
        }
        
        if rl.tokens.CompareAndSwap(current, current-1) {
            return true
        }
    }
}

func (rl *RateLimiter) refill() {
    rl.mu.Lock()
    defer rl.mu.Unlock()
    
    now := time.Now()
    elapsed := now.Sub(rl.lastRefill)
    tokensToAdd := int64(elapsed / rl.refillRate)
    
    if tokensToAdd > 0 {
        current := rl.tokens.Load()
        newTokens := min(current+tokensToAdd, rl.maxTokens)
        rl.tokens.Store(newTokens)
        rl.lastRefill = now
    }
}
```

### Thread-Safe Cache

```go
package main

import (
    "sync"
    "time"
)

type CacheItem struct {
    Value      interface{}
    Expiration time.Time
}

type Cache struct {
    mu    sync.RWMutex
    items map[string]CacheItem
}

func NewCache() *Cache {
    c := &Cache{
        items: make(map[string]CacheItem),
    }
    go c.cleanup()
    return c
}

func (c *Cache) Set(key string, value interface{}, ttl time.Duration) {
    c.mu.Lock()
    defer c.mu.Unlock()
    
    c.items[key] = CacheItem{
        Value:      value,
        Expiration: time.Now().Add(ttl),
    }
}

func (c *Cache) Get(key string) (interface{}, bool) {
    c.mu.RLock()
    defer c.mu.RUnlock()
    
    item, found := c.items[key]
    if !found {
        return nil, false
    }
    
    if time.Now().After(item.Expiration) {
        return nil, false
    }
    
    return item.Value, true
}

func (c *Cache) Delete(key string) {
    c.mu.Lock()
    defer c.mu.Unlock()
    delete(c.items, key)
}

func (c *Cache) cleanup() {
    ticker := time.NewTicker(time.Minute)
    defer ticker.Stop()
    
    for range ticker.C {
        c.mu.Lock()
        now := time.Now()
        for key, item := range c.items {
            if now.After(item.Expiration) {
                delete(c.items, key)
            }
        }
        c.mu.Unlock()
    }
}
```

### Connection Pool

```go
package main

import (
    "errors"
    "sync"
)

type Connection struct {
    ID int
}

type Pool struct {
    mu          sync.Mutex
    connections chan *Connection
    maxSize     int
    created     int
}

func NewPool(maxSize int) *Pool {
    return &Pool{
        connections: make(chan *Connection, maxSize),
        maxSize:     maxSize,
    }
}

func (p *Pool) Get() (*Connection, error) {
    select {
    case conn := <-p.connections:
        return conn, nil
    default:
        return p.create()
    }
}

func (p *Pool) create() (*Connection, error) {
    p.mu.Lock()
    defer p.mu.Unlock()
    
    if p.created >= p.maxSize {
        // Wait for available connection
        conn := <-p.connections
        return conn, nil
    }
    
    p.created++
    return &Connection{ID: p.created}, nil
}

func (p *Pool) Put(conn *Connection) error {
    if conn == nil {
        return errors.New("nil connection")
    }
    
    select {
    case p.connections <- conn:
        return nil
    default:
        return errors.New("pool full")
    }
}
```

---

## 📋 Race Condition Checklist

### Junior ✅
- [ ] Understand what race condition is
- [ ] Use `go run -race` to detect races
- [ ] Basic mutex usage
- [ ] Always use `defer unlock`

### Mid ✅
- [ ] Use `sync/atomic` for counters
- [ ] Use `sync.Map` for concurrent maps
- [ ] Understand RWMutex vs Mutex
- [ ] Run race detector in CI/CD

### Senior ✅
- [ ] Design to avoid shared state
- [ ] Channel-based concurrency patterns
- [ ] `sync.Once` for lazy init
- [ ] CAS (Compare-and-Swap) operations

### Expert ✅
- [ ] Lock-free data structures
- [ ] Memory ordering understanding
- [ ] Performance profiling of locks
- [ ] Designing concurrent APIs
