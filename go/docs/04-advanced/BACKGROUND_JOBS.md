# ⚙️ Background Jobs & Async Processing di Go

## Kenapa Penting?

Background jobs untuk:
- ✅ Offload heavy processing
- ✅ Asynchronous task execution
- ✅ Retry failed tasks
- ✅ Scheduled jobs

---

## 📚 Daftar Isi

1. [Worker Pool Pattern](#1️⃣-worker-pool-pattern)
2. [Asynq (Redis-backed)](#2️⃣-asynq-redis-backed)
3. [Goroutine Job Queue](#3️⃣-goroutine-job-queue)
4. [Scheduled Jobs](#4️⃣-scheduled-jobs)
5. [Distributed Jobs](#5️⃣-distributed-jobs)
6. [Monitoring & Retry](#6️⃣-monitoring--retry)

---

## 1️⃣ Worker Pool Pattern

### Simple Worker Pool

```go
// internal/worker/pool.go
package worker

import (
    "context"
    "fmt"
    "sync"
)

type Job func(context.Context) error

type WorkerPool struct {
    numWorkers int
    jobs       chan Job
    results    chan error
    wg         sync.WaitGroup
}

func NewWorkerPool(numWorkers int) *WorkerPool {
    return &WorkerPool{
        numWorkers: numWorkers,
        jobs:       make(chan Job, 100),
        results:    make(chan error, 100),
    }
}

func (p *WorkerPool) Start(ctx context.Context) {
    for i := 0; i < p.numWorkers; i++ {
        p.wg.Add(1)
        go p.worker(ctx, i)
    }
}

func (p *WorkerPool) worker(ctx context.Context, id int) {
    defer p.wg.Done()
    
    for {
        select {
        case <-ctx.Done():
            fmt.Printf("Worker %d stopped\n", id)
            return
        case job, ok := <-p.jobs:
            if !ok {
                return
            }
            
            fmt.Printf("Worker %d processing job\n", id)
            err := job(ctx)
            p.results <- err
        }
    }
}

func (p *WorkerPool) Submit(job Job) {
    p.jobs <- job
}

func (p *WorkerPool) Stop() {
    close(p.jobs)
    p.wg.Wait()
    close(p.results)
}

func (p *WorkerPool) Results() <-chan error {
    return p.results
}
```

### Usage Example

```go
// cmd/worker/main.go
package main

import (
    "context"
    "fmt"
    "time"
    
    "myapp/internal/worker"
)

func main() {
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()
    
    pool := worker.NewWorkerPool(5)
    pool.Start(ctx)
    
    // Submit jobs
    for i := 0; i < 20; i++ {
        jobID := i
        pool.Submit(func(ctx context.Context) error {
            fmt.Printf("Processing job %d\n", jobID)
            time.Sleep(time.Second)
            return nil
        })
    }
    
    // Collect results
    go func() {
        for err := range pool.Results() {
            if err != nil {
                fmt.Printf("Job failed: %v\n", err)
            }
        }
    }()
    
    // Wait and shutdown
    time.Sleep(30 * time.Second)
    pool.Stop()
}
```

### Worker with Context & Timeout

```go
// internal/worker/timeout_worker.go
package worker

import (
    "context"
    "time"
)

func ProcessJobWithTimeout(job Job, timeout time.Duration) error {
    ctx, cancel := context.WithTimeout(context.Background(), timeout)
    defer cancel()
    
    errChan := make(chan error, 1)
    
    go func() {
        errChan <- job(ctx)
    }()
    
    select {
    case err := <-errChan:
        return err
    case <-ctx.Done():
        return ctx.Err()
    }
}
```

---

## 2️⃣ Asynq (Redis-backed)

### Installation

```bash
go get github.com/hibiken/asynq
```

### Task Definition

```go
// internal/tasks/tasks.go
package tasks

import (
    "context"
    "encoding/json"
    "fmt"
    "time"
    
    "github.com/hibiken/asynq"
)

// Task types
const (
    TypeSendEmail    = "email:send"
    TypeProcessImage = "image:process"
    TypeGenerateReport = "report:generate"
)

// Email task payload
type EmailPayload struct {
    To      string
    Subject string
    Body    string
}

func NewSendEmailTask(to, subject, body string) (*asynq.Task, error) {
    payload, err := json.Marshal(EmailPayload{
        To:      to,
        Subject: subject,
        Body:    body,
    })
    if err != nil {
        return nil, err
    }
    return asynq.NewTask(TypeSendEmail, payload), nil
}

// Image processing task
type ImagePayload struct {
    ImageURL string
    Filters  []string
}

func NewProcessImageTask(imageURL string, filters []string) (*asynq.Task, error) {
    payload, err := json.Marshal(ImagePayload{
        ImageURL: imageURL,
        Filters:  filters,
    })
    if err != nil {
        return nil, err
    }
    return asynq.NewTask(TypeProcessImage, payload), nil
}
```

### Task Handlers

```go
// internal/tasks/handlers.go
package tasks

import (
    "context"
    "encoding/json"
    "fmt"
    "time"
    
    "github.com/hibiken/asynq"
)

type EmailService interface {
    Send(ctx context.Context, to, subject, body string) error
}

type ImageService interface {
    Process(ctx context.Context, url string, filters []string) error
}

type TaskHandlers struct {
    emailSvc EmailService
    imageSvc ImageService
}

func NewTaskHandlers(emailSvc EmailService, imageSvc ImageService) *TaskHandlers {
    return &TaskHandlers{
        emailSvc: emailSvc,
        imageSvc: imageSvc,
    }
}

func (h *TaskHandlers) HandleSendEmail(ctx context.Context, t *asynq.Task) error {
    var payload EmailPayload
    if err := json.Unmarshal(t.Payload(), &payload); err != nil {
        return fmt.Errorf("json.Unmarshal failed: %w", err)
    }
    
    fmt.Printf("Sending email to %s\n", payload.To)
    
    if err := h.emailSvc.Send(ctx, payload.To, payload.Subject, payload.Body); err != nil {
        return fmt.Errorf("failed to send email: %w", err)
    }
    
    fmt.Printf("Email sent successfully to %s\n", payload.To)
    return nil
}

func (h *TaskHandlers) HandleProcessImage(ctx context.Context, t *asynq.Task) error {
    var payload ImagePayload
    if err := json.Unmarshal(t.Payload(), &payload); err != nil {
        return fmt.Errorf("json.Unmarshal failed: %w", err)
    }
    
    fmt.Printf("Processing image: %s with filters: %v\n", payload.ImageURL, payload.Filters)
    
    if err := h.imageSvc.Process(ctx, payload.ImageURL, payload.Filters); err != nil {
        return fmt.Errorf("failed to process image: %w", err)
    }
    
    fmt.Printf("Image processed successfully: %s\n", payload.ImageURL)
    return nil
}
```

### Server Setup

```go
// cmd/worker/main.go
package main

import (
    "log"
    
    "github.com/hibiken/asynq"
    "myapp/internal/tasks"
)

func main() {
    redisOpt := asynq.RedisClientOpt{
        Addr: "localhost:6379",
    }
    
    server := asynq.NewServer(
        redisOpt,
        asynq.Config{
            Concurrency: 10,
            Queues: map[string]int{
                "critical": 6,  // 60% of workers
                "default":  3,  // 30% of workers
                "low":      1,  // 10% of workers
            },
            RetryDelayFunc: func(n int, err error, task *asynq.Task) time.Duration {
                // Exponential backoff
                return time.Duration(n) * time.Minute
            },
            Logger: log.Default(),
        },
    )
    
    // Initialize handlers
    handlers := tasks.NewTaskHandlers(emailService, imageService)
    
    // Register handlers
    mux := asynq.NewServeMux()
    mux.HandleFunc(tasks.TypeSendEmail, handlers.HandleSendEmail)
    mux.HandleFunc(tasks.TypeProcessImage, handlers.HandleProcessImage)
    
    if err := server.Run(mux); err != nil {
        log.Fatalf("could not run server: %v", err)
    }
}
```

### Client - Enqueue Tasks

```go
// internal/service/task_service.go
package service

import (
    "fmt"
    "time"
    
    "github.com/hibiken/asynq"
    "myapp/internal/tasks"
)

type TaskService struct {
    client *asynq.Client
}

func NewTaskService(redisAddr string) *TaskService {
    client := asynq.NewClient(asynq.RedisClientOpt{
        Addr: redisAddr,
    })
    return &TaskService{client: client}
}

// Enqueue task immediately
func (s *TaskService) SendEmail(to, subject, body string) error {
    task, err := tasks.NewSendEmailTask(to, subject, body)
    if err != nil {
        return err
    }
    
    info, err := s.client.Enqueue(task)
    if err != nil {
        return err
    }
    
    fmt.Printf("Enqueued task: id=%s queue=%s\n", info.ID, info.Queue)
    return nil
}

// Schedule task for later
func (s *TaskService) SendEmailAt(to, subject, body string, processAt time.Time) error {
    task, err := tasks.NewSendEmailTask(to, subject, body)
    if err != nil {
        return err
    }
    
    info, err := s.client.Enqueue(task, asynq.ProcessAt(processAt))
    if err != nil {
        return err
    }
    
    fmt.Printf("Scheduled task: id=%s at=%v\n", info.ID, processAt)
    return nil
}

// Enqueue with options
func (s *TaskService) ProcessImage(imageURL string, filters []string) error {
    task, err := tasks.NewProcessImageTask(imageURL, filters)
    if err != nil {
        return err
    }
    
    info, err := s.client.Enqueue(
        task,
        asynq.Queue("critical"),            // High priority queue
        asynq.MaxRetry(5),                  // Retry up to 5 times
        asynq.Timeout(10*time.Minute),      // Timeout after 10 minutes
        asynq.Deadline(time.Now().Add(1*time.Hour)), // Must complete in 1 hour
    )
    if err != nil {
        return err
    }
    
    fmt.Printf("Enqueued image processing: id=%s\n", info.ID)
    return nil
}

func (s *TaskService) Close() error {
    return s.client.Close()
}
```

---

## 3️⃣ Goroutine Job Queue

### Custom Job Queue

```go
// internal/queue/queue.go
package queue

import (
    "context"
    "sync"
    "time"
)

type Job struct {
    ID        string
    Payload   interface{}
    CreatedAt time.Time
    Retries   int
    MaxRetries int
}

type Handler func(context.Context, *Job) error

type Queue struct {
    jobs    chan *Job
    workers int
    handler Handler
    wg      sync.WaitGroup
    mu      sync.RWMutex
    running bool
}

func NewQueue(workers int, handler Handler) *Queue {
    return &Queue{
        jobs:    make(chan *Job, 1000),
        workers: workers,
        handler: handler,
    }
}

func (q *Queue) Start(ctx context.Context) {
    q.mu.Lock()
    if q.running {
        q.mu.Unlock()
        return
    }
    q.running = true
    q.mu.Unlock()
    
    for i := 0; i < q.workers; i++ {
        q.wg.Add(1)
        go q.worker(ctx)
    }
}

func (q *Queue) worker(ctx context.Context) {
    defer q.wg.Done()
    
    for {
        select {
        case <-ctx.Done():
            return
        case job, ok := <-q.jobs:
            if !ok {
                return
            }
            
            if err := q.handler(ctx, job); err != nil {
                // Retry logic
                if job.Retries < job.MaxRetries {
                    job.Retries++
                    time.Sleep(time.Second * time.Duration(job.Retries))
                    q.Enqueue(job)
                }
            }
        }
    }
}

func (q *Queue) Enqueue(job *Job) error {
    q.mu.RLock()
    defer q.mu.RUnlock()
    
    if !q.running {
        return fmt.Errorf("queue is not running")
    }
    
    select {
    case q.jobs <- job:
        return nil
    default:
        return fmt.Errorf("queue is full")
    }
}

func (q *Queue) Stop() {
    q.mu.Lock()
    if !q.running {
        q.mu.Unlock()
        return
    }
    q.running = false
    q.mu.Unlock()
    
    close(q.jobs)
    q.wg.Wait()
}
```

### Usage

```go
// cmd/api/main.go
package main

import (
    "context"
    "fmt"
    
    "myapp/internal/queue"
)

func main() {
    ctx := context.Background()
    
    // Create queue with handler
    q := queue.NewQueue(5, func(ctx context.Context, job *queue.Job) error {
        fmt.Printf("Processing job: %s\n", job.ID)
        
        // Type assertion for payload
        if data, ok := job.Payload.(map[string]interface{}); ok {
            fmt.Printf("Data: %v\n", data)
        }
        
        return nil
    })
    
    q.Start(ctx)
    defer q.Stop()
    
    // Enqueue jobs
    for i := 0; i < 10; i++ {
        job := &queue.Job{
            ID:         fmt.Sprintf("job-%d", i),
            Payload:    map[string]interface{}{"index": i},
            MaxRetries: 3,
        }
        q.Enqueue(job)
    }
}
```

---

## 4️⃣ Scheduled Jobs

### Cron-like Scheduler

```bash
go get github.com/robfig/cron/v3
```

```go
// internal/scheduler/scheduler.go
package scheduler

import (
    "context"
    "fmt"
    "log"
    
    "github.com/robfig/cron/v3"
)

type Scheduler struct {
    cron *cron.Cron
}

func NewScheduler() *Scheduler {
    return &Scheduler{
        cron: cron.New(cron.WithSeconds()),
    }
}

func (s *Scheduler) AddJob(spec string, cmd func()) error {
    _, err := s.cron.AddFunc(spec, cmd)
    return err
}

func (s *Scheduler) Start() {
    s.cron.Start()
}

func (s *Scheduler) Stop() {
    s.cron.Stop()
}
```

### Scheduled Tasks

```go
// cmd/scheduler/main.go
package main

import (
    "fmt"
    "time"
    
    "myapp/internal/scheduler"
    "myapp/internal/service"
)

func main() {
    sched := scheduler.NewScheduler()
    
    // Every day at midnight
    sched.AddJob("0 0 0 * * *", func() {
        fmt.Println("Running daily cleanup...")
        service.CleanupOldData()
    })
    
    // Every hour
    sched.AddJob("0 0 * * * *", func() {
        fmt.Println("Generating hourly report...")
        service.GenerateReport()
    })
    
    // Every 5 minutes
    sched.AddJob("0 */5 * * * *", func() {
        fmt.Println("Checking system health...")
        service.HealthCheck()
    })
    
    // Every Monday at 9 AM
    sched.AddJob("0 0 9 * * MON", func() {
        fmt.Println("Sending weekly summary...")
        service.SendWeeklySummary()
    })
    
    sched.Start()
    defer sched.Stop()
    
    // Keep running
    select {}
}
```

### Ticker-based Scheduler

```go
// internal/scheduler/ticker.go
package scheduler

import (
    "context"
    "time"
)

type TickerJob struct {
    interval time.Duration
    job      func(context.Context)
}

func RunPeriodic(ctx context.Context, interval time.Duration, job func(context.Context)) {
    ticker := time.NewTicker(interval)
    defer ticker.Stop()
    
    // Run immediately
    job(ctx)
    
    for {
        select {
        case <-ctx.Done():
            return
        case <-ticker.C:
            job(ctx)
        }
    }
}

// Usage
func main() {
    ctx := context.Background()
    
    go RunPeriodic(ctx, 5*time.Minute, func(ctx context.Context) {
        fmt.Println("Periodic task executed")
    })
}
```

---

## 5️⃣ Distributed Jobs

### Redis-based Distributed Lock

```go
// internal/lock/redis_lock.go
package lock

import (
    "context"
    "time"
    
    "github.com/go-redis/redis/v8"
)

type RedisLock struct {
    client *redis.Client
}

func NewRedisLock(client *redis.Client) *RedisLock {
    return &RedisLock{client: client}
}

func (l *RedisLock) Acquire(ctx context.Context, key string, ttl time.Duration) (bool, error) {
    return l.client.SetNX(ctx, key, "locked", ttl).Result()
}

func (l *RedisLock) Release(ctx context.Context, key string) error {
    return l.client.Del(ctx, key).Err()
}

// Run job with distributed lock
func (l *RedisLock) RunWithLock(ctx context.Context, lockKey string, ttl time.Duration, job func() error) error {
    acquired, err := l.Acquire(ctx, lockKey, ttl)
    if err != nil {
        return err
    }
    
    if !acquired {
        return fmt.Errorf("could not acquire lock")
    }
    
    defer l.Release(ctx, lockKey)
    
    return job()
}
```

### Usage

```go
// Ensure only one instance processes the job
func ProcessReportJob(ctx context.Context, lock *lock.RedisLock) error {
    return lock.RunWithLock(ctx, "job:report:generate", 10*time.Minute, func() error {
        fmt.Println("Generating report...")
        // Heavy processing
        return generateReport()
    })
}
```

---

## 6️⃣ Monitoring & Retry

### Job Status Tracking

```go
// internal/jobs/status.go
package jobs

import (
    "context"
    "time"
)

type JobStatus string

const (
    StatusPending   JobStatus = "pending"
    StatusRunning   JobStatus = "running"
    StatusCompleted JobStatus = "completed"
    StatusFailed    JobStatus = "failed"
)

type JobRecord struct {
    ID          string
    Type        string
    Status      JobStatus
    Payload     string
    Result      string
    Error       string
    Retries     int
    MaxRetries  int
    CreatedAt   time.Time
    UpdatedAt   time.Time
    CompletedAt *time.Time
}

type JobRepository interface {
    Create(ctx context.Context, job *JobRecord) error
    Update(ctx context.Context, job *JobRecord) error
    GetByID(ctx context.Context, id string) (*JobRecord, error)
    GetPending(ctx context.Context, limit int) ([]*JobRecord, error)
}
```

### Retry with Exponential Backoff

```go
// internal/jobs/retry.go
package jobs

import (
    "context"
    "fmt"
    "time"
)

func RetryWithBackoff(ctx context.Context, maxRetries int, job func() error) error {
    var err error
    
    for attempt := 0; attempt < maxRetries; attempt++ {
        if attempt > 0 {
            // Exponential backoff: 1s, 2s, 4s, 8s, ...
            backoff := time.Duration(1<<uint(attempt-1)) * time.Second
            
            select {
            case <-ctx.Done():
                return ctx.Err()
            case <-time.After(backoff):
            }
        }
        
        err = job()
        if err == nil {
            return nil
        }
        
        fmt.Printf("Attempt %d failed: %v\n", attempt+1, err)
    }
    
    return fmt.Errorf("max retries exceeded: %w", err)
}
```

### Monitoring Dashboard Data

```go
// internal/jobs/metrics.go
package jobs

import (
    "context"
    "time"
)

type JobMetrics struct {
    TotalJobs      int
    PendingJobs    int
    RunningJobs    int
    CompletedJobs  int
    FailedJobs     int
    AvgDuration    time.Duration
}

func (r *jobRepository) GetMetrics(ctx context.Context, since time.Time) (*JobMetrics, error) {
    query := `
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
            COUNT(CASE WHEN status = 'running' THEN 1 END) as running,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
            COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
            AVG(EXTRACT(EPOCH FROM (completed_at - created_at))) as avg_duration
        FROM jobs
        WHERE created_at >= $1
    `
    
    var metrics JobMetrics
    err := r.db.QueryRowContext(ctx, query, since).Scan(
        &metrics.TotalJobs,
        &metrics.PendingJobs,
        &metrics.RunningJobs,
        &metrics.CompletedJobs,
        &metrics.FailedJobs,
        &metrics.AvgDuration,
    )
    
    return &metrics, err
}
```

---

## 📋 Background Jobs Checklist

### Junior ✅
- [ ] Simple goroutine for async tasks
- [ ] Basic worker pool
- [ ] Channel-based job queue

### Mid ✅
- [ ] Asynq or similar library
- [ ] Task retry logic
- [ ] Multiple queues with priorities
- [ ] Scheduled jobs with cron

### Senior ✅
- [ ] Distributed locks
- [ ] Job status tracking
- [ ] Exponential backoff
- [ ] Job metrics & monitoring

### Expert ✅
- [ ] Multi-tenant job processing
- [ ] Dynamic worker scaling
- [ ] Dead letter queue
- [ ] Job dependency graph
