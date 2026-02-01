# 🔌 WebSocket di Go

## Kenapa Penting?

WebSocket untuk:
- ✅ Real-time communication
- ✅ Bidirectional data flow
- ✅ Low latency
- ✅ Persistent connections

---

## 📚 Daftar Isi

1. [WebSocket Basics](#1️⃣-websocket-basics)
2. [Gorilla WebSocket](#2️⃣-gorilla-websocket)
3. [Connection Management](#3️⃣-connection-management)
4. [Broadcast & Rooms](#4️⃣-broadcast--rooms)
5. [Authentication & Security](#5️⃣-authentication--security)
6. [Production Patterns](#6️⃣-production-patterns)

---

## 1️⃣ WebSocket Basics

### HTTP Upgrade

```
Client                          Server
  |                               |
  |  GET /ws HTTP/1.1             |
  |  Upgrade: websocket           |
  |  Connection: Upgrade          |
  | ----------------------------> |
  |                               |
  |  HTTP/1.1 101 Switching       |
  |  Upgrade: websocket           |
  |  Connection: Upgrade          |
  | <---------------------------- |
  |                               |
  |  WebSocket Frame              |
  | <----------------------------> |
```

### Message Types

```go
const (
    TextMessage   = 1
    BinaryMessage = 2
    CloseMessage  = 8
    PingMessage   = 9
    PongMessage   = 10
)
```

---

## 2️⃣ Gorilla WebSocket

### Installation

```bash
go get github.com/gorilla/websocket
```

### Basic Server

```go
// internal/websocket/server.go
package websocket

import (
    "fmt"
    "log"
    "net/http"
    
    "github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{
    ReadBufferSize:  1024,
    WriteBufferSize: 1024,
    CheckOrigin: func(r *http.Request) bool {
        // Allow all connections (customize for production)
        return true
    },
}

func HandleWebSocket(w http.ResponseWriter, r *http.Request) {
    conn, err := upgrader.Upgrade(w, r, nil)
    if err != nil {
        log.Printf("Upgrade error: %v", err)
        return
    }
    defer conn.Close()
    
    log.Println("Client connected")
    
    for {
        messageType, message, err := conn.ReadMessage()
        if err != nil {
            log.Printf("Read error: %v", err)
            break
        }
        
        log.Printf("Received: %s", message)
        
        // Echo back
        err = conn.WriteMessage(messageType, message)
        if err != nil {
            log.Printf("Write error: %v", err)
            break
        }
    }
}

// Setup routes
func SetupRoutes() {
    http.HandleFunc("/ws", HandleWebSocket)
    log.Fatal(http.ListenAndServe(":8080", nil))
}
```

### Client

```go
// internal/websocket/client.go
package websocket

import (
    "log"
    "time"
    
    "github.com/gorilla/websocket"
)

func ConnectClient() {
    url := "ws://localhost:8080/ws"
    
    conn, _, err := websocket.DefaultDialer.Dial(url, nil)
    if err != nil {
        log.Fatal("Dial error:", err)
    }
    defer conn.Close()
    
    // Send message
    err = conn.WriteMessage(websocket.TextMessage, []byte("Hello, Server!"))
    if err != nil {
        log.Fatal("Write error:", err)
    }
    
    // Read response
    _, message, err := conn.ReadMessage()
    if err != nil {
        log.Fatal("Read error:", err)
    }
    
    log.Printf("Received: %s", message)
}
```

---

## 3️⃣ Connection Management

### Client Connection

```go
// internal/websocket/client.go
package websocket

import (
    "encoding/json"
    "log"
    "sync"
    "time"
    
    "github.com/gorilla/websocket"
)

type Client struct {
    conn     *websocket.Conn
    send     chan []byte
    hub      *Hub
    userID   int
    mu       sync.Mutex
}

func NewClient(conn *websocket.Conn, hub *Hub, userID int) *Client {
    return &Client{
        conn:   conn,
        send:   make(chan []byte, 256),
        hub:    hub,
        userID: userID,
    }
}

// Read messages from client
func (c *Client) ReadPump() {
    defer func() {
        c.hub.Unregister(c)
        c.conn.Close()
    }()
    
    c.conn.SetReadDeadline(time.Now().Add(60 * time.Second))
    c.conn.SetPongHandler(func(string) error {
        c.conn.SetReadDeadline(time.Now().Add(60 * time.Second))
        return nil
    })
    
    for {
        _, message, err := c.conn.ReadMessage()
        if err != nil {
            if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
                log.Printf("Error: %v", err)
            }
            break
        }
        
        // Process message
        c.handleMessage(message)
    }
}

// Write messages to client
func (c *Client) WritePump() {
    ticker := time.NewTicker(54 * time.Second)
    defer func() {
        ticker.Stop()
        c.conn.Close()
    }()
    
    for {
        select {
        case message, ok := <-c.send:
            c.conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
            if !ok {
                c.conn.WriteMessage(websocket.CloseMessage, []byte{})
                return
            }
            
            w, err := c.conn.NextWriter(websocket.TextMessage)
            if err != nil {
                return
            }
            w.Write(message)
            
            // Add queued messages to current websocket message
            n := len(c.send)
            for i := 0; i < n; i++ {
                w.Write([]byte{'\n'})
                w.Write(<-c.send)
            }
            
            if err := w.Close(); err != nil {
                return
            }
            
        case <-ticker.C:
            c.conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
            if err := c.conn.WriteMessage(websocket.PingMessage, nil); err != nil {
                return
            }
        }
    }
}

func (c *Client) handleMessage(message []byte) {
    var msg Message
    if err := json.Unmarshal(message, &msg); err != nil {
        log.Printf("Error unmarshaling message: %v", err)
        return
    }
    
    switch msg.Type {
    case "chat":
        c.hub.Broadcast(msg)
    case "private":
        c.hub.SendToUser(msg.RecipientID, msg)
    default:
        log.Printf("Unknown message type: %s", msg.Type)
    }
}
```

### Message Structure

```go
// internal/websocket/message.go
package websocket

import "time"

type Message struct {
    Type        string      `json:"type"`
    Payload     interface{} `json:"payload"`
    SenderID    int         `json:"sender_id"`
    RecipientID int         `json:"recipient_id,omitempty"`
    Timestamp   time.Time   `json:"timestamp"`
}

type ChatMessage struct {
    Text   string `json:"text"`
    RoomID string `json:"room_id"`
}

type NotificationMessage struct {
    Title string `json:"title"`
    Body  string `json:"body"`
}
```

---

## 4️⃣ Broadcast & Rooms

### Hub (Connection Manager)

```go
// internal/websocket/hub.go
package websocket

import (
    "encoding/json"
    "log"
    "sync"
)

type Hub struct {
    clients    map[*Client]bool
    broadcast  chan []byte
    register   chan *Client
    unregister chan *Client
    rooms      map[string]map[*Client]bool
    mu         sync.RWMutex
}

func NewHub() *Hub {
    return &Hub{
        clients:    make(map[*Client]bool),
        broadcast:  make(chan []byte),
        register:   make(chan *Client),
        unregister: make(chan *Client),
        rooms:      make(map[string]map[*Client]bool),
    }
}

func (h *Hub) Run() {
    for {
        select {
        case client := <-h.register:
            h.mu.Lock()
            h.clients[client] = true
            h.mu.Unlock()
            log.Printf("Client registered: %d", client.userID)
            
        case client := <-h.unregister:
            h.mu.Lock()
            if _, ok := h.clients[client]; ok {
                delete(h.clients, client)
                close(client.send)
                log.Printf("Client unregistered: %d", client.userID)
            }
            h.mu.Unlock()
            
        case message := <-h.broadcast:
            h.mu.RLock()
            for client := range h.clients {
                select {
                case client.send <- message:
                default:
                    close(client.send)
                    delete(h.clients, client)
                }
            }
            h.mu.RUnlock()
        }
    }
}

func (h *Hub) Register(client *Client) {
    h.register <- client
}

func (h *Hub) Unregister(client *Client) {
    h.unregister <- client
}

func (h *Hub) Broadcast(message Message) {
    data, err := json.Marshal(message)
    if err != nil {
        log.Printf("Error marshaling message: %v", err)
        return
    }
    h.broadcast <- data
}

// Send to specific user
func (h *Hub) SendToUser(userID int, message Message) {
    data, err := json.Marshal(message)
    if err != nil {
        return
    }
    
    h.mu.RLock()
    defer h.mu.RUnlock()
    
    for client := range h.clients {
        if client.userID == userID {
            select {
            case client.send <- data:
            default:
                close(client.send)
                delete(h.clients, client)
            }
        }
    }
}

// Room management
func (h *Hub) JoinRoom(client *Client, roomID string) {
    h.mu.Lock()
    defer h.mu.Unlock()
    
    if _, ok := h.rooms[roomID]; !ok {
        h.rooms[roomID] = make(map[*Client]bool)
    }
    h.rooms[roomID][client] = true
    log.Printf("Client %d joined room %s", client.userID, roomID)
}

func (h *Hub) LeaveRoom(client *Client, roomID string) {
    h.mu.Lock()
    defer h.mu.Unlock()
    
    if room, ok := h.rooms[roomID]; ok {
        delete(room, client)
        if len(room) == 0 {
            delete(h.rooms, roomID)
        }
    }
}

func (h *Hub) BroadcastToRoom(roomID string, message Message) {
    data, err := json.Marshal(message)
    if err != nil {
        return
    }
    
    h.mu.RLock()
    defer h.mu.RUnlock()
    
    if room, ok := h.rooms[roomID]; ok {
        for client := range room {
            select {
            case client.send <- data:
            default:
                close(client.send)
                delete(h.clients, client)
                delete(room, client)
            }
        }
    }
}
```

### Usage

```go
// cmd/server/main.go
package main

import (
    "log"
    "net/http"
    
    "myapp/internal/websocket"
)

func main() {
    hub := websocket.NewHub()
    go hub.Run()
    
    http.HandleFunc("/ws", func(w http.ResponseWriter, r *http.Request) {
        websocket.ServeWs(hub, w, r)
    })
    
    log.Println("Server started on :8080")
    log.Fatal(http.ListenAndServe(":8080", nil))
}
```

---

## 5️⃣ Authentication & Security

### JWT Authentication

```go
// internal/websocket/auth.go
package websocket

import (
    "errors"
    "net/http"
    "strings"
    
    "github.com/golang-jwt/jwt/v4"
)

func ServeWs(hub *Hub, w http.ResponseWriter, r *http.Request) {
    // Authenticate
    token := r.URL.Query().Get("token")
    if token == "" {
        token = extractTokenFromHeader(r)
    }
    
    userID, err := validateToken(token)
    if err != nil {
        http.Error(w, "Unauthorized", http.StatusUnauthorized)
        return
    }
    
    // Upgrade connection
    conn, err := upgrader.Upgrade(w, r, nil)
    if err != nil {
        log.Println(err)
        return
    }
    
    client := NewClient(conn, hub, userID)
    hub.Register(client)
    
    go client.WritePump()
    go client.ReadPump()
}

func extractTokenFromHeader(r *http.Request) string {
    bearerToken := r.Header.Get("Authorization")
    if len(strings.Split(bearerToken, " ")) == 2 {
        return strings.Split(bearerToken, " ")[1]
    }
    return ""
}

func validateToken(tokenString string) (int, error) {
    token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
        return []byte("your-secret-key"), nil
    })
    
    if err != nil {
        return 0, err
    }
    
    if claims, ok := token.Claims.(jwt.MapClaims); ok && token.Valid {
        userID := int(claims["user_id"].(float64))
        return userID, nil
    }
    
    return 0, errors.New("invalid token")
}
```

### Origin Check

```go
var upgrader = websocket.Upgrader{
    ReadBufferSize:  1024,
    WriteBufferSize: 1024,
    CheckOrigin: func(r *http.Request) bool {
        origin := r.Header.Get("Origin")
        allowedOrigins := []string{
            "https://example.com",
            "https://app.example.com",
        }
        
        for _, allowed := range allowedOrigins {
            if origin == allowed {
                return true
            }
        }
        
        return false
    },
}
```

### Rate Limiting

```go
// internal/websocket/rate_limit.go
package websocket

import (
    "sync"
    "time"
)

type RateLimiter struct {
    clients map[int]*ClientLimiter
    mu      sync.RWMutex
}

type ClientLimiter struct {
    tokens     int
    lastRefill time.Time
    maxTokens  int
    refillRate time.Duration
}

func NewRateLimiter() *RateLimiter {
    return &RateLimiter{
        clients: make(map[int]*ClientLimiter),
    }
}

func (rl *RateLimiter) Allow(userID int) bool {
    rl.mu.Lock()
    defer rl.mu.Unlock()
    
    limiter, exists := rl.clients[userID]
    if !exists {
        limiter = &ClientLimiter{
            tokens:     10,
            maxTokens:  10,
            refillRate: time.Second,
            lastRefill: time.Now(),
        }
        rl.clients[userID] = limiter
    }
    
    // Refill tokens
    now := time.Now()
    elapsed := now.Sub(limiter.lastRefill)
    tokensToAdd := int(elapsed / limiter.refillRate)
    
    if tokensToAdd > 0 {
        limiter.tokens = min(limiter.maxTokens, limiter.tokens+tokensToAdd)
        limiter.lastRefill = now
    }
    
    // Check if allowed
    if limiter.tokens > 0 {
        limiter.tokens--
        return true
    }
    
    return false
}

func min(a, b int) int {
    if a < b {
        return a
    }
    return b
}
```

---

## 6️⃣ Production Patterns

### Connection Pool

```go
// internal/websocket/pool.go
package websocket

import (
    "sync"
)

type ConnectionPool struct {
    maxConnections int
    activeConns    int
    mu             sync.Mutex
}

func NewConnectionPool(max int) *ConnectionPool {
    return &ConnectionPool{
        maxConnections: max,
        activeConns:    0,
    }
}

func (p *ConnectionPool) Acquire() bool {
    p.mu.Lock()
    defer p.mu.Unlock()
    
    if p.activeConns >= p.maxConnections {
        return false
    }
    
    p.activeConns++
    return true
}

func (p *ConnectionPool) Release() {
    p.mu.Lock()
    defer p.mu.Unlock()
    
    if p.activeConns > 0 {
        p.activeConns--
    }
}
```

### Reconnection Strategy

```go
// Client-side reconnection
func ConnectWithRetry(url string, maxRetries int) (*websocket.Conn, error) {
    var conn *websocket.Conn
    var err error
    
    for i := 0; i < maxRetries; i++ {
        conn, _, err = websocket.DefaultDialer.Dial(url, nil)
        if err == nil {
            return conn, nil
        }
        
        // Exponential backoff
        backoff := time.Duration(1<<uint(i)) * time.Second
        log.Printf("Connection failed, retrying in %v...", backoff)
        time.Sleep(backoff)
    }
    
    return nil, err
}
```

### Graceful Shutdown

```go
// internal/websocket/shutdown.go
package websocket

import (
    "context"
    "log"
    "time"
)

func (h *Hub) Shutdown(ctx context.Context) error {
    log.Println("Shutting down WebSocket hub...")
    
    h.mu.Lock()
    defer h.mu.Unlock()
    
    // Send close message to all clients
    closeMessage := websocket.FormatCloseMessage(websocket.CloseGoingAway, "Server shutting down")
    
    for client := range h.clients {
        client.conn.WriteControl(
            websocket.CloseMessage,
            closeMessage,
            time.Now().Add(time.Second),
        )
        client.conn.Close()
        delete(h.clients, client)
    }
    
    log.Println("All WebSocket connections closed")
    return nil
}
```

### Monitoring

```go
// internal/websocket/metrics.go
package websocket

import (
    "sync/atomic"
    "time"
)

type Metrics struct {
    activeConnections  int64
    totalConnections   int64
    messagesReceived   int64
    messagesSent       int64
    errors             int64
    startTime          time.Time
}

func NewMetrics() *Metrics {
    return &Metrics{
        startTime: time.Now(),
    }
}

func (m *Metrics) IncrementConnections() {
    atomic.AddInt64(&m.activeConnections, 1)
    atomic.AddInt64(&m.totalConnections, 1)
}

func (m *Metrics) DecrementConnections() {
    atomic.AddInt64(&m.activeConnections, -1)
}

func (m *Metrics) IncrementMessagesReceived() {
    atomic.AddInt64(&m.messagesReceived, 1)
}

func (m *Metrics) IncrementMessagesSent() {
    atomic.AddInt64(&m.messagesSent, 1)
}

func (m *Metrics) IncrementErrors() {
    atomic.AddInt64(&m.errors, 1)
}

func (m *Metrics) GetStats() map[string]interface{} {
    return map[string]interface{}{
        "active_connections": atomic.LoadInt64(&m.activeConnections),
        "total_connections":  atomic.LoadInt64(&m.totalConnections),
        "messages_received":  atomic.LoadInt64(&m.messagesReceived),
        "messages_sent":      atomic.LoadInt64(&m.messagesSent),
        "errors":             atomic.LoadInt64(&m.errors),
        "uptime":             time.Since(m.startTime).String(),
    }
}
```

---

## 📋 WebSocket Checklist

### Junior ✅
- [ ] Basic WebSocket connection
- [ ] Echo server
- [ ] Simple message handling

### Mid ✅
- [ ] Connection management
- [ ] Broadcast messages
- [ ] Room-based messaging
- [ ] Ping/Pong heartbeat

### Senior ✅
- [ ] Authentication & authorization
- [ ] Rate limiting
- [ ] Graceful shutdown
- [ ] Error handling & reconnection

### Expert ✅
- [ ] Horizontal scaling (Redis pub/sub)
- [ ] Message persistence
- [ ] Metrics & monitoring
- [ ] Load balancing WebSocket connections
