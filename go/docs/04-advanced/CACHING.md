# 🚀 Caching di Go

## Kenapa Penting?

Caching untuk:
- ✅ Reduce database load
- ✅ Improve response time
- ✅ Scale horizontally
- ✅ Lower infrastructure cost

---

## 📚 Daftar Isi

1. [In-Memory Cache](#1️⃣-in-memory-cache)
2. [Redis Integration](#2️⃣-redis-integration)
3. [Cache-Aside Pattern](#3️⃣-cache-aside-pattern)
4. [Cache Invalidation](#4️⃣-cache-invalidation)
5. [Distributed Cache](#5️⃣-distributed-cache)
6. [Advanced Patterns](#6️⃣-advanced-patterns)

---

## 1️⃣ In-Memory Cache

### Simple Map-Based Cache

```go
// internal/cache/memory.go
package cache

import (
    "sync"
    "time"
)

type Item struct {
    Value      interface{}
    Expiration int64
}

func (item Item) IsExpired() bool {
    if item.Expiration == 0 {
        return false
    }
    return time.Now().UnixNano() > item.Expiration
}

type MemoryCache struct {
    items map[string]Item
    mu    sync.RWMutex
}

func NewMemoryCache() *MemoryCache {
    cache := &MemoryCache{
        items: make(map[string]Item),
    }
    
    // Start cleanup goroutine
    go cache.cleanupExpired()
    
    return cache
}

func (c *MemoryCache) Set(key string, value interface{}, ttl time.Duration) {
    c.mu.Lock()
    defer c.mu.Unlock()
    
    var expiration int64
    if ttl > 0 {
        expiration = time.Now().Add(ttl).UnixNano()
    }
    
    c.items[key] = Item{
        Value:      value,
        Expiration: expiration,
    }
}

func (c *MemoryCache) Get(key string) (interface{}, bool) {
    c.mu.RLock()
    defer c.mu.RUnlock()
    
    item, found := c.items[key]
    if !found {
        return nil, false
    }
    
    if item.IsExpired() {
        return nil, false
    }
    
    return item.Value, true
}

func (c *MemoryCache) Delete(key string) {
    c.mu.Lock()
    defer c.mu.Unlock()
    delete(c.items, key)
}

func (c *MemoryCache) Clear() {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.items = make(map[string]Item)
}

func (c *MemoryCache) cleanupExpired() {
    ticker := time.NewTicker(time.Minute)
    defer ticker.Stop()
    
    for range ticker.C {
        c.mu.Lock()
        for key, item := range c.items {
            if item.IsExpired() {
                delete(c.items, key)
            }
        }
        c.mu.Unlock()
    }
}
```

### Using go-cache Library

```bash
go get github.com/patrickmn/go-cache
```

```go
// internal/cache/gocache.go
package cache

import (
    "time"
    
    gocache "github.com/patrickmn/go-cache"
)

type GoCache struct {
    cache *gocache.Cache
}

func NewGoCache(defaultExpiration, cleanupInterval time.Duration) *GoCache {
    return &GoCache{
        cache: gocache.New(defaultExpiration, cleanupInterval),
    }
}

func (c *GoCache) Set(key string, value interface{}, ttl time.Duration) {
    c.cache.Set(key, value, ttl)
}

func (c *GoCache) Get(key string) (interface{}, bool) {
    return c.cache.Get(key)
}

func (c *GoCache) Delete(key string) {
    c.cache.Delete(key)
}

func (c *GoCache) Clear() {
    c.cache.Flush()
}

// Increment counter
func (c *GoCache) Increment(key string, delta int64) error {
    return c.cache.Increment(key, delta)
}
```

---

## 2️⃣ Redis Integration

### Redis Client Setup

```bash
go get github.com/go-redis/redis/v8
```

```go
// internal/cache/redis.go
package cache

import (
    "context"
    "encoding/json"
    "time"
    
    "github.com/go-redis/redis/v8"
)

type RedisCache struct {
    client *redis.Client
}

func NewRedisCache(addr string) *RedisCache {
    client := redis.NewClient(&redis.Options{
        Addr:     addr,
        Password: "",
        DB:       0,
    })
    
    return &RedisCache{client: client}
}

func (c *RedisCache) Set(ctx context.Context, key string, value interface{}, ttl time.Duration) error {
    data, err := json.Marshal(value)
    if err != nil {
        return err
    }
    
    return c.client.Set(ctx, key, data, ttl).Err()
}

func (c *RedisCache) Get(ctx context.Context, key string, dest interface{}) error {
    data, err := c.client.Get(ctx, key).Bytes()
    if err != nil {
        return err
    }
    
    return json.Unmarshal(data, dest)
}

func (c *RedisCache) Delete(ctx context.Context, keys ...string) error {
    return c.client.Del(ctx, keys...).Err()
}

func (c *RedisCache) Exists(ctx context.Context, key string) (bool, error) {
    count, err := c.client.Exists(ctx, key).Result()
    return count > 0, err
}

func (c *RedisCache) Clear(ctx context.Context) error {
    return c.client.FlushDB(ctx).Err()
}

func (c *RedisCache) Close() error {
    return c.client.Close()
}
```

### String Operations

```go
func (c *RedisCache) SetString(ctx context.Context, key, value string, ttl time.Duration) error {
    return c.client.Set(ctx, key, value, ttl).Err()
}

func (c *RedisCache) GetString(ctx context.Context, key string) (string, error) {
    return c.client.Get(ctx, key).Result()
}

func (c *RedisCache) Increment(ctx context.Context, key string) (int64, error) {
    return c.client.Incr(ctx, key).Result()
}

func (c *RedisCache) IncrementBy(ctx context.Context, key string, value int64) (int64, error) {
    return c.client.IncrBy(ctx, key, value).Result()
}
```

### Hash Operations

```go
func (c *RedisCache) HSet(ctx context.Context, key, field string, value interface{}) error {
    return c.client.HSet(ctx, key, field, value).Err()
}

func (c *RedisCache) HGet(ctx context.Context, key, field string) (string, error) {
    return c.client.HGet(ctx, key, field).Result()
}

func (c *RedisCache) HGetAll(ctx context.Context, key string) (map[string]string, error) {
    return c.client.HGetAll(ctx, key).Result()
}

func (c *RedisCache) HDelete(ctx context.Context, key string, fields ...string) error {
    return c.client.HDel(ctx, key, fields...).Err()
}
```

### List Operations

```go
func (c *RedisCache) LPush(ctx context.Context, key string, values ...interface{}) error {
    return c.client.LPush(ctx, key, values...).Err()
}

func (c *RedisCache) RPush(ctx context.Context, key string, values ...interface{}) error {
    return c.client.RPush(ctx, key, values...).Err()
}

func (c *RedisCache) LRange(ctx context.Context, key string, start, stop int64) ([]string, error) {
    return c.client.LRange(ctx, key, start, stop).Result()
}
```

### Set Operations

```go
func (c *RedisCache) SAdd(ctx context.Context, key string, members ...interface{}) error {
    return c.client.SAdd(ctx, key, members...).Err()
}

func (c *RedisCache) SMembers(ctx context.Context, key string) ([]string, error) {
    return c.client.SMembers(ctx, key).Result()
}

func (c *RedisCache) SIsMember(ctx context.Context, key string, member interface{}) (bool, error) {
    return c.client.SIsMember(ctx, key, member).Result()
}
```

---

## 3️⃣ Cache-Aside Pattern

### Repository with Cache

```go
// internal/repository/user_repo.go
package repository

import (
    "context"
    "fmt"
    "time"
    
    "myapp/internal/cache"
    "myapp/internal/domain"
)

type UserRepository struct {
    db    *sql.DB
    cache cache.Cache
}

func NewUserRepository(db *sql.DB, cache cache.Cache) *UserRepository {
    return &UserRepository{
        db:    db,
        cache: cache,
    }
}

func (r *UserRepository) GetByID(ctx context.Context, id int) (*domain.User, error) {
    cacheKey := fmt.Sprintf("user:%d", id)
    
    // Try cache first
    var user domain.User
    err := r.cache.Get(ctx, cacheKey, &user)
    if err == nil {
        return &user, nil
    }
    
    // Cache miss - query database
    query := "SELECT id, email, name FROM users WHERE id = $1"
    err = r.db.QueryRowContext(ctx, query, id).Scan(&user.ID, &user.Email, &user.Name)
    if err != nil {
        return nil, err
    }
    
    // Store in cache
    r.cache.Set(ctx, cacheKey, user, 5*time.Minute)
    
    return &user, nil
}

func (r *UserRepository) Update(ctx context.Context, user *domain.User) error {
    query := "UPDATE users SET email = $1, name = $2 WHERE id = $3"
    _, err := r.db.ExecContext(ctx, query, user.Email, user.Name, user.ID)
    if err != nil {
        return err
    }
    
    // Invalidate cache
    cacheKey := fmt.Sprintf("user:%d", user.ID)
    r.cache.Delete(ctx, cacheKey)
    
    return nil
}

func (r *UserRepository) Delete(ctx context.Context, id int) error {
    query := "DELETE FROM users WHERE id = $1"
    _, err := r.db.ExecContext(ctx, query, id)
    if err != nil {
        return err
    }
    
    // Invalidate cache
    cacheKey := fmt.Sprintf("user:%d", id)
    r.cache.Delete(ctx, cacheKey)
    
    return nil
}
```

### Cache Interface

```go
// internal/cache/cache.go
package cache

import (
    "context"
    "time"
)

type Cache interface {
    Set(ctx context.Context, key string, value interface{}, ttl time.Duration) error
    Get(ctx context.Context, key string, dest interface{}) error
    Delete(ctx context.Context, keys ...string) error
    Exists(ctx context.Context, key string) (bool, error)
}
```

---

## 4️⃣ Cache Invalidation

### Tag-Based Invalidation

```go
// internal/cache/tagged_cache.go
package cache

import (
    "context"
    "fmt"
    "time"
)

type TaggedCache struct {
    cache Cache
}

func NewTaggedCache(cache Cache) *TaggedCache {
    return &TaggedCache{cache: cache}
}

func (c *TaggedCache) SetWithTags(ctx context.Context, key string, value interface{}, ttl time.Duration, tags []string) error {
    // Store the actual value
    if err := c.cache.Set(ctx, key, value, ttl); err != nil {
        return err
    }
    
    // Store tags for this key
    for _, tag := range tags {
        tagKey := fmt.Sprintf("tag:%s", tag)
        // Add key to the tag's set
        if err := c.cache.SAdd(ctx, tagKey, key); err != nil {
            return err
        }
    }
    
    return nil
}

func (c *TaggedCache) InvalidateByTag(ctx context.Context, tag string) error {
    tagKey := fmt.Sprintf("tag:%s", tag)
    
    // Get all keys with this tag
    keys, err := c.cache.SMembers(ctx, tagKey)
    if err != nil {
        return err
    }
    
    // Delete all keys
    if len(keys) > 0 {
        if err := c.cache.Delete(ctx, keys...); err != nil {
            return err
        }
    }
    
    // Delete the tag set
    return c.cache.Delete(ctx, tagKey)
}

// Usage
func (r *UserRepository) GetWithTags(ctx context.Context, id int) (*domain.User, error) {
    cacheKey := fmt.Sprintf("user:%d", id)
    tags := []string{"users", fmt.Sprintf("user:%d", id)}
    
    var user domain.User
    err := r.cache.Get(ctx, cacheKey, &user)
    if err == nil {
        return &user, nil
    }
    
    // Query database...
    
    // Cache with tags
    r.cache.SetWithTags(ctx, cacheKey, user, 5*time.Minute, tags)
    
    return &user, nil
}
```

### Time-Based Invalidation

```go
// internal/cache/ttl_cache.go
package cache

import (
    "context"
    "time"
)

type TTLCache struct {
    cache Cache
}

func NewTTLCache(cache Cache) *TTLCache {
    return &TTLCache{cache: cache}
}

// Different TTLs based on data type
func (c *TTLCache) GetTTL(dataType string) time.Duration {
    ttls := map[string]time.Duration{
        "user":       5 * time.Minute,
        "session":    15 * time.Minute,
        "static":     24 * time.Hour,
        "hot":        1 * time.Minute,
        "cold":       1 * time.Hour,
    }
    
    if ttl, ok := ttls[dataType]; ok {
        return ttl
    }
    
    return 5 * time.Minute // default
}

func (c *TTLCache) Set(ctx context.Context, key string, value interface{}, dataType string) error {
    ttl := c.GetTTL(dataType)
    return c.cache.Set(ctx, key, value, ttl)
}
```

### Write-Through Cache

```go
// internal/cache/write_through.go
package cache

import (
    "context"
    "time"
)

type WriteThroughCache struct {
    cache Cache
    db    Database
}

func (c *WriteThroughCache) Set(ctx context.Context, key string, value interface{}) error {
    // Write to database first
    if err := c.db.Save(ctx, key, value); err != nil {
        return err
    }
    
    // Then update cache
    return c.cache.Set(ctx, key, value, 5*time.Minute)
}

func (c *WriteThroughCache) Get(ctx context.Context, key string, dest interface{}) error {
    // Try cache first
    err := c.cache.Get(ctx, key, dest)
    if err == nil {
        return nil
    }
    
    // Cache miss - load from database
    if err := c.db.Load(ctx, key, dest); err != nil {
        return err
    }
    
    // Update cache
    c.cache.Set(ctx, key, dest, 5*time.Minute)
    
    return nil
}
```

---

## 5️⃣ Distributed Cache

### Redis Cluster

```go
// internal/cache/redis_cluster.go
package cache

import (
    "context"
    
    "github.com/go-redis/redis/v8"
)

func NewRedisCluster(addrs []string) *redis.ClusterClient {
    return redis.NewClusterClient(&redis.ClusterOptions{
        Addrs: addrs,
    })
}

// Usage
func main() {
    cluster := NewRedisCluster([]string{
        "localhost:7000",
        "localhost:7001",
        "localhost:7002",
    })
    
    ctx := context.Background()
    cluster.Set(ctx, "key", "value", 0)
}
```

### Cache Replication

```go
// internal/cache/replicated_cache.go
package cache

import (
    "context"
    "time"
)

type ReplicatedCache struct {
    primary   Cache
    replicas  []Cache
}

func NewReplicatedCache(primary Cache, replicas ...Cache) *ReplicatedCache {
    return &ReplicatedCache{
        primary:  primary,
        replicas: replicas,
    }
}

func (c *ReplicatedCache) Set(ctx context.Context, key string, value interface{}, ttl time.Duration) error {
    // Write to primary
    if err := c.primary.Set(ctx, key, value, ttl); err != nil {
        return err
    }
    
    // Async write to replicas
    for _, replica := range c.replicas {
        go replica.Set(context.Background(), key, value, ttl)
    }
    
    return nil
}

func (c *ReplicatedCache) Get(ctx context.Context, key string, dest interface{}) error {
    // Try primary first
    err := c.primary.Get(ctx, key, dest)
    if err == nil {
        return nil
    }
    
    // Try replicas
    for _, replica := range c.replicas {
        if err := replica.Get(ctx, key, dest); err == nil {
            // Restore to primary
            go c.primary.Set(context.Background(), key, dest, 5*time.Minute)
            return nil
        }
    }
    
    return err
}
```

---

## 6️⃣ Advanced Patterns

### Multi-Level Cache

```go
// internal/cache/multi_level.go
package cache

import (
    "context"
    "time"
)

type MultiLevelCache struct {
    l1 Cache // In-memory
    l2 Cache // Redis
}

func NewMultiLevelCache(l1, l2 Cache) *MultiLevelCache {
    return &MultiLevelCache{l1: l1, l2: l2}
}

func (c *MultiLevelCache) Get(ctx context.Context, key string, dest interface{}) error {
    // Try L1 (in-memory)
    err := c.l1.Get(ctx, key, dest)
    if err == nil {
        return nil
    }
    
    // Try L2 (Redis)
    err = c.l2.Get(ctx, key, dest)
    if err == nil {
        // Promote to L1
        c.l1.Set(ctx, key, dest, time.Minute)
        return nil
    }
    
    return err
}

func (c *MultiLevelCache) Set(ctx context.Context, key string, value interface{}, ttl time.Duration) error {
    // Set in both levels
    if err := c.l1.Set(ctx, key, value, ttl); err != nil {
        return err
    }
    return c.l2.Set(ctx, key, value, ttl)
}
```

### Cache Stampede Prevention

```go
// internal/cache/stampede_prevention.go
package cache

import (
    "context"
    "sync"
    "time"
)

type StampedeCache struct {
    cache Cache
    locks sync.Map
}

func NewStampedeCache(cache Cache) *StampedeCache {
    return &StampedeCache{cache: cache}
}

func (c *StampedeCache) GetOrLoad(ctx context.Context, key string, loader func() (interface{}, error), ttl time.Duration) (interface{}, error) {
    // Try cache first
    var result interface{}
    err := c.cache.Get(ctx, key, &result)
    if err == nil {
        return result, nil
    }
    
    // Acquire lock for this key
    lock, _ := c.locks.LoadOrStore(key, &sync.Mutex{})
    mutex := lock.(*sync.Mutex)
    
    mutex.Lock()
    defer mutex.Unlock()
    
    // Double-check cache
    err = c.cache.Get(ctx, key, &result)
    if err == nil {
        return result, nil
    }
    
    // Load data
    result, err = loader()
    if err != nil {
        return nil, err
    }
    
    // Store in cache
    c.cache.Set(ctx, key, result, ttl)
    
    return result, nil
}
```

---

## 📋 Caching Checklist

### Junior ✅
- [ ] Simple in-memory map cache
- [ ] Basic TTL support
- [ ] Cache-aside pattern

### Mid ✅
- [ ] Redis integration
- [ ] Cache invalidation
- [ ] Multiple data structures (hash, list, set)
- [ ] Cache key naming strategy

### Senior ✅
- [ ] Multi-level cache
- [ ] Tag-based invalidation
- [ ] Cache stampede prevention
- [ ] Write-through/write-behind

### Expert ✅
- [ ] Distributed caching
- [ ] Cache warming strategies
- [ ] Cache metrics & monitoring
- [ ] Adaptive TTL based on access patterns
