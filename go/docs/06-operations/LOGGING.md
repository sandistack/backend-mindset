# 📝 LOGGING - Logging di Go (Junior → Senior)

Dokumentasi lengkap tentang logging di Go - dari standard library hingga structured logging.

---

## 🎯 Logging di Go

```
Logging Levels (common):
DEBUG → INFO → WARN → ERROR → FATAL

Log Output:
- Console (stdout/stderr)
- File
- External services (ELK, Datadog, etc.)
```

---

## 1️⃣ JUNIOR LEVEL - Standard Library

### Basic log Package

```go
package main

import (
    "log"
    "os"
)

func main() {
    // Basic logging
    log.Println("This is a log message")
    log.Printf("User %s logged in", "john")
    
    // Fatal - logs and calls os.Exit(1)
    // log.Fatal("This is fatal")
    
    // Panic - logs and panics
    // log.Panic("This is panic")
}
```

### Log Flags

```go
package main

import (
    "log"
)

func main() {
    // Default flags
    log.SetFlags(log.LstdFlags) // date and time
    log.Println("Default flags")
    // Output: 2024/01/15 10:30:45 Default flags
    
    // With file and line number
    log.SetFlags(log.LstdFlags | log.Lshortfile)
    log.Println("With file info")
    // Output: 2024/01/15 10:30:45 main.go:15: With file info
    
    // With microseconds
    log.SetFlags(log.LstdFlags | log.Lmicroseconds)
    log.Println("With microseconds")
    // Output: 2024/01/15 10:30:45.123456 With microseconds
    
    // UTC time
    log.SetFlags(log.LstdFlags | log.LUTC)
    log.Println("UTC time")
    
    // Custom prefix
    log.SetPrefix("[APP] ")
    log.Println("With prefix")
    // Output: [APP] 2024/01/15 10:30:45 With prefix
}
```

### Log to File

```go
package main

import (
    "log"
    "os"
)

func main() {
    // Open file for logging
    file, err := os.OpenFile(
        "app.log",
        os.O_CREATE|os.O_WRONLY|os.O_APPEND,
        0666,
    )
    if err != nil {
        log.Fatal(err)
    }
    defer file.Close()
    
    // Set output to file
    log.SetOutput(file)
    log.Println("This goes to file")
    
    // Log to multiple outputs
    // mw := io.MultiWriter(os.Stdout, file)
    // log.SetOutput(mw)
}
```

---

## 2️⃣ MID LEVEL - Custom Logger

### Multiple Loggers

```go
package main

import (
    "io"
    "log"
    "os"
)

var (
    Debug   *log.Logger
    Info    *log.Logger
    Warning *log.Logger
    Error   *log.Logger
)

func init() {
    file, err := os.OpenFile("app.log", os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
    if err != nil {
        log.Fatal(err)
    }
    
    multi := io.MultiWriter(os.Stdout, file)
    
    Debug = log.New(os.Stdout, "DEBUG: ", log.Ldate|log.Ltime|log.Lshortfile)
    Info = log.New(multi, "INFO: ", log.Ldate|log.Ltime|log.Lshortfile)
    Warning = log.New(multi, "WARNING: ", log.Ldate|log.Ltime|log.Lshortfile)
    Error = log.New(multi, "ERROR: ", log.Ldate|log.Ltime|log.Lshortfile)
}

func main() {
    Debug.Println("This is a debug message")
    Info.Println("This is an info message")
    Warning.Println("This is a warning message")
    Error.Println("This is an error message")
}
```

### Logger Interface

```go
package logger

import (
    "io"
    "log"
    "os"
)

type LogLevel int

const (
    LevelDebug LogLevel = iota
    LevelInfo
    LevelWarn
    LevelError
)

type Logger interface {
    Debug(msg string, args ...interface{})
    Info(msg string, args ...interface{})
    Warn(msg string, args ...interface{})
    Error(msg string, args ...interface{})
}

type SimpleLogger struct {
    level   LogLevel
    debug   *log.Logger
    info    *log.Logger
    warn    *log.Logger
    errorL  *log.Logger
}

func NewSimpleLogger(level LogLevel, output io.Writer) *SimpleLogger {
    if output == nil {
        output = os.Stdout
    }
    
    flags := log.Ldate | log.Ltime | log.Lshortfile
    
    return &SimpleLogger{
        level:  level,
        debug:  log.New(output, "[DEBUG] ", flags),
        info:   log.New(output, "[INFO] ", flags),
        warn:   log.New(output, "[WARN] ", flags),
        errorL: log.New(output, "[ERROR] ", flags),
    }
}

func (l *SimpleLogger) Debug(msg string, args ...interface{}) {
    if l.level <= LevelDebug {
        l.debug.Printf(msg, args...)
    }
}

func (l *SimpleLogger) Info(msg string, args ...interface{}) {
    if l.level <= LevelInfo {
        l.info.Printf(msg, args...)
    }
}

func (l *SimpleLogger) Warn(msg string, args ...interface{}) {
    if l.level <= LevelWarn {
        l.warn.Printf(msg, args...)
    }
}

func (l *SimpleLogger) Error(msg string, args ...interface{}) {
    if l.level <= LevelError {
        l.errorL.Printf(msg, args...)
    }
}
```

---

## 3️⃣ MID-SENIOR LEVEL - Structured Logging with Zap

### Install Zap

```bash
go get go.uber.org/zap
```

### Basic Zap Usage

```go
package main

import (
    "go.uber.org/zap"
)

func main() {
    // Development logger (pretty printed)
    logger, _ := zap.NewDevelopment()
    defer logger.Sync()
    
    logger.Info("User logged in",
        zap.String("username", "john"),
        zap.Int("userId", 123),
    )
    
    // Production logger (JSON format)
    prodLogger, _ := zap.NewProduction()
    defer prodLogger.Sync()
    
    prodLogger.Info("User logged in",
        zap.String("username", "john"),
        zap.Int("userId", 123),
    )
    
    // Output (production):
    // {"level":"info","ts":1705312245.123,"caller":"main.go:20","msg":"User logged in","username":"john","userId":123}
}
```

### Sugared Logger (Easier Syntax)

```go
package main

import (
    "go.uber.org/zap"
)

func main() {
    logger, _ := zap.NewDevelopment()
    defer logger.Sync()
    
    sugar := logger.Sugar()
    
    // Printf style
    sugar.Infof("User %s logged in", "john")
    
    // Key-value pairs
    sugar.Infow("User logged in",
        "username", "john",
        "userId", 123,
        "role", "admin",
    )
    
    // Simple messages
    sugar.Info("Application started")
    sugar.Warn("Low memory")
    sugar.Error("Database connection failed")
}
```

### Custom Zap Configuration

```go
package logger

import (
    "os"
    
    "go.uber.org/zap"
    "go.uber.org/zap/zapcore"
)

func NewLogger(env string) *zap.Logger {
    var config zap.Config
    
    if env == "production" {
        config = zap.NewProductionConfig()
        config.Level = zap.NewAtomicLevelAt(zapcore.InfoLevel)
    } else {
        config = zap.NewDevelopmentConfig()
        config.Level = zap.NewAtomicLevelAt(zapcore.DebugLevel)
        config.EncoderConfig.EncodeLevel = zapcore.CapitalColorLevelEncoder
    }
    
    config.OutputPaths = []string{"stdout"}
    config.ErrorOutputPaths = []string{"stderr"}
    
    logger, err := config.Build()
    if err != nil {
        panic(err)
    }
    
    return logger
}

func NewLoggerWithFile(env, filepath string) *zap.Logger {
    // Create log file
    file, _ := os.OpenFile(filepath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
    
    // Encoder config
    encoderConfig := zap.NewProductionEncoderConfig()
    encoderConfig.TimeKey = "timestamp"
    encoderConfig.EncodeTime = zapcore.ISO8601TimeEncoder
    
    // Create cores
    fileEncoder := zapcore.NewJSONEncoder(encoderConfig)
    consoleEncoder := zapcore.NewConsoleEncoder(encoderConfig)
    
    fileCore := zapcore.NewCore(fileEncoder, zapcore.AddSync(file), zapcore.InfoLevel)
    consoleCore := zapcore.NewCore(consoleEncoder, zapcore.AddSync(os.Stdout), zapcore.DebugLevel)
    
    // Combine cores
    core := zapcore.NewTee(fileCore, consoleCore)
    
    return zap.New(core, zap.AddCaller(), zap.AddStacktrace(zapcore.ErrorLevel))
}
```

---

## 4️⃣ SENIOR LEVEL - Structured Logging with Zerolog

### Install Zerolog

```bash
go get github.com/rs/zerolog
```

### Basic Zerolog Usage

```go
package main

import (
    "os"
    
    "github.com/rs/zerolog"
    "github.com/rs/zerolog/log"
)

func main() {
    // Pretty console output
    log.Logger = log.Output(zerolog.ConsoleWriter{Out: os.Stdout})
    
    // Basic logging
    log.Info().Msg("Application started")
    
    // With fields
    log.Info().
        Str("username", "john").
        Int("userId", 123).
        Msg("User logged in")
    
    // With error
    err := errors.New("connection refused")
    log.Error().
        Err(err).
        Str("database", "postgres").
        Msg("Database connection failed")
    
    // Output:
    // 10:30:45 INF Application started
    // 10:30:45 INF User logged in username=john userId=123
    // 10:30:45 ERR Database connection failed database=postgres error="connection refused"
}
```

### Global Logger Setup

```go
package logger

import (
    "io"
    "os"
    "time"
    
    "github.com/rs/zerolog"
    "github.com/rs/zerolog/log"
)

func Setup(env string) {
    zerolog.TimeFieldFormat = time.RFC3339Nano
    
    var output io.Writer = os.Stdout
    
    if env == "development" {
        output = zerolog.ConsoleWriter{
            Out:        os.Stdout,
            TimeFormat: "15:04:05",
        }
        zerolog.SetGlobalLevel(zerolog.DebugLevel)
    } else {
        zerolog.SetGlobalLevel(zerolog.InfoLevel)
    }
    
    log.Logger = zerolog.New(output).
        With().
        Timestamp().
        Caller().
        Logger()
}

func SetupWithFile(filepath string) {
    file, _ := os.OpenFile(filepath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
    
    multi := zerolog.MultiLevelWriter(os.Stdout, file)
    
    log.Logger = zerolog.New(multi).
        With().
        Timestamp().
        Caller().
        Str("service", "my-api").
        Logger()
}
```

### Context Logger

```go
package main

import (
    "context"
    
    "github.com/rs/zerolog"
    "github.com/rs/zerolog/log"
)

func main() {
    // Create logger with context
    ctx := log.Logger.WithContext(context.Background())
    
    // Add request-specific fields
    logger := zerolog.Ctx(ctx).With().
        Str("requestId", "abc-123").
        Str("userId", "user-456").
        Logger()
    
    // Use throughout request
    ProcessRequest(logger.WithContext(ctx))
}

func ProcessRequest(ctx context.Context) {
    logger := zerolog.Ctx(ctx)
    
    logger.Info().Msg("Processing request")
    
    // Fields from parent context are preserved
}
```

---

## 5️⃣ SENIOR LEVEL - Gin Middleware Logging

### Zap Middleware

```go
package middleware

import (
    "time"
    
    "github.com/gin-gonic/gin"
    "go.uber.org/zap"
)

func ZapLogger(logger *zap.Logger) gin.HandlerFunc {
    return func(c *gin.Context) {
        start := time.Now()
        path := c.Request.URL.Path
        query := c.Request.URL.RawQuery
        
        // Process request
        c.Next()
        
        // Log after request
        latency := time.Since(start)
        status := c.Writer.Status()
        clientIP := c.ClientIP()
        method := c.Request.Method
        
        if len(c.Errors) > 0 {
            for _, e := range c.Errors.Errors() {
                logger.Error("Request error",
                    zap.String("error", e),
                    zap.String("path", path),
                    zap.String("method", method),
                )
            }
        }
        
        logger.Info("Request completed",
            zap.Int("status", status),
            zap.String("method", method),
            zap.String("path", path),
            zap.String("query", query),
            zap.String("ip", clientIP),
            zap.Duration("latency", latency),
            zap.String("user-agent", c.Request.UserAgent()),
        )
    }
}

func main() {
    logger, _ := zap.NewProduction()
    
    r := gin.New()
    r.Use(ZapLogger(logger))
    r.Use(gin.Recovery())
    
    r.GET("/", func(c *gin.Context) {
        c.JSON(200, gin.H{"message": "Hello"})
    })
    
    r.Run(":8080")
}
```

### Zerolog Middleware

```go
package middleware

import (
    "time"
    
    "github.com/gin-gonic/gin"
    "github.com/rs/zerolog"
)

func ZerologLogger(logger zerolog.Logger) gin.HandlerFunc {
    return func(c *gin.Context) {
        start := time.Now()
        
        // Add request ID to context
        requestID := c.GetHeader("X-Request-ID")
        if requestID == "" {
            requestID = uuid.New().String()
        }
        
        // Create request-scoped logger
        reqLogger := logger.With().
            Str("requestId", requestID).
            Str("method", c.Request.Method).
            Str("path", c.Request.URL.Path).
            Logger()
        
        // Add to context
        c.Set("logger", reqLogger)
        c.Header("X-Request-ID", requestID)
        
        // Process request
        c.Next()
        
        // Log completion
        latency := time.Since(start)
        status := c.Writer.Status()
        
        event := reqLogger.Info()
        if status >= 500 {
            event = reqLogger.Error()
        } else if status >= 400 {
            event = reqLogger.Warn()
        }
        
        event.
            Int("status", status).
            Dur("latency", latency).
            Str("clientIP", c.ClientIP()).
            Msg("Request completed")
    }
}

// Helper to get logger from context
func GetLogger(c *gin.Context) zerolog.Logger {
    logger, exists := c.Get("logger")
    if !exists {
        return zerolog.Nop()
    }
    return logger.(zerolog.Logger)
}
```

---

## 6️⃣ EXPERT LEVEL - Correlation & Tracing

### Request Correlation

```go
package middleware

import (
    "context"
    
    "github.com/gin-gonic/gin"
    "github.com/google/uuid"
    "github.com/rs/zerolog"
    "github.com/rs/zerolog/log"
)

type contextKey string

const LoggerKey contextKey = "logger"

func CorrelationMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        // Get or generate correlation ID
        correlationID := c.GetHeader("X-Correlation-ID")
        if correlationID == "" {
            correlationID = uuid.New().String()
        }
        
        // Get trace headers (for distributed tracing)
        traceID := c.GetHeader("X-Trace-ID")
        spanID := c.GetHeader("X-Span-ID")
        
        // Create correlated logger
        logger := log.With().
            Str("correlationId", correlationID).
            Str("traceId", traceID).
            Str("spanId", spanID).
            Logger()
        
        // Store in context
        ctx := context.WithValue(c.Request.Context(), LoggerKey, logger)
        c.Request = c.Request.WithContext(ctx)
        
        // Set response headers
        c.Header("X-Correlation-ID", correlationID)
        
        c.Next()
    }
}

// Logger from context
func LoggerFromContext(ctx context.Context) zerolog.Logger {
    if logger, ok := ctx.Value(LoggerKey).(zerolog.Logger); ok {
        return logger
    }
    return log.Logger
}

// Usage in service
func (s *UserService) GetUser(ctx context.Context, id uint) (*User, error) {
    logger := LoggerFromContext(ctx)
    
    logger.Debug().
        Uint("userId", id).
        Msg("Fetching user")
    
    user, err := s.repo.FindByID(id)
    if err != nil {
        logger.Error().
            Err(err).
            Uint("userId", id).
            Msg("Failed to fetch user")
        return nil, err
    }
    
    logger.Info().
        Uint("userId", id).
        Str("username", user.Name).
        Msg("User fetched successfully")
    
    return user, nil
}
```

### Distributed Tracing Context

```go
package tracing

import (
    "context"
    "net/http"
    
    "github.com/google/uuid"
    "github.com/rs/zerolog"
)

type TraceContext struct {
    TraceID       string
    SpanID        string
    ParentSpanID  string
    CorrelationID string
}

func ExtractTraceContext(r *http.Request) TraceContext {
    return TraceContext{
        TraceID:       getOrGenerate(r.Header.Get("X-Trace-ID")),
        SpanID:        uuid.New().String()[:8],
        ParentSpanID:  r.Header.Get("X-Span-ID"),
        CorrelationID: getOrGenerate(r.Header.Get("X-Correlation-ID")),
    }
}

func getOrGenerate(value string) string {
    if value == "" {
        return uuid.New().String()
    }
    return value
}

func (tc TraceContext) Logger(base zerolog.Logger) zerolog.Logger {
    return base.With().
        Str("traceId", tc.TraceID).
        Str("spanId", tc.SpanID).
        Str("parentSpanId", tc.ParentSpanID).
        Str("correlationId", tc.CorrelationID).
        Logger()
}

func (tc TraceContext) InjectHeaders(r *http.Request) {
    r.Header.Set("X-Trace-ID", tc.TraceID)
    r.Header.Set("X-Span-ID", tc.SpanID)
    r.Header.Set("X-Correlation-ID", tc.CorrelationID)
}
```

---

## 7️⃣ EXPERT LEVEL - Log Rotation

### Lumberjack for Rotation

```bash
go get gopkg.in/natefinch/lumberjack.v2
```

```go
package logger

import (
    "io"
    "os"
    
    "github.com/rs/zerolog"
    "gopkg.in/natefinch/lumberjack.v2"
)

func NewRotatingLogger() zerolog.Logger {
    // File rotation config
    fileWriter := &lumberjack.Logger{
        Filename:   "logs/app.log",
        MaxSize:    100, // MB
        MaxBackups: 5,
        MaxAge:     30, // days
        Compress:   true,
    }
    
    // Multi-writer for console and file
    multiWriter := io.MultiWriter(
        zerolog.ConsoleWriter{Out: os.Stdout},
        fileWriter,
    )
    
    return zerolog.New(multiWriter).
        With().
        Timestamp().
        Caller().
        Logger()
}

// With Zap
func NewZapRotatingLogger() *zap.Logger {
    // File rotation
    fileWriter := zapcore.AddSync(&lumberjack.Logger{
        Filename:   "logs/app.log",
        MaxSize:    100,
        MaxBackups: 5,
        MaxAge:     30,
        Compress:   true,
    })
    
    encoderConfig := zap.NewProductionEncoderConfig()
    encoderConfig.TimeKey = "timestamp"
    encoderConfig.EncodeTime = zapcore.ISO8601TimeEncoder
    
    core := zapcore.NewCore(
        zapcore.NewJSONEncoder(encoderConfig),
        fileWriter,
        zapcore.InfoLevel,
    )
    
    return zap.New(core, zap.AddCaller())
}
```

---

## 📊 Logging Comparison

### Libraries Comparison

| Feature | log (std) | Zap | Zerolog |
|---------|-----------|-----|---------|
| Performance | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Structured | ❌ | ✅ | ✅ |
| JSON | ❌ | ✅ | ✅ |
| Levels | ❌ | ✅ | ✅ |
| Zero alloc | ❌ | ✅ | ✅ |
| Context | ❌ | ✅ | ✅ |
| Learning curve | Easy | Medium | Medium |

### Log Levels

| Level | Use Case |
|-------|----------|
| DEBUG | Development only, verbose info |
| INFO | Normal operations, milestones |
| WARN | Potential issues, non-critical |
| ERROR | Errors that need attention |
| FATAL | Application cannot continue |

### Best Practices

```go
// ✅ GOOD - Structured with context
logger.Info().
    Str("userId", user.ID).
    Str("action", "login").
    Dur("duration", elapsed).
    Msg("User login successful")

// ❌ BAD - Unstructured
log.Printf("User %s logged in, took %v", user.ID, elapsed)

// ✅ GOOD - Error with context
logger.Error().
    Err(err).
    Str("operation", "database_query").
    Str("query", "SELECT * FROM users").
    Msg("Query failed")

// ❌ BAD - Just error
log.Printf("Error: %v", err)
```

---

## 💡 Summary

| Level | Focus |
|-------|-------|
| **Junior** | Standard log package, basic logging |
| **Mid** | Custom loggers, log levels |
| **Mid-Senior** | Zap/Zerolog, structured logging |
| **Senior** | Request logging, middleware |
| **Expert** | Correlation, tracing, rotation |

**Best Practices:**
- ✅ Use structured logging in production
- ✅ Include correlation IDs for tracing
- ✅ Log with appropriate levels
- ✅ Include relevant context (userID, requestID)
- ✅ Set up log rotation
- ✅ Use JSON format for production
- ❌ Don't log sensitive data (passwords, tokens)
- ❌ Don't over-log (performance impact)
- ❌ Don't use fmt.Println for logging
