# 🔒 SECURITY - Keamanan di Express (Junior → Senior)

Dokumentasi lengkap tentang security best practices di Express.js.

---

## 🎯 Security Layers

```
Security Defense in Depth:
┌──────────────────────────┐
│     Rate Limiting        │ → Prevent brute force
├──────────────────────────┤
│     Input Validation     │ → Prevent injection
├──────────────────────────┤
│     Authentication       │ → Verify identity
├──────────────────────────┤
│     Authorization        │ → Check permissions
├──────────────────────────┤
│     Data Encryption      │ → Protect data
└──────────────────────────┘
```

---

## 1️⃣ JUNIOR LEVEL - Basic Security Setup

### Essential Security Packages

```bash
npm install helmet cors express-rate-limit
```

### Helmet - Security Headers

```javascript
// src/app.js
const express = require('express');
const helmet = require('helmet');

const app = express();

// Basic helmet (includes many security headers)
app.use(helmet());

// Or with custom config
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
    },
  },
  crossOriginEmbedderPolicy: false,
}));
```

### Headers Set by Helmet

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 0 (disabled, CSP is better)
Strict-Transport-Security: max-age=15552000; includeSubDomains
Content-Security-Policy: ...
X-Download-Options: noopen
X-Permitted-Cross-Domain-Policies: none
Referrer-Policy: no-referrer
```

### CORS Configuration

```javascript
const cors = require('cors');

// Simple - allow specific origins
app.use(cors({
  origin: ['http://localhost:3000', 'https://myapp.com'],
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true,
  maxAge: 86400 // 24 hours
}));

// Dynamic origin
app.use(cors({
  origin: (origin, callback) => {
    const allowedOrigins = process.env.CORS_ORIGINS?.split(',') || [];
    
    // Allow requests with no origin (mobile apps, curl)
    if (!origin) return callback(null, true);
    
    if (allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true
}));
```

---

## 2️⃣ MID LEVEL - Input Validation & Sanitization

### Validation with Joi

```javascript
// src/validations/user.validation.js
const Joi = require('joi');

const createUser = Joi.object({
  name: Joi.string()
    .min(2)
    .max(100)
    .pattern(/^[a-zA-Z\s]+$/)
    .required()
    .messages({
      'string.pattern.base': 'Name can only contain letters and spaces'
    }),
  
  email: Joi.string()
    .email({ tlds: { allow: false } })
    .lowercase()
    .required(),
  
  password: Joi.string()
    .min(8)
    .max(128)
    .pattern(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])/)
    .required()
    .messages({
      'string.pattern.base': 'Password must contain uppercase, lowercase, number and special character'
    }),
  
  age: Joi.number()
    .integer()
    .min(13)
    .max(120)
    .optional()
});

// Sanitize options
const options = {
  abortEarly: false,
  stripUnknown: true, // Remove unknown fields
  convert: true       // Type coercion
};
```

### HTML Sanitization (XSS Prevention)

```bash
npm install xss-clean sanitize-html
```

```javascript
const xss = require('xss-clean');
const sanitizeHtml = require('sanitize-html');

// Global XSS protection
app.use(xss());

// Custom sanitizer for rich text
const sanitizeContent = (dirty) => {
  return sanitizeHtml(dirty, {
    allowedTags: ['b', 'i', 'em', 'strong', 'a', 'p', 'br', 'ul', 'ol', 'li'],
    allowedAttributes: {
      'a': ['href', 'target']
    },
    allowedSchemes: ['http', 'https', 'mailto'],
    transformTags: {
      'a': (tagName, attribs) => {
        return {
          tagName: 'a',
          attribs: {
            ...attribs,
            target: '_blank',
            rel: 'noopener noreferrer'
          }
        };
      }
    }
  });
};

// Usage
const cleanContent = sanitizeContent('<script>alert("xss")</script><p>Hello</p>');
// Result: <p>Hello</p>
```

### NoSQL Injection Prevention

```bash
npm install express-mongo-sanitize
```

```javascript
const mongoSanitize = require('express-mongo-sanitize');

// Remove $ and . from req.body, req.query, req.params
app.use(mongoSanitize());

// Or with replacement
app.use(mongoSanitize({
  replaceWith: '_'
}));
```

### SQL Injection Prevention

```javascript
// ❌ BAD - SQL Injection vulnerable
const query = `SELECT * FROM users WHERE email = '${email}'`;

// ✅ GOOD - Parameterized query (Prisma handles this)
const user = await prisma.user.findUnique({
  where: { email }
});

// ✅ GOOD - Raw query with parameters
const users = await prisma.$queryRaw`
  SELECT * FROM users WHERE email = ${email}
`;
```

---

## 3️⃣ MID LEVEL - Rate Limiting

### Basic Rate Limiting

```javascript
const rateLimit = require('express-rate-limit');

// General limiter
const generalLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // 100 requests per window
  message: {
    success: false,
    message: 'Too many requests, please try again later'
  },
  standardHeaders: true,
  legacyHeaders: false,
  skipSuccessfulRequests: false
});

// Apply to all routes
app.use('/api', generalLimiter);
```

### Different Limiters for Different Routes

```javascript
// Strict limiter for auth
const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5,
  message: { success: false, message: 'Too many login attempts' },
  skipSuccessfulRequests: true
});

// API limiter
const apiLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 60,
  keyGenerator: (req) => req.user?.id || req.ip
});

// Expensive operations
const uploadLimiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1 hour
  max: 10,
  message: { success: false, message: 'Upload limit exceeded' }
});

// Apply
app.use('/api/auth/login', authLimiter);
app.use('/api/auth/register', authLimiter);
app.use('/api', apiLimiter);
app.use('/api/upload', uploadLimiter);
```

### Redis-Based Rate Limiting (Production)

```bash
npm install rate-limit-redis ioredis
```

```javascript
const rateLimit = require('express-rate-limit');
const RedisStore = require('rate-limit-redis');
const Redis = require('ioredis');

const redis = new Redis(process.env.REDIS_URL);

const limiter = rateLimit({
  store: new RedisStore({
    sendCommand: (...args) => redis.call(...args)
  }),
  windowMs: 15 * 60 * 1000,
  max: 100,
  standardHeaders: true,
  legacyHeaders: false
});

app.use('/api', limiter);
```

---

## 4️⃣ SENIOR LEVEL - Advanced Security

### Request Validation Middleware

```javascript
// src/middlewares/security.middleware.js
const ApiError = require('../utils/ApiError');

// Validate Content-Type
const validateContentType = (req, res, next) => {
  if (['POST', 'PUT', 'PATCH'].includes(req.method)) {
    const contentType = req.headers['content-type'];
    
    if (!contentType || !contentType.includes('application/json')) {
      return next(ApiError.badRequest('Content-Type must be application/json'));
    }
  }
  next();
};

// Limit request body size
const limitBodySize = (maxSize = '10kb') => {
  return express.json({ limit: maxSize });
};

// Prevent parameter pollution
const hpp = require('hpp');
app.use(hpp({
  whitelist: ['sort', 'filter', 'fields', 'page', 'limit']
}));
```

### Secure Headers Middleware

```javascript
// src/middlewares/secureHeaders.middleware.js
const secureHeaders = (req, res, next) => {
  // Remove server info
  res.removeHeader('X-Powered-By');
  
  // Additional security headers
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-XSS-Protection', '1; mode=block');
  res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
  res.setHeader('Permissions-Policy', 'geolocation=(), microphone=(), camera=()');
  
  // HSTS (only in production)
  if (process.env.NODE_ENV === 'production') {
    res.setHeader(
      'Strict-Transport-Security',
      'max-age=31536000; includeSubDomains; preload'
    );
  }
  
  next();
};

module.exports = secureHeaders;
```

### API Key Authentication

```javascript
// src/middlewares/apiKey.middleware.js
const prisma = require('../lib/prisma');
const ApiError = require('../utils/ApiError');

const validateApiKey = async (req, res, next) => {
  const apiKey = req.headers['x-api-key'];
  
  if (!apiKey) {
    return next(ApiError.unauthorized('API key required'));
  }
  
  const key = await prisma.apiKey.findUnique({
    where: { key: apiKey },
    include: { user: true }
  });
  
  if (!key || !key.isActive) {
    return next(ApiError.unauthorized('Invalid API key'));
  }
  
  if (key.expiresAt && key.expiresAt < new Date()) {
    return next(ApiError.unauthorized('API key expired'));
  }
  
  // Update last used
  await prisma.apiKey.update({
    where: { id: key.id },
    data: { lastUsedAt: new Date() }
  });
  
  req.apiKey = key;
  req.user = key.user;
  
  next();
};

module.exports = validateApiKey;
```

---

## 5️⃣ SENIOR LEVEL - CSRF Protection

### CSRF with csurf

```bash
npm install csurf cookie-parser
```

```javascript
const csrf = require('csurf');
const cookieParser = require('cookie-parser');

app.use(cookieParser());
app.use(csrf({
  cookie: {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'strict'
  }
}));

// Send token to client
app.get('/api/csrf-token', (req, res) => {
  res.json({ csrfToken: req.csrfToken() });
});

// Error handler for CSRF
app.use((err, req, res, next) => {
  if (err.code === 'EBADCSRFTOKEN') {
    return res.status(403).json({
      success: false,
      message: 'Invalid CSRF token'
    });
  }
  next(err);
});
```

### Double Submit Cookie Pattern

```javascript
// src/middlewares/csrf.middleware.js
const crypto = require('crypto');

const generateToken = () => crypto.randomBytes(32).toString('hex');

const csrfProtection = (req, res, next) => {
  // Skip for GET, HEAD, OPTIONS
  if (['GET', 'HEAD', 'OPTIONS'].includes(req.method)) {
    return next();
  }
  
  const cookieToken = req.cookies['csrf-token'];
  const headerToken = req.headers['x-csrf-token'];
  
  if (!cookieToken || !headerToken || cookieToken !== headerToken) {
    return res.status(403).json({
      success: false,
      message: 'Invalid CSRF token'
    });
  }
  
  next();
};

// Set CSRF cookie
const setCsrfCookie = (req, res, next) => {
  if (!req.cookies['csrf-token']) {
    const token = generateToken();
    res.cookie('csrf-token', token, {
      httpOnly: false, // Must be accessible by JS
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict'
    });
  }
  next();
};

module.exports = { csrfProtection, setCsrfCookie };
```

---

## 6️⃣ EXPERT LEVEL - Audit Logging

### Audit Log Schema

```prisma
// prisma/schema.prisma
model AuditLog {
  id         String   @id @default(uuid())
  action     String   // CREATE, UPDATE, DELETE, LOGIN, etc.
  entity     String   // User, Post, Order
  entityId   String?
  userId     String?
  user       User?    @relation(fields: [userId], references: [id])
  ipAddress  String?
  userAgent  String?
  oldData    Json?
  newData    Json?
  metadata   Json?
  createdAt  DateTime @default(now())

  @@index([action])
  @@index([entity])
  @@index([userId])
  @@index([createdAt])
}
```

### Audit Service

```javascript
// src/services/audit.service.js
const prisma = require('../lib/prisma');

class AuditService {
  async log(data) {
    const {
      action,
      entity,
      entityId,
      userId,
      ipAddress,
      userAgent,
      oldData,
      newData,
      metadata
    } = data;

    return prisma.auditLog.create({
      data: {
        action,
        entity,
        entityId,
        userId,
        ipAddress,
        userAgent,
        oldData: oldData ? JSON.parse(JSON.stringify(oldData)) : null,
        newData: newData ? JSON.parse(JSON.stringify(newData)) : null,
        metadata
      }
    });
  }

  async logCreate(entity, entityId, newData, req) {
    return this.log({
      action: 'CREATE',
      entity,
      entityId,
      userId: req.user?.sub,
      ipAddress: req.ip,
      userAgent: req.headers['user-agent'],
      newData
    });
  }

  async logUpdate(entity, entityId, oldData, newData, req) {
    return this.log({
      action: 'UPDATE',
      entity,
      entityId,
      userId: req.user?.sub,
      ipAddress: req.ip,
      userAgent: req.headers['user-agent'],
      oldData,
      newData
    });
  }

  async logDelete(entity, entityId, oldData, req) {
    return this.log({
      action: 'DELETE',
      entity,
      entityId,
      userId: req.user?.sub,
      ipAddress: req.ip,
      userAgent: req.headers['user-agent'],
      oldData
    });
  }

  async logAuth(action, userId, req, metadata = {}) {
    return this.log({
      action,
      entity: 'Auth',
      userId,
      ipAddress: req.ip,
      userAgent: req.headers['user-agent'],
      metadata
    });
  }
}

module.exports = new AuditService();
```

### Usage in Service

```javascript
// src/services/user.service.js
const auditService = require('./audit.service');

async update(id, data, req) {
  const oldUser = await prisma.user.findUnique({ where: { id } });
  
  const updatedUser = await prisma.user.update({
    where: { id },
    data
  });
  
  // Audit log
  await auditService.logUpdate('User', id, oldUser, updatedUser, req);
  
  return updatedUser;
}
```

---

## 7️⃣ EXPERT LEVEL - Secrets Management

### Environment Variables

```bash
# .env
NODE_ENV=production
PORT=3000

# Database
DATABASE_URL=postgresql://...

# JWT Secrets (generate with: openssl rand -base64 64)
JWT_ACCESS_SECRET=your-super-long-random-secret
JWT_REFRESH_SECRET=another-super-long-random-secret

# API Keys
SENDGRID_API_KEY=...
STRIPE_SECRET_KEY=...

# Encryption
ENCRYPTION_KEY=32-byte-hex-string
```

### Encrypted Secrets

```javascript
// src/utils/encryption.js
const crypto = require('crypto');

const ALGORITHM = 'aes-256-gcm';
const IV_LENGTH = 16;
const AUTH_TAG_LENGTH = 16;

const encrypt = (text) => {
  const key = Buffer.from(process.env.ENCRYPTION_KEY, 'hex');
  const iv = crypto.randomBytes(IV_LENGTH);
  
  const cipher = crypto.createCipheriv(ALGORITHM, key, iv);
  
  let encrypted = cipher.update(text, 'utf8', 'hex');
  encrypted += cipher.final('hex');
  
  const authTag = cipher.getAuthTag();
  
  return `${iv.toString('hex')}:${authTag.toString('hex')}:${encrypted}`;
};

const decrypt = (encryptedData) => {
  const key = Buffer.from(process.env.ENCRYPTION_KEY, 'hex');
  const [ivHex, authTagHex, encrypted] = encryptedData.split(':');
  
  const iv = Buffer.from(ivHex, 'hex');
  const authTag = Buffer.from(authTagHex, 'hex');
  
  const decipher = crypto.createDecipheriv(ALGORITHM, key, iv);
  decipher.setAuthTag(authTag);
  
  let decrypted = decipher.update(encrypted, 'hex', 'utf8');
  decrypted += decipher.final('utf8');
  
  return decrypted;
};

module.exports = { encrypt, decrypt };
```

---

## 8️⃣ Complete Security Setup

```javascript
// src/app.js
const express = require('express');
const helmet = require('helmet');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
const mongoSanitize = require('express-mongo-sanitize');
const xss = require('xss-clean');
const hpp = require('hpp');
const compression = require('compression');

const app = express();

// Trust proxy
app.set('trust proxy', 1);

// Security headers
app.use(helmet());

// CORS
app.use(cors({
  origin: process.env.CORS_ORIGINS?.split(',') || '*',
  credentials: true
}));

// Rate limiting
app.use('/api', rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100
}));

// Body parser with size limit
app.use(express.json({ limit: '10kb' }));
app.use(express.urlencoded({ extended: true, limit: '10kb' }));

// Data sanitization
app.use(mongoSanitize());
app.use(xss());

// Prevent parameter pollution
app.use(hpp({ whitelist: ['sort', 'filter'] }));

// Compression
app.use(compression());

// Remove X-Powered-By
app.disable('x-powered-by');

// Routes
app.use('/api/v1', require('./routes'));

// Error handler
app.use(require('./middlewares/error.middleware').errorHandler);

module.exports = app;
```

---

## 📊 Security Checklist

### Must Have

| Security | Implementation |
|----------|----------------|
| ✅ HTTPS | SSL/TLS in production |
| ✅ Helmet | Security headers |
| ✅ CORS | Origin whitelist |
| ✅ Rate Limiting | Prevent brute force |
| ✅ Input Validation | Joi/Yup |
| ✅ Parameterized Queries | Prevent SQL injection |
| ✅ Password Hashing | bcrypt 12+ rounds |
| ✅ JWT with expiry | Short-lived tokens |

### Should Have

| Security | Implementation |
|----------|----------------|
| ✅ XSS Protection | xss-clean, sanitize-html |
| ✅ CSRF Protection | Double submit cookie |
| ✅ Audit Logging | Track sensitive operations |
| ✅ Request ID | Correlation tracking |
| ✅ API Key | For external integrations |

---

## 💡 Summary

| Level | Focus |
|-------|-------|
| **Junior** | Helmet, CORS, basic setup |
| **Mid** | Input validation, sanitization, rate limiting |
| **Senior** | CSRF, API keys, advanced headers |
| **Expert** | Audit logging, encryption, secrets |

**Best Practices:**
- ✅ Defense in depth (multiple layers)
- ✅ Validate all input
- ✅ Use HTTPS everywhere
- ✅ Keep dependencies updated
- ✅ Log security events
- ✅ Regular security audits
- ❌ Don't trust user input
- ❌ Don't store secrets in code
- ❌ Don't expose stack traces in production
