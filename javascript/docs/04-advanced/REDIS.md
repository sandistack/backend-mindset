# ⚡ REDIS - Caching & Session di Express (Junior → Senior)

Dokumentasi lengkap tentang Redis untuk caching, session, dan queue di Express.js.

---

## 🎯 Apa itu Redis?

```
Redis = Remote Dictionary Server

Use Cases:
✅ Caching (API responses, database queries)
✅ Session storage
✅ Rate limiting
✅ Real-time leaderboards
✅ Pub/Sub messaging
✅ Queue management
```

---

## 1️⃣ JUNIOR LEVEL - Setup Redis

### Installation

```bash
# Install Redis client
npm install ioredis

# Or using redis package
npm install redis
```

### Redis Connection

```javascript
// src/lib/redis.js
const Redis = require('ioredis');

const redis = new Redis({
  host: process.env.REDIS_HOST || 'localhost',
  port: process.env.REDIS_PORT || 6379,
  password: process.env.REDIS_PASSWORD || undefined,
  db: process.env.REDIS_DB || 0,
  retryDelayOnFailover: 100,
  maxRetriesPerRequest: 3
});

redis.on('connect', () => {
  console.log('✅ Redis connected');
});

redis.on('error', (err) => {
  console.error('❌ Redis error:', err);
});

module.exports = redis;
```

### Basic Operations

```javascript
const redis = require('./lib/redis');

// String operations
await redis.set('key', 'value');
await redis.set('key', 'value', 'EX', 3600); // Expires in 1 hour
const value = await redis.get('key');
await redis.del('key');

// Check if exists
const exists = await redis.exists('key'); // 1 or 0

// Increment/Decrement
await redis.incr('counter');
await redis.incrby('counter', 5);
await redis.decr('counter');

// TTL
await redis.expire('key', 3600); // Set expiry
const ttl = await redis.ttl('key'); // Get remaining time
```

---

## 2️⃣ MID LEVEL - Caching Patterns

### Cache Service

```javascript
// src/services/cache.service.js
const redis = require('../lib/redis');

class CacheService {
  constructor(prefix = 'cache') {
    this.prefix = prefix;
    this.defaultTTL = 3600; // 1 hour
  }

  getKey(key) {
    return `${this.prefix}:${key}`;
  }

  async get(key) {
    const data = await redis.get(this.getKey(key));
    return data ? JSON.parse(data) : null;
  }

  async set(key, value, ttl = this.defaultTTL) {
    const data = JSON.stringify(value);
    if (ttl) {
      await redis.setex(this.getKey(key), ttl, data);
    } else {
      await redis.set(this.getKey(key), data);
    }
  }

  async del(key) {
    await redis.del(this.getKey(key));
  }

  async delPattern(pattern) {
    const keys = await redis.keys(this.getKey(pattern));
    if (keys.length > 0) {
      await redis.del(...keys);
    }
  }

  async exists(key) {
    return await redis.exists(this.getKey(key));
  }

  // Cache-aside pattern
  async getOrSet(key, fetchFn, ttl = this.defaultTTL) {
    const cached = await this.get(key);
    
    if (cached !== null) {
      return cached;
    }

    const data = await fetchFn();
    await this.set(key, data, ttl);
    return data;
  }

  async invalidate(key) {
    await this.del(key);
  }

  async invalidatePattern(pattern) {
    await this.delPattern(pattern);
  }

  async flush() {
    const keys = await redis.keys(`${this.prefix}:*`);
    if (keys.length > 0) {
      await redis.del(...keys);
    }
  }
}

module.exports = new CacheService();
```

### Using Cache in Service

```javascript
// src/services/user.service.js
const prisma = require('../lib/prisma');
const cacheService = require('./cache.service');

class UserService {
  async findById(id) {
    const cacheKey = `user:${id}`;
    
    // Try cache first
    return cacheService.getOrSet(cacheKey, async () => {
      return prisma.user.findUnique({
        where: { id },
        select: {
          id: true,
          name: true,
          email: true,
          role: true
        }
      });
    }, 1800); // 30 minutes
  }

  async findAll(params) {
    const { page = 1, limit = 10 } = params;
    const cacheKey = `users:page:${page}:limit:${limit}`;
    
    return cacheService.getOrSet(cacheKey, async () => {
      const [users, total] = await Promise.all([
        prisma.user.findMany({
          skip: (page - 1) * limit,
          take: limit,
          orderBy: { createdAt: 'desc' }
        }),
        prisma.user.count()
      ]);

      return {
        data: users,
        pagination: {
          page,
          limit,
          total,
          totalPages: Math.ceil(total / limit)
        }
      };
    }, 300); // 5 minutes
  }

  async update(id, data) {
    const user = await prisma.user.update({
      where: { id },
      data
    });

    // Invalidate cache
    await cacheService.del(`user:${id}`);
    await cacheService.delPattern('users:*'); // Invalidate list cache

    return user;
  }

  async delete(id) {
    await prisma.user.delete({ where: { id } });
    
    // Invalidate cache
    await cacheService.del(`user:${id}`);
    await cacheService.delPattern('users:*');
  }
}

module.exports = new UserService();
```

---

## 3️⃣ MID LEVEL - Cache Middleware

### Response Cache Middleware

```javascript
// src/middlewares/cache.middleware.js
const cacheService = require('../services/cache.service');

const cacheMiddleware = (ttl = 300, keyGenerator = null) => {
  return async (req, res, next) => {
    // Only cache GET requests
    if (req.method !== 'GET') {
      return next();
    }

    // Generate cache key
    const cacheKey = keyGenerator 
      ? keyGenerator(req)
      : `response:${req.originalUrl}`;

    // Check cache
    const cached = await cacheService.get(cacheKey);
    
    if (cached) {
      return res.json(cached);
    }

    // Store original json method
    const originalJson = res.json.bind(res);

    // Override json method to cache response
    res.json = async (data) => {
      // Only cache successful responses
      if (res.statusCode >= 200 && res.statusCode < 300) {
        await cacheService.set(cacheKey, data, ttl);
      }
      return originalJson(data);
    };

    next();
  };
};

// Clear cache on mutation
const clearCache = (patterns) => {
  return async (req, res, next) => {
    const originalJson = res.json.bind(res);

    res.json = async (data) => {
      // Clear cache after successful mutation
      if (res.statusCode >= 200 && res.statusCode < 300) {
        for (const pattern of patterns) {
          await cacheService.delPattern(pattern);
        }
      }
      return originalJson(data);
    };

    next();
  };
};

module.exports = { cacheMiddleware, clearCache };
```

### Using Cache Middleware

```javascript
// src/routes/user.routes.js
const { cacheMiddleware, clearCache } = require('../middlewares/cache.middleware');

// Cache GET requests
router.get('/', cacheMiddleware(300), userController.getUsers);
router.get('/:id', cacheMiddleware(600), userController.getUser);

// Clear cache on mutations
router.post('/', clearCache(['users:*']), userController.createUser);
router.put('/:id', clearCache(['users:*', 'user:*']), userController.updateUser);
router.delete('/:id', clearCache(['users:*', 'user:*']), userController.deleteUser);
```

---

## 4️⃣ SENIOR LEVEL - Session Storage

### Express Session with Redis

```bash
npm install express-session connect-redis
```

```javascript
// src/app.js
const session = require('express-session');
const RedisStore = require('connect-redis').default;
const redis = require('./lib/redis');

app.use(session({
  store: new RedisStore({ client: redis }),
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: process.env.NODE_ENV === 'production',
    httpOnly: true,
    maxAge: 24 * 60 * 60 * 1000, // 24 hours
    sameSite: 'strict'
  },
  name: 'sessionId' // Custom cookie name
}));

// Usage in routes
app.post('/login', (req, res) => {
  // Store user in session
  req.session.userId = user.id;
  req.session.role = user.role;
  res.json({ message: 'Logged in' });
});

app.get('/profile', (req, res) => {
  if (!req.session.userId) {
    return res.status(401).json({ message: 'Not authenticated' });
  }
  // Use req.session.userId
});

app.post('/logout', (req, res) => {
  req.session.destroy((err) => {
    if (err) {
      return res.status(500).json({ message: 'Logout failed' });
    }
    res.clearCookie('sessionId');
    res.json({ message: 'Logged out' });
  });
});
```

---

## 5️⃣ SENIOR LEVEL - Rate Limiting with Redis

### Sliding Window Rate Limiter

```javascript
// src/services/rateLimiter.service.js
const redis = require('../lib/redis');

class RateLimiter {
  constructor(options = {}) {
    this.windowMs = options.windowMs || 60000; // 1 minute
    this.max = options.max || 100;
    this.prefix = options.prefix || 'ratelimit';
  }

  async consume(key) {
    const redisKey = `${this.prefix}:${key}`;
    const now = Date.now();
    const windowStart = now - this.windowMs;

    // Use Redis transaction
    const pipeline = redis.pipeline();
    
    // Remove old entries
    pipeline.zremrangebyscore(redisKey, 0, windowStart);
    
    // Add current request
    pipeline.zadd(redisKey, now, `${now}-${Math.random()}`);
    
    // Count requests in window
    pipeline.zcard(redisKey);
    
    // Set expiry
    pipeline.expire(redisKey, Math.ceil(this.windowMs / 1000));

    const results = await pipeline.exec();
    const requestCount = results[2][1];

    const remaining = Math.max(0, this.max - requestCount);
    const resetTime = now + this.windowMs;

    return {
      allowed: requestCount <= this.max,
      remaining,
      resetTime,
      total: this.max
    };
  }
}

module.exports = RateLimiter;
```

### Rate Limit Middleware

```javascript
// src/middlewares/rateLimiter.middleware.js
const RateLimiter = require('../services/rateLimiter.service');
const ApiError = require('../utils/ApiError');

const createRateLimiter = (options = {}) => {
  const limiter = new RateLimiter(options);
  const keyGenerator = options.keyGenerator || ((req) => req.ip);

  return async (req, res, next) => {
    const key = keyGenerator(req);
    const result = await limiter.consume(key);

    // Set rate limit headers
    res.setHeader('X-RateLimit-Limit', result.total);
    res.setHeader('X-RateLimit-Remaining', result.remaining);
    res.setHeader('X-RateLimit-Reset', result.resetTime);

    if (!result.allowed) {
      return next(
        ApiError.tooManyRequests('Rate limit exceeded. Try again later.')
      );
    }

    next();
  };
};

// Different limiters
const generalLimiter = createRateLimiter({
  windowMs: 60 * 1000,
  max: 100
});

const authLimiter = createRateLimiter({
  windowMs: 15 * 60 * 1000,
  max: 5,
  prefix: 'auth'
});

const apiLimiter = createRateLimiter({
  windowMs: 60 * 1000,
  max: 60,
  keyGenerator: (req) => req.user?.id || req.ip
});

module.exports = { createRateLimiter, generalLimiter, authLimiter, apiLimiter };
```

---

## 6️⃣ SENIOR LEVEL - Hash & List Operations

### Hash Operations (Objects)

```javascript
// Store object as hash
await redis.hset('user:123', {
  name: 'John',
  email: 'john@example.com',
  role: 'USER'
});

// Get all fields
const user = await redis.hgetall('user:123');
// { name: 'John', email: 'john@example.com', role: 'USER' }

// Get specific field
const name = await redis.hget('user:123', 'name');

// Update field
await redis.hset('user:123', 'name', 'John Doe');

// Delete field
await redis.hdel('user:123', 'role');

// Check field exists
const exists = await redis.hexists('user:123', 'name');

// Increment number field
await redis.hincrby('user:123', 'loginCount', 1);
```

### List Operations (Queues)

```javascript
// Add to list (right/left)
await redis.rpush('queue:emails', JSON.stringify({ to: 'user@example.com' }));
await redis.lpush('queue:emails', JSON.stringify({ to: 'urgent@example.com' }));

// Get from list (blocking pop)
const item = await redis.brpop('queue:emails', 5); // 5 second timeout

// Get list length
const length = await redis.llen('queue:emails');

// Get range
const items = await redis.lrange('queue:emails', 0, -1); // All items

// Trim list (keep last 100)
await redis.ltrim('queue:emails', -100, -1);
```

### Set Operations

```javascript
// Add to set
await redis.sadd('online:users', 'user:123', 'user:456');

// Remove from set
await redis.srem('online:users', 'user:123');

// Check membership
const isMember = await redis.sismember('online:users', 'user:123');

// Get all members
const members = await redis.smembers('online:users');

// Count members
const count = await redis.scard('online:users');

// Random member
const random = await redis.srandmember('online:users');
```

---

## 7️⃣ EXPERT LEVEL - Pub/Sub

### Publisher

```javascript
// src/services/pubsub.service.js
const Redis = require('ioredis');

const publisher = new Redis(process.env.REDIS_URL);
const subscriber = new Redis(process.env.REDIS_URL);

// Publish event
const publish = async (channel, message) => {
  await publisher.publish(channel, JSON.stringify(message));
};

// Subscribe to channel
const subscribe = (channel, callback) => {
  subscriber.subscribe(channel, (err) => {
    if (err) {
      console.error('Subscribe error:', err);
      return;
    }
    console.log(`Subscribed to ${channel}`);
  });

  subscriber.on('message', (ch, message) => {
    if (ch === channel) {
      callback(JSON.parse(message));
    }
  });
};

module.exports = { publish, subscribe, publisher, subscriber };
```

### Real-time Notifications

```javascript
// src/events/notifications.js
const { publish, subscribe } = require('../services/pubsub.service');

// Publish notification
const notifyUser = async (userId, notification) => {
  await publish(`notifications:${userId}`, {
    type: notification.type,
    title: notification.title,
    message: notification.message,
    timestamp: Date.now()
  });
};

// Subscribe to notifications (for WebSocket integration)
const subscribeToUserNotifications = (userId, callback) => {
  subscribe(`notifications:${userId}`, callback);
};

module.exports = { notifyUser, subscribeToUserNotifications };
```

### Event-Driven Architecture

```javascript
// src/events/handlers.js
const { subscribe } = require('../services/pubsub.service');
const emailService = require('../services/email.service');

// Event handlers
subscribe('user:created', async (data) => {
  console.log('User created:', data);
  await emailService.sendWelcomeEmail(data.email);
});

subscribe('order:completed', async (data) => {
  console.log('Order completed:', data);
  await emailService.sendOrderConfirmation(data);
});

// Usage
const { publish } = require('../services/pubsub.service');

// In user service after creating user
await publish('user:created', { id: user.id, email: user.email });
```

---

## 8️⃣ EXPERT LEVEL - Job Queue with BullMQ

```bash
npm install bullmq
```

### Queue Setup

```javascript
// src/queues/email.queue.js
const { Queue, Worker } = require('bullmq');
const redis = require('../lib/redis');

const connection = {
  host: process.env.REDIS_HOST,
  port: process.env.REDIS_PORT
};

// Create queue
const emailQueue = new Queue('email', { connection });

// Add job
const addEmailJob = async (data, options = {}) => {
  return emailQueue.add('send-email', data, {
    attempts: 3,
    backoff: { type: 'exponential', delay: 1000 },
    ...options
  });
};

// Worker
const emailWorker = new Worker('email', async (job) => {
  const { to, subject, body } = job.data;
  
  console.log(`Sending email to ${to}`);
  
  // Send email logic
  await sendEmail(to, subject, body);
  
  return { sent: true, to };
}, { connection });

emailWorker.on('completed', (job, result) => {
  console.log(`Email job ${job.id} completed:`, result);
});

emailWorker.on('failed', (job, err) => {
  console.error(`Email job ${job.id} failed:`, err);
});

module.exports = { emailQueue, addEmailJob, emailWorker };
```

### Scheduled Jobs

```javascript
// Delayed job
await emailQueue.add('send-reminder', 
  { userId: '123', message: 'Don\'t forget!' },
  { delay: 24 * 60 * 60 * 1000 } // 24 hours
);

// Repeating job
await emailQueue.add('daily-digest',
  { type: 'digest' },
  { 
    repeat: { 
      cron: '0 9 * * *' // Every day at 9 AM
    }
  }
);
```

---

## 📊 Redis Commands Cheat Sheet

### String Commands

| Command | Description |
|---------|-------------|
| `SET key value` | Set value |
| `GET key` | Get value |
| `SETEX key ttl value` | Set with expiry |
| `INCR key` | Increment |
| `DEL key` | Delete |
| `EXISTS key` | Check exists |
| `TTL key` | Get remaining TTL |

### Hash Commands

| Command | Description |
|---------|-------------|
| `HSET key field value` | Set field |
| `HGET key field` | Get field |
| `HGETALL key` | Get all fields |
| `HDEL key field` | Delete field |
| `HINCRBY key field n` | Increment field |

### List Commands

| Command | Description |
|---------|-------------|
| `LPUSH key value` | Add to left |
| `RPUSH key value` | Add to right |
| `LPOP key` | Remove from left |
| `RPOP key` | Remove from right |
| `LRANGE key 0 -1` | Get all |
| `LLEN key` | Get length |

---

## 💡 Summary

| Level | Focus |
|-------|-------|
| **Junior** | Basic operations, connection |
| **Mid** | Caching patterns, cache service |
| **Senior** | Session, rate limiting, data structures |
| **Expert** | Pub/Sub, job queues |

**Best Practices:**
- ✅ Use connection pooling
- ✅ Set appropriate TTL
- ✅ Use pipeline for multiple operations
- ✅ Handle connection errors
- ✅ Use JSON serialization
- ✅ Namespace keys with prefix
- ❌ Don't store large objects
- ❌ Don't use KEYS in production (use SCAN)
- ❌ Don't forget to handle cache invalidation
