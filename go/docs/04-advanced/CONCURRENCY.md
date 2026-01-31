# ⚡ CONCURRENCY - Goroutines & Channels (Junior → Senior)

Dokumentasi lengkap tentang concurrency di Go - fitur paling powerful dari Go.

---

## 🎯 Mengapa Concurrency Penting?

```
Concurrency = Melakukan banyak hal sekaligus

Go dirancang untuk concurrency dari awal:
- Goroutines: Lightweight threads
- Channels: Komunikasi antar goroutines
- Simple syntax: Tidak perlu lock manual

Concurrency ≠ Parallelism
- Concurrency: Dealing with many things at once (design)
- Parallelism: Doing many things at once (execution)
```

---

## 1️⃣ JUNIOR LEVEL - Goroutines

### Basic Goroutine

```go
package main

import (
    "fmt"
    "time"
)

func sayHello(name string) {
    for i := 0; i < 3; i++ {
        fmt.Println("Hello", name)
        time.Sleep(100 * time.Millisecond)
    }
}

func main() {
    // Regular function call (blocking)
    sayHello("World")
    
    // Goroutine (non-blocking)
    go sayHello("Go")
    go sayHello("Concurrency")
    
    // Main harus menunggu, kalau tidak program langsung selesai
    time.Sleep(500 * time.Millisecond)
    
    fmt.Println("Main done")
}

// Output (bisa berbeda urutan):
// Hello World
// Hello World
// Hello World
// Hello Go
// Hello Concurrency
// Hello Go
// Hello Concurrency
// Hello Go
// Hello Concurrency
// Main done
```

### Anonymous Goroutine

```go
package main

import (
    "fmt"
    "time"
)

func main() {
    // Anonymous function as goroutine
    go func() {
        fmt.Println("Hello from anonymous goroutine")
    }()
    
    // With parameter
    message := "Hello Go"
    go func(msg string) {
        fmt.Println(msg)
    }(message) // Pass value to avoid closure issues
    
    time.Sleep(100 * time.Millisecond)
}
```

### Common Mistake: Loop Variable

```go
package main

import (
    "fmt"
    "time"
)

func main() {
    // WRONG: All goroutines might print the same value
    for i := 0; i < 5; i++ {
        go func() {
            fmt.Println(i) // Closure captures variable, not value
        }()
    }
    
    time.Sleep(100 * time.Millisecond)
    // Output might be: 5 5 5 5 5
    
    fmt.Println("---")
    
    // CORRECT: Pass value as parameter
    for i := 0; i < 5; i++ {
        go func(n int) {
            fmt.Println(n)
        }(i) // Pass i as argument
    }
    
    time.Sleep(100 * time.Millisecond)
    // Output: 0 1 2 3 4 (order may vary)
}
```

---

## 2️⃣ MID LEVEL - Channels

### Channel Basics

```go
package main

import "fmt"

func main() {
    // Create channel
    ch := make(chan string)
    
    // Send to channel (in goroutine)
    go func() {
        ch <- "Hello from channel"
    }()
    
    // Receive from channel (blocking)
    message := <-ch
    fmt.Println(message) // Hello from channel
}
```

### Buffered vs Unbuffered Channels

```go
package main

import "fmt"

func main() {
    // Unbuffered channel (synchronous)
    // Send blocks until someone receives
    unbuffered := make(chan int)
    
    go func() {
        unbuffered <- 1 // Blocks until received
        fmt.Println("Sent to unbuffered")
    }()
    
    fmt.Println("Received:", <-unbuffered)
    
    // Buffered channel (asynchronous up to buffer size)
    buffered := make(chan int, 3) // Buffer size 3
    
    // Can send without blocking (up to buffer size)
    buffered <- 1
    buffered <- 2
    buffered <- 3
    // buffered <- 4 // Would block (buffer full)
    
    fmt.Println("Buffered:", <-buffered, <-buffered, <-buffered)
}
```

### Channel Direction

```go
package main

import "fmt"

// Send-only channel
func producer(ch chan<- int) {
    for i := 0; i < 5; i++ {
        ch <- i
    }
    close(ch) // Important: close when done
}

// Receive-only channel
func consumer(ch <-chan int) {
    for num := range ch { // Loop until channel closed
        fmt.Println("Received:", num)
    }
}

func main() {
    ch := make(chan int)
    
    go producer(ch)
    consumer(ch)
}
```

### Range over Channel

```go
package main

import "fmt"

func main() {
    ch := make(chan int, 5)
    
    // Send values
    go func() {
        for i := 1; i <= 5; i++ {
            ch <- i
        }
        close(ch) // MUST close for range to work
    }()
    
    // Receive with range
    for num := range ch {
        fmt.Println(num)
    }
    // 1 2 3 4 5
}
```

---

## 3️⃣ MID LEVEL - Select Statement

### Basic Select

```go
package main

import (
    "fmt"
    "time"
)

func main() {
    ch1 := make(chan string)
    ch2 := make(chan string)
    
    go func() {
        time.Sleep(100 * time.Millisecond)
        ch1 <- "from ch1"
    }()
    
    go func() {
        time.Sleep(200 * time.Millisecond)
        ch2 <- "from ch2"
    }()
    
    // Select waits on multiple channels
    for i := 0; i < 2; i++ {
        select {
        case msg1 := <-ch1:
            fmt.Println("Received", msg1)
        case msg2 := <-ch2:
            fmt.Println("Received", msg2)
        }
    }
}
```

### Select with Timeout

```go
package main

import (
    "fmt"
    "time"
)

func main() {
    ch := make(chan string)
    
    go func() {
        time.Sleep(2 * time.Second)
        ch <- "result"
    }()
    
    select {
    case res := <-ch:
        fmt.Println("Received:", res)
    case <-time.After(1 * time.Second):
        fmt.Println("Timeout!")
    }
}
```

### Select with Default (Non-blocking)

```go
package main

import "fmt"

func main() {
    ch := make(chan int, 1)
    
    // Non-blocking send
    select {
    case ch <- 1:
        fmt.Println("Sent!")
    default:
        fmt.Println("Channel full, skipped")
    }
    
    // Non-blocking receive
    select {
    case val := <-ch:
        fmt.Println("Received:", val)
    default:
        fmt.Println("Nothing to receive")
    }
}
```

---

## 4️⃣ MID-SENIOR LEVEL - sync Package

### WaitGroup

```go
package main

import (
    "fmt"
    "sync"
    "time"
)

func worker(id int, wg *sync.WaitGroup) {
    defer wg.Done() // Decrement counter when done
    
    fmt.Printf("Worker %d starting\n", id)
    time.Sleep(time.Second)
    fmt.Printf("Worker %d done\n", id)
}

func main() {
    var wg sync.WaitGroup
    
    for i := 1; i <= 5; i++ {
        wg.Add(1) // Increment counter
        go worker(i, &wg)
    }
    
    wg.Wait() // Wait for all workers
    fmt.Println("All workers completed")
}
```

### Mutex (Mutual Exclusion)

```go
package main

import (
    "fmt"
    "sync"
)

type SafeCounter struct {
    mu    sync.Mutex
    count int
}

func (c *SafeCounter) Increment() {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.count++
}

func (c *SafeCounter) Value() int {
    c.mu.Lock()
    defer c.mu.Unlock()
    return c.count
}

func main() {
    counter := &SafeCounter{}
    var wg sync.WaitGroup
    
    // 1000 goroutines incrementing
    for i := 0; i < 1000; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            counter.Increment()
        }()
    }
    
    wg.Wait()
    fmt.Println("Count:", counter.Value()) // Always 1000
}
```

### RWMutex (Read/Write Lock)

```go
package main

import (
    "fmt"
    "sync"
    "time"
)

type Cache struct {
    mu    sync.RWMutex
    items map[string]string
}

func NewCache() *Cache {
    return &Cache{
        items: make(map[string]string),
    }
}

func (c *Cache) Get(key string) (string, bool) {
    c.mu.RLock() // Multiple readers allowed
    defer c.mu.RUnlock()
    
    val, ok := c.items[key]
    return val, ok
}

func (c *Cache) Set(key, value string) {
    c.mu.Lock() // Exclusive access
    defer c.mu.Unlock()
    
    c.items[key] = value
}

func main() {
    cache := NewCache()
    var wg sync.WaitGroup
    
    // Writers
    for i := 0; i < 10; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()
            cache.Set(fmt.Sprintf("key%d", id), fmt.Sprintf("value%d", id))
        }(i)
    }
    
    // Readers
    for i := 0; i < 100; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()
            cache.Get(fmt.Sprintf("key%d", id%10))
        }(i)
    }
    
    wg.Wait()
    fmt.Println("Done!")
}
```

### Once (Run Once)

```go
package main

import (
    "fmt"
    "sync"
)

var once sync.Once

func initialize() {
    fmt.Println("Initializing... (should only print once)")
}

func main() {
    var wg sync.WaitGroup
    
    for i := 0; i < 10; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            once.Do(initialize) // Only runs once
        }()
    }
    
    wg.Wait()
    // Output: Initializing... (should only print once)
    // (prints only ONCE despite 10 goroutines)
}
```

---

## 5️⃣ SENIOR LEVEL - Common Patterns

### Worker Pool

```go
package main

import (
    "fmt"
    "sync"
    "time"
)

type Job struct {
    ID   int
    Data string
}

type Result struct {
    JobID  int
    Output string
}

func worker(id int, jobs <-chan Job, results chan<- Result, wg *sync.WaitGroup) {
    defer wg.Done()
    
    for job := range jobs {
        fmt.Printf("Worker %d processing job %d\n", id, job.ID)
        
        // Simulate work
        time.Sleep(100 * time.Millisecond)
        
        results <- Result{
            JobID:  job.ID,
            Output: fmt.Sprintf("Processed: %s", job.Data),
        }
    }
}

func main() {
    numWorkers := 3
    numJobs := 10
    
    jobs := make(chan Job, numJobs)
    results := make(chan Result, numJobs)
    
    // Start workers
    var wg sync.WaitGroup
    for i := 1; i <= numWorkers; i++ {
        wg.Add(1)
        go worker(i, jobs, results, &wg)
    }
    
    // Send jobs
    for i := 1; i <= numJobs; i++ {
        jobs <- Job{ID: i, Data: fmt.Sprintf("Data-%d", i)}
    }
    close(jobs) // Signal no more jobs
    
    // Wait for workers in separate goroutine
    go func() {
        wg.Wait()
        close(results)
    }()
    
    // Collect results
    for result := range results {
        fmt.Printf("Result: Job %d -> %s\n", result.JobID, result.Output)
    }
}
```

### Fan-Out, Fan-In

```go
package main

import (
    "fmt"
    "sync"
)

// Fan-out: One channel to multiple goroutines
// Fan-in: Multiple channels to one channel

func generator(nums ...int) <-chan int {
    out := make(chan int)
    go func() {
        for _, n := range nums {
            out <- n
        }
        close(out)
    }()
    return out
}

func square(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        for n := range in {
            out <- n * n
        }
        close(out)
    }()
    return out
}

// Fan-in: merge multiple channels
func merge(channels ...<-chan int) <-chan int {
    var wg sync.WaitGroup
    out := make(chan int)
    
    output := func(c <-chan int) {
        defer wg.Done()
        for n := range c {
            out <- n
        }
    }
    
    wg.Add(len(channels))
    for _, c := range channels {
        go output(c)
    }
    
    go func() {
        wg.Wait()
        close(out)
    }()
    
    return out
}

func main() {
    // Generate numbers
    nums := generator(1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
    
    // Fan-out: Distribute to multiple workers
    sq1 := square(nums) // Worker 1
    sq2 := square(nums) // Worker 2
    
    // Oops! This doesn't work because nums is consumed by sq1
    // Each number goes to EITHER sq1 OR sq2, not both
    
    // Better approach: Create separate generators
    in := generator(1, 2, 3, 4, 5)
    
    // Fan-out
    c1 := square(in)
    // c2 := square(in) // Same issue
    
    // Fan-in
    for n := range c1 {
        fmt.Println(n)
    }
}
```

### Pipeline Pattern

```go
package main

import "fmt"

// Stage 1: Generate numbers
func generate(nums ...int) <-chan int {
    out := make(chan int)
    go func() {
        for _, n := range nums {
            out <- n
        }
        close(out)
    }()
    return out
}

// Stage 2: Square numbers
func square(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        for n := range in {
            out <- n * n
        }
        close(out)
    }()
    return out
}

// Stage 3: Add 10
func addTen(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        for n := range in {
            out <- n + 10
        }
        close(out)
    }()
    return out
}

// Stage 4: Print
func print(in <-chan int) {
    for n := range in {
        fmt.Println(n)
    }
}

func main() {
    // Pipeline: generate -> square -> addTen -> print
    nums := generate(1, 2, 3, 4, 5)
    squared := square(nums)
    added := addTen(squared)
    print(added)
    
    // Output: 11, 14, 19, 26, 35
    // (1² + 10 = 11, 2² + 10 = 14, ...)
}
```

### Context for Cancellation

```go
package main

import (
    "context"
    "fmt"
    "time"
)

func worker(ctx context.Context, id int) {
    for {
        select {
        case <-ctx.Done():
            fmt.Printf("Worker %d cancelled\n", id)
            return
        default:
            fmt.Printf("Worker %d working...\n", id)
            time.Sleep(500 * time.Millisecond)
        }
    }
}

func main() {
    // Create context with cancel
    ctx, cancel := context.WithCancel(context.Background())
    
    // Start workers
    for i := 1; i <= 3; i++ {
        go worker(ctx, i)
    }
    
    // Let them work for 2 seconds
    time.Sleep(2 * time.Second)
    
    // Cancel all workers
    cancel()
    
    // Give workers time to finish
    time.Sleep(100 * time.Millisecond)
    fmt.Println("All workers stopped")
}
```

### Context with Timeout

```go
package main

import (
    "context"
    "fmt"
    "time"
)

func slowOperation(ctx context.Context) error {
    select {
    case <-time.After(5 * time.Second):
        return nil // Operation completed
    case <-ctx.Done():
        return ctx.Err() // Context cancelled/timeout
    }
}

func main() {
    // Context with 2 second timeout
    ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
    defer cancel() // Always call cancel to release resources
    
    fmt.Println("Starting slow operation...")
    
    if err := slowOperation(ctx); err != nil {
        fmt.Println("Error:", err) // context deadline exceeded
    } else {
        fmt.Println("Operation completed")
    }
}
```

---

## 6️⃣ SENIOR LEVEL - Semaphore Pattern

### Limit Concurrent Operations

```go
package main

import (
    "fmt"
    "sync"
    "time"
)

// Semaphore using buffered channel
type Semaphore struct {
    sem chan struct{}
}

func NewSemaphore(max int) *Semaphore {
    return &Semaphore{
        sem: make(chan struct{}, max),
    }
}

func (s *Semaphore) Acquire() {
    s.sem <- struct{}{}
}

func (s *Semaphore) Release() {
    <-s.sem
}

func main() {
    // Allow max 3 concurrent operations
    sem := NewSemaphore(3)
    var wg sync.WaitGroup
    
    for i := 1; i <= 10; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()
            
            sem.Acquire()
            defer sem.Release()
            
            fmt.Printf("Worker %d started\n", id)
            time.Sleep(time.Second)
            fmt.Printf("Worker %d finished\n", id)
        }(i)
    }
    
    wg.Wait()
    fmt.Println("All done!")
}
```

### Rate Limiter

```go
package main

import (
    "fmt"
    "sync"
    "time"
)

type RateLimiter struct {
    ticker *time.Ticker
}

func NewRateLimiter(ratePerSecond int) *RateLimiter {
    return &RateLimiter{
        ticker: time.NewTicker(time.Second / time.Duration(ratePerSecond)),
    }
}

func (r *RateLimiter) Wait() {
    <-r.ticker.C
}

func (r *RateLimiter) Stop() {
    r.ticker.Stop()
}

func main() {
    // 5 requests per second
    limiter := NewRateLimiter(5)
    defer limiter.Stop()
    
    var wg sync.WaitGroup
    
    for i := 1; i <= 10; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()
            
            limiter.Wait()
            fmt.Printf("Request %d at %s\n", id, time.Now().Format("15:04:05.000"))
        }(i)
    }
    
    wg.Wait()
}
```

---

## 7️⃣ EXPERT LEVEL - Error Handling in Goroutines

### errgroup Pattern

```go
package main

import (
    "context"
    "errors"
    "fmt"
    
    "golang.org/x/sync/errgroup"
)

func fetchUser(ctx context.Context, id int) error {
    if id == 2 {
        return errors.New("user 2 not found")
    }
    fmt.Printf("Fetched user %d\n", id)
    return nil
}

func main() {
    g, ctx := errgroup.WithContext(context.Background())
    
    for i := 1; i <= 5; i++ {
        id := i // Capture loop variable
        g.Go(func() error {
            return fetchUser(ctx, id)
        })
    }
    
    // Wait for all and get first error
    if err := g.Wait(); err != nil {
        fmt.Println("Error:", err)
    } else {
        fmt.Println("All done!")
    }
}
```

### Panic Recovery in Goroutines

```go
package main

import (
    "fmt"
    "sync"
)

func safeGo(fn func()) {
    go func() {
        defer func() {
            if r := recover(); r != nil {
                fmt.Printf("Recovered from panic: %v\n", r)
            }
        }()
        fn()
    }()
}

func main() {
    var wg sync.WaitGroup
    
    wg.Add(1)
    safeGo(func() {
        defer wg.Done()
        panic("something went wrong!")
    })
    
    wg.Wait()
    fmt.Println("Main continues...")
}
```

---

## 📊 Concurrency Cheat Sheet

### Channel Operations

| Operation | Syntax | Blocks When |
|-----------|--------|-------------|
| Send | `ch <- v` | Buffer full (unbuffered: no receiver) |
| Receive | `v := <-ch` | Buffer empty |
| Close | `close(ch)` | Never |
| Range | `for v := range ch` | Until channel closed |

### sync Package

| Type | Use Case |
|------|----------|
| `sync.WaitGroup` | Wait for goroutines to finish |
| `sync.Mutex` | Exclusive access to resource |
| `sync.RWMutex` | Multiple readers, one writer |
| `sync.Once` | Run something only once |
| `sync.Pool` | Object pooling |
| `sync.Map` | Concurrent-safe map |

### Patterns

| Pattern | Description |
|---------|-------------|
| Worker Pool | Fixed number of workers processing jobs |
| Pipeline | Chain of processing stages |
| Fan-Out | One to many distribution |
| Fan-In | Many to one aggregation |
| Semaphore | Limit concurrent operations |
| Rate Limiter | Control operation rate |

---

## 💡 Summary

| Level | Focus |
|-------|-------|
| **Junior** | Goroutines, basic channels |
| **Mid** | Buffered channels, select, range |
| **Mid-Senior** | WaitGroup, Mutex, Once |
| **Senior** | Worker pool, pipeline, context |
| **Expert** | errgroup, semaphore, rate limiting |

**Best Practices:**
- ✅ Always close channels when done sending
- ✅ Use WaitGroup to wait for goroutines
- ✅ Use context for cancellation
- ✅ Protect shared state with mutex
- ✅ Prefer channels over shared memory
- ❌ Don't pass loop variables directly to goroutines
- ❌ Don't forget to handle panics in goroutines
- ❌ Don't create too many goroutines (use worker pool)
