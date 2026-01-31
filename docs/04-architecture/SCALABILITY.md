# 📈 SCALABILITY - Skalabilitas Sistem (Junior → Senior)

Dokumentasi lengkap tentang Scalability dari konsep dasar hingga advanced strategies.

---

## 🎯 Apa itu Scalability?

```
Scalability = Kemampuan sistem untuk handle peningkatan load
              dengan menambah resources

┌─────────────────────────────────────────────────────────────┐
│                     Traffic Growth                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Users    │  100  │  1K  │  10K  │  100K  │  1M  │          │
│           │       │      │       │        │      │          │
│  Response │ 50ms  │ 50ms │ 60ms  │  70ms  │ 100ms│          │
│  Time     │       │      │       │        │      │          │
│           │       │      │       │        │      │          │
│  Strategy │ None  │ Cache│ Scale │ Scale  │ Full │          │
│           │       │      │ Vert. │ Horiz. │ Arch │          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 1️⃣ JUNIOR LEVEL - Scaling Basics

### Vertical vs Horizontal Scaling

```
Vertical Scaling (Scale Up)
━━━━━━━━━━━━━━━━━━━━━━━━━━
Add more power to existing machine

Before:         After:
┌─────────┐     ┌─────────────┐
│ 2 CPU   │ ──► │   16 CPU    │
│ 4GB RAM │     │   64GB RAM  │
│ 100GB   │     │   1TB SSD   │
└─────────┘     └─────────────┘

✅ Pros:
- Simple (no code changes)
- No distributed complexity

❌ Cons:
- Hardware limits
- Single point of failure
- Expensive
- Downtime for upgrade


Horizontal Scaling (Scale Out)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Add more machines

Before:              After:
┌─────────┐         ┌─────────┐
│ Server  │         │ Server  │
└─────────┘         ├─────────┤
                    │ Server  │
                    ├─────────┤
                    │ Server  │
                    └─────────┘

✅ Pros:
- Near infinite scaling
- No single point of failure
- Cost effective (commodity hardware)

❌ Cons:
- Complexity (distributed systems)
- Data consistency challenges
- Network overhead
```

### When to Scale What

| Metric | Symptom | Solution |
|--------|---------|----------|
| CPU > 80% | Slow response | Scale compute |
| Memory > 85% | OOM errors | Scale memory/cache |
| Disk I/O high | Slow queries | Scale storage/cache |
| Network saturated | Timeouts | Scale bandwidth/CDN |
| DB connections maxed | Connection errors | Connection pooling/read replicas |

---

## 2️⃣ MID LEVEL - Load Balancing

### Load Balancer Architecture

```
                         ┌───────────────┐
                         │ Load Balancer │
                         └───────┬───────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
       ┌──────────┐       ┌──────────┐       ┌──────────┐
       │ Server 1 │       │ Server 2 │       │ Server 3 │
       └──────────┘       └──────────┘       └──────────┘
```

### Load Balancing Algorithms

```python
# 1. Round Robin
# Rotate through servers sequentially
servers = ['s1', 's2', 's3']
current = 0

def round_robin():
    global current
    server = servers[current]
    current = (current + 1) % len(servers)
    return server

# s1 → s2 → s3 → s1 → s2 → ...


# 2. Weighted Round Robin
# More traffic to more powerful servers
servers = [
    ('s1', 3),  # 3x weight
    ('s2', 2),  # 2x weight  
    ('s3', 1),  # 1x weight
]
# s1, s1, s1, s2, s2, s3, repeat...


# 3. Least Connections
# Send to server with fewest active connections
connections = {'s1': 10, 's2': 5, 's3': 8}

def least_connections():
    return min(connections, key=connections.get)
# Returns 's2'


# 4. IP Hash
# Same client always goes to same server (session affinity)
def ip_hash(client_ip):
    return servers[hash(client_ip) % len(servers)]


# 5. Least Response Time
# Send to fastest responding server
response_times = {'s1': 50, 's2': 30, 's3': 45}

def least_response_time():
    return min(response_times, key=response_times.get)
```

### Nginx Load Balancer

```nginx
# /etc/nginx/nginx.conf

upstream backend {
    # Least connections algorithm
    least_conn;
    
    server 192.168.1.10:8000 weight=3;
    server 192.168.1.11:8000 weight=2;
    server 192.168.1.12:8000 weight=1;
    
    # Health check
    server 192.168.1.13:8000 backup;  # Only if others fail
}

server {
    listen 80;
    
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # Timeouts
        proxy_connect_timeout 5s;
        proxy_read_timeout 60s;
    }
}
```

### Health Checks

```python
# Application health endpoint
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health_check():
    # Check dependencies
    db_healthy = await check_database()
    cache_healthy = await check_redis()
    
    if db_healthy and cache_healthy:
        return {"status": "healthy"}
    else:
        return {"status": "unhealthy"}, 503
```

```yaml
# Docker Compose health check
services:
  web:
    image: myapp
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

---

## 3️⃣ MID-SENIOR LEVEL - Caching Strategies

### Cache Layers

```
┌─────────────────────────────────────────────────────────────┐
│                      Caching Layers                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Client    → Browser Cache (static files)                   │
│            → CDN (global edge cache)                        │
│                                                              │
│  Server    → Application Cache (in-memory)                  │
│            → Distributed Cache (Redis)                      │
│            → Database Cache (query cache)                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Cache Patterns

```python
# 1. Cache-Aside (Lazy Loading)
# App manages cache, load on miss

async def get_user(user_id: int):
    # Try cache first
    cached = await redis.get(f"user:{user_id}")
    if cached:
        return json.loads(cached)
    
    # Cache miss - load from DB
    user = await db.get_user(user_id)
    
    # Store in cache
    await redis.set(f"user:{user_id}", json.dumps(user), ex=3600)
    
    return user


# 2. Write-Through
# Write to cache and DB simultaneously

async def update_user(user_id: int, data: dict):
    # Update DB
    user = await db.update_user(user_id, data)
    
    # Update cache
    await redis.set(f"user:{user_id}", json.dumps(user), ex=3600)
    
    return user


# 3. Write-Behind (Write-Back)
# Write to cache, async write to DB

async def update_user(user_id: int, data: dict):
    # Write to cache immediately
    await redis.set(f"user:{user_id}", json.dumps(data), ex=3600)
    
    # Queue DB write for later
    await queue.publish("user_updates", {
        "user_id": user_id,
        "data": data
    })
    
    return data


# 4. Read-Through
# Cache handles loading from DB

class CacheableUser:
    @staticmethod
    async def get(user_id: int):
        return await cache.get_or_set(
            key=f"user:{user_id}",
            loader=lambda: db.get_user(user_id),
            ttl=3600
        )
```

### Cache Invalidation

```python
# 1. Time-based (TTL)
await redis.set("key", "value", ex=3600)  # Expires in 1 hour

# 2. Event-based
async def update_user(user_id: int, data: dict):
    await db.update_user(user_id, data)
    await redis.delete(f"user:{user_id}")  # Invalidate cache

# 3. Version-based
async def get_user(user_id: int, version: int):
    cached = await redis.get(f"user:{user_id}:v{version}")
    if cached:
        return json.loads(cached)
    # ...

# 4. Tag-based invalidation
async def invalidate_user_caches(user_id: int):
    # Delete all caches related to user
    keys = await redis.keys(f"*user:{user_id}*")
    if keys:
        await redis.delete(*keys)
```

---

## 4️⃣ SENIOR LEVEL - Database Scaling

### Read Replicas

```
┌─────────────────────────────────────────────────────────────┐
│                    Read Replica Pattern                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│                    ┌──────────────┐                         │
│    Writes ───────► │    Master    │                         │
│                    │   (Primary)  │                         │
│                    └──────┬───────┘                         │
│                           │                                  │
│                    Replication                               │
│                           │                                  │
│              ┌────────────┼────────────┐                    │
│              ▼            ▼            ▼                    │
│       ┌──────────┐ ┌──────────┐ ┌──────────┐               │
│       │ Replica 1│ │ Replica 2│ │ Replica 3│               │
│       └────▲─────┘ └────▲─────┘ └────▲─────┘               │
│            │            │            │                       │
│            └────────────┴────────────┘                       │
│                    Reads                                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

```python
# Django multiple databases
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mydb',
        'HOST': 'master.db.example.com',
    },
    'replica': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mydb',
        'HOST': 'replica.db.example.com',
    }
}

# Database router
class ReadReplicaRouter:
    def db_for_read(self, model, **hints):
        return 'replica'
    
    def db_for_write(self, model, **hints):
        return 'default'

# Usage
users = User.objects.using('replica').all()  # Read from replica
user.save(using='default')  # Write to master
```

### Database Sharding

```
┌─────────────────────────────────────────────────────────────┐
│                      Sharding                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   Shard Key: user_id                                        │
│                                                              │
│   user_id 1-1M     → Shard 1 (DB Server 1)                  │
│   user_id 1M-2M    → Shard 2 (DB Server 2)                  │
│   user_id 2M-3M    → Shard 3 (DB Server 3)                  │
│                                                              │
│   OR Hash-based:                                             │
│   shard = user_id % 3                                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

```python
# Simple sharding logic
class ShardRouter:
    def __init__(self, num_shards: int):
        self.num_shards = num_shards
    
    def get_shard(self, user_id: int) -> str:
        shard_id = user_id % self.num_shards
        return f"shard_{shard_id}"

router = ShardRouter(num_shards=3)

def get_user_db(user_id: int):
    shard = router.get_shard(user_id)
    return databases[shard]

# Usage
db = get_user_db(user_id=12345)
user = db.query(User).filter_by(id=12345).first()
```

### Connection Pooling

```python
# SQLAlchemy connection pool
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql://user:pass@localhost/db",
    pool_size=20,           # Base pool size
    max_overflow=10,        # Extra connections allowed
    pool_timeout=30,        # Wait time for connection
    pool_recycle=1800,      # Recycle connections after 30 min
    pool_pre_ping=True,     # Check connection before use
)

# Django
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mydb',
        'CONN_MAX_AGE': 600,  # Keep connections for 10 minutes
        'OPTIONS': {
            'MAX_CONNS': 20,
        }
    }
}
```

---

## 5️⃣ SENIOR LEVEL - CDN & Static Assets

### CDN Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CDN                                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  User (Asia)                                                 │
│       ↓                                                      │
│  Edge Server (Tokyo)  ←──── Cache Hit ────┐                 │
│       ↓ (Cache Miss)                      │                 │
│  Origin Server (US) ─────────────────────►│                 │
│                                                              │
│  Benefits:                                                   │
│  - Lower latency (closer to user)                           │
│  - Reduce origin load                                       │
│  - DDoS protection                                          │
│  - SSL termination                                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### CDN Configuration

```python
# Django Static Files with CDN
# settings.py

# Use S3 + CloudFront
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'
AWS_S3_CUSTOM_DOMAIN = 'd123abc.cloudfront.net'
STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'

# Cache headers
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=31536000',  # 1 year
}
```

```nginx
# Nginx caching
location /static/ {
    alias /var/www/static/;
    expires 1y;
    add_header Cache-Control "public, immutable";
    add_header Vary Accept-Encoding;
    gzip_static on;
}

location /api/ {
    proxy_pass http://backend;
    # No caching for API
    add_header Cache-Control "no-cache, no-store, must-revalidate";
}
```

---

## 6️⃣ SENIOR LEVEL - Async Processing

### Background Jobs

```python
# Celery for background tasks
from celery import Celery

app = Celery('tasks', broker='redis://localhost:6379')

@app.task
def process_video(video_id: int):
    """Heavy task - runs in background"""
    video = get_video(video_id)
    transcode(video)
    generate_thumbnails(video)
    update_status(video_id, 'ready')

# API endpoint
@router.post("/videos/")
async def upload_video(file: UploadFile):
    video = save_video(file)
    
    # Don't wait - process in background
    process_video.delay(video.id)
    
    return {"video_id": video.id, "status": "processing"}
```

### Rate Limiting

```python
# Token Bucket Algorithm
import time
from dataclasses import dataclass

@dataclass
class TokenBucket:
    capacity: int
    refill_rate: float  # tokens per second
    tokens: float = None
    last_refill: float = None
    
    def __post_init__(self):
        self.tokens = self.capacity
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def _refill(self):
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.refill_rate
        )
        self.last_refill = now

# Usage
bucket = TokenBucket(capacity=100, refill_rate=10)  # 100 requests, refill 10/sec

if bucket.consume():
    process_request()
else:
    return {"error": "Rate limit exceeded"}, 429
```

```python
# Redis-based rate limiting
import redis
import time

r = redis.Redis()

def is_rate_limited(user_id: str, limit: int = 100, window: int = 60):
    """
    Sliding window rate limiter
    limit: max requests
    window: time window in seconds
    """
    key = f"ratelimit:{user_id}"
    now = time.time()
    
    pipe = r.pipeline()
    
    # Remove old entries
    pipe.zremrangebyscore(key, 0, now - window)
    
    # Count requests in window
    pipe.zcard(key)
    
    # Add current request
    pipe.zadd(key, {str(now): now})
    
    # Set expiry
    pipe.expire(key, window)
    
    results = pipe.execute()
    request_count = results[1]
    
    return request_count >= limit

# Usage
if is_rate_limited(user_id):
    return {"error": "Too many requests"}, 429
```

---

## 7️⃣ EXPERT LEVEL - Performance Optimization

### Profiling

```python
# Python cProfile
import cProfile
import pstats

def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Code to profile
    result = expensive_function()
    
    profiler.disable()
    
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # Top 10 functions
    
    return result

# Django Silk for request profiling
# settings.py
INSTALLED_APPS += ['silk']
MIDDLEWARE += ['silk.middleware.SilkyMiddleware']
```

### Database Query Optimization

```python
# Django ORM optimization

# ❌ Bad: N+1 query problem
users = User.objects.all()
for user in users:
    print(user.profile.bio)  # Extra query per user!

# ✅ Good: Use select_related (FK/OneToOne)
users = User.objects.select_related('profile').all()
for user in users:
    print(user.profile.bio)  # No extra queries

# ✅ Good: Use prefetch_related (ManyToMany/Reverse FK)
users = User.objects.prefetch_related('orders').all()
for user in users:
    print(len(user.orders.all()))  # No extra queries

# ✅ Good: Only fetch needed fields
users = User.objects.only('id', 'name').all()
users = User.objects.values('id', 'name')  # Returns dicts

# ✅ Good: Use indexes
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, db_index=True)
    created_at = models.DateTimeField(db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['-created_at']),
        ]
```

### Pagination

```python
# Offset pagination (simple but slow for large offsets)
# Page 1000 still scans 999,000 rows first
users = User.objects.all()[offset:offset + limit]

# Cursor pagination (efficient for large datasets)
# Uses indexed field, no offset scanning
class CursorPaginator:
    def get_page(self, queryset, cursor: str = None, limit: int = 20):
        if cursor:
            # Decode cursor (e.g., base64 encoded ID)
            last_id = decode_cursor(cursor)
            queryset = queryset.filter(id__gt=last_id)
        
        items = list(queryset.order_by('id')[:limit + 1])
        
        has_next = len(items) > limit
        items = items[:limit]
        
        next_cursor = None
        if has_next and items:
            next_cursor = encode_cursor(items[-1].id)
        
        return {
            'items': items,
            'next_cursor': next_cursor
        }
```

---

## 📊 Quick Reference

### Scaling Strategies by Layer

| Layer | Strategy |
|-------|----------|
| **DNS** | Geo DNS, Round Robin |
| **CDN** | Edge caching, Static assets |
| **Load Balancer** | Round Robin, Least Conn |
| **Application** | Horizontal scaling, Containers |
| **Cache** | Redis Cluster, Memcached |
| **Database** | Read replicas, Sharding |
| **Storage** | Object storage (S3), Distributed FS |

### Performance Targets

| Metric | Good | Great | Excellent |
|--------|------|-------|-----------|
| Response Time (P50) | < 200ms | < 100ms | < 50ms |
| Response Time (P99) | < 1s | < 500ms | < 200ms |
| Availability | 99.9% | 99.95% | 99.99% |
| Error Rate | < 1% | < 0.1% | < 0.01% |

### Scaling Checklist

```
□ Caching (Redis, CDN)
□ Load balancing
□ Database optimization (indexes, queries)
□ Read replicas
□ Connection pooling
□ Async processing (Celery)
□ Rate limiting
□ Compression (gzip)
□ Monitoring & alerting
□ Auto-scaling
```

---

## 💡 Summary

| Level | Focus |
|-------|-------|
| **Junior** | Vertical vs Horizontal |
| **Mid** | Load balancing, basic caching |
| **Mid-Senior** | Cache patterns, CDN |
| **Senior** | DB scaling, async processing |
| **Expert** | Profiling, optimization |

**Scaling Order:**
```
1. Optimize code (algorithms, queries)
2. Add caching (Redis)
3. Use CDN for static files
4. Add load balancer + more servers
5. Database read replicas
6. Sharding (if needed)
7. Microservices (if needed)
```

**Golden Rules:**
- ✅ Measure before optimizing
- ✅ Cache aggressively
- ✅ Use async for heavy tasks
- ✅ Scale horizontally when possible
- ✅ Database is usually the bottleneck
- ✅ Monitor everything
- ✅ Plan for failure
- ✅ Start simple, scale gradually
