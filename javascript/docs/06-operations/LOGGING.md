# 📝 LOGGING - Logging di Express (Junior → Senior)

Dokumentasi lengkap tentang logging - Winston, Morgan, dan best practices.

---

## 🎯 Logging Overview

```
       ┌────────────────┐
       │   Application  │
       └───────┬────────┘
               │
    ┌──────────┴──────────┐
    │                     │
    ▼                     ▼
┌───────┐           ┌─────────┐
│ Morgan│ ─────────▶│ Winston │
│(HTTP) │           │(General)│
└───────┘           └────┬────┘
                         │
    ┌────────────────────┼────────────────────┐
    │                    │                    │
    ▼                    ▼                    ▼
┌─────────┐        ┌───────────┐        ┌─────────┐
│ Console │        │   File    │        │ External│
│         │        │(Rotation) │        │(Loki,ELK)
└─────────┘        └───────────┘        └─────────┘
```

---

## 1️⃣ JUNIOR LEVEL - Basic Logging

### Installation

```bash
npm install winston
npm install morgan
npm install winston-daily-rotate-file
```

### Simple Console Logger

```javascript
// src/utils/logger.js
const winston = require('winston');

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple()
      )
    })
  ]
});

module.exports = logger;
```

### Using Logger

```javascript
const logger = require('./utils/logger');

// Log levels (dari terendah ke tertinggi)
logger.error('Something failed!');
logger.warn('Warning message');
logger.info('User logged in');
logger.http('HTTP request');
logger.debug('Debug info');

// Dengan metadata
logger.info('User created', { userId: '123', email: 'user@example.com' });

// Error dengan stack trace
try {
  throw new Error('Something went wrong');
} catch (error) {
  logger.error('Operation failed', { error });
}
```

---

## 2️⃣ JUNIOR LEVEL - HTTP Request Logging

### Morgan Setup

```javascript
// src/middleware/requestLogger.js
const morgan = require('morgan');
const logger = require('../utils/logger');

// Custom token
morgan.token('body', (req) => {
  // Jangan log password
  if (req.body && req.body.password) {
    const { password, ...safeBody } = req.body;
    return JSON.stringify(safeBody);
  }
  return JSON.stringify(req.body);
});

// Stream ke Winston
const stream = {
  write: (message) => {
    logger.http(message.trim());
  }
};

// Format untuk development
const devFormat = ':method :url :status :response-time ms - :res[content-length]';

// Format untuk production (JSON)
const prodFormat = JSON.stringify({
  method: ':method',
  url: ':url',
  status: ':status',
  responseTime: ':response-time ms',
  contentLength: ':res[content-length]',
  userAgent: ':user-agent',
  ip: ':remote-addr'
});

const requestLogger = morgan(
  process.env.NODE_ENV === 'production' ? prodFormat : devFormat,
  { stream }
);

module.exports = requestLogger;
```

### Integrate with Express

```javascript
// src/app.js
const express = require('express');
const requestLogger = require('./middleware/requestLogger');

const app = express();

// Request logging
app.use(requestLogger);

// ... rest of middleware
```

---

## 3️⃣ MID LEVEL - Advanced Winston Setup

### Complete Logger Configuration

```javascript
// src/lib/logger.js
const winston = require('winston');
const DailyRotateFile = require('winston-daily-rotate-file');
const path = require('path');

const logDir = process.env.LOG_DIR || 'logs';

// Custom format
const customFormat = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
  winston.format.errors({ stack: true }),
  winston.format.printf(({ timestamp, level, message, ...meta }) => {
    let logMessage = `${timestamp} [${level.toUpperCase()}]: ${message}`;
    
    if (Object.keys(meta).length > 0) {
      logMessage += ` ${JSON.stringify(meta)}`;
    }
    
    return logMessage;
  })
);

// JSON format untuk production
const jsonFormat = winston.format.combine(
  winston.format.timestamp(),
  winston.format.errors({ stack: true }),
  winston.format.json()
);

// Transports
const transports = [];

// Console transport
if (process.env.NODE_ENV !== 'test') {
  transports.push(
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        customFormat
      )
    })
  );
}

// File transport - all logs
transports.push(
  new DailyRotateFile({
    dirname: logDir,
    filename: 'app-%DATE%.log',
    datePattern: 'YYYY-MM-DD',
    maxSize: '20m',
    maxFiles: '14d',
    format: jsonFormat
  })
);

// Error-only file
transports.push(
  new DailyRotateFile({
    dirname: logDir,
    filename: 'error-%DATE%.log',
    datePattern: 'YYYY-MM-DD',
    level: 'error',
    maxSize: '20m',
    maxFiles: '30d',
    format: jsonFormat
  })
);

// Create logger
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  transports,
  // Handle uncaught exceptions
  exceptionHandlers: [
    new DailyRotateFile({
      dirname: logDir,
      filename: 'exceptions-%DATE%.log',
      datePattern: 'YYYY-MM-DD',
      maxSize: '20m',
      maxFiles: '30d'
    })
  ],
  // Handle unhandled rejections
  rejectionHandlers: [
    new DailyRotateFile({
      dirname: logDir,
      filename: 'rejections-%DATE%.log',
      datePattern: 'YYYY-MM-DD',
      maxSize: '20m',
      maxFiles: '30d'
    })
  ]
});

module.exports = logger;
```

---

## 4️⃣ MID LEVEL - Request Context

### Request ID Middleware

```javascript
// src/middleware/requestId.js
const { v4: uuidv4 } = require('uuid');

const requestId = (req, res, next) => {
  // Use existing header or generate new
  const id = req.headers['x-request-id'] || uuidv4();
  
  req.requestId = id;
  res.setHeader('X-Request-Id', id);
  
  next();
};

module.exports = requestId;
```

### Context-aware Logging

```javascript
// src/lib/contextLogger.js
const { AsyncLocalStorage } = require('async_hooks');
const logger = require('./logger');

const asyncLocalStorage = new AsyncLocalStorage();

// Middleware untuk set context
const loggerContext = (req, res, next) => {
  const context = {
    requestId: req.requestId,
    userId: req.user?.id,
    ip: req.ip,
    userAgent: req.get('User-Agent'),
    path: req.path,
    method: req.method
  };

  asyncLocalStorage.run(context, () => {
    next();
  });
};

// Context-aware logger
const contextLogger = {
  log: (level, message, meta = {}) => {
    const context = asyncLocalStorage.getStore() || {};
    logger.log(level, message, { ...context, ...meta });
  },
  
  error: (message, meta) => contextLogger.log('error', message, meta),
  warn: (message, meta) => contextLogger.log('warn', message, meta),
  info: (message, meta) => contextLogger.log('info', message, meta),
  http: (message, meta) => contextLogger.log('http', message, meta),
  debug: (message, meta) => contextLogger.log('debug', message, meta)
};

module.exports = { loggerContext, contextLogger };
```

### Usage in Services

```javascript
// src/services/user.service.js
const { contextLogger: logger } = require('../lib/contextLogger');

class UserService {
  async findById(id) {
    logger.debug('Finding user by id', { userId: id });
    
    const user = await prisma.user.findUnique({
      where: { id }
    });

    if (!user) {
      logger.warn('User not found', { userId: id });
      throw new ApiError(404, 'User not found');
    }

    logger.info('User found', { userId: id });
    return user;
  }
}
```

---

## 5️⃣ SENIOR LEVEL - Performance Logging

### Response Time Logging

```javascript
// src/middleware/performanceLogger.js
const { contextLogger: logger } = require('../lib/contextLogger');

const performanceLogger = (req, res, next) => {
  const start = process.hrtime.bigint();

  // Log request start
  logger.debug('Request started', {
    body: sanitizeBody(req.body)
  });

  // Override res.end untuk log response
  const originalEnd = res.end;
  res.end = function(chunk, encoding) {
    const end = process.hrtime.bigint();
    const durationMs = Number(end - start) / 1e6;

    // Log level berdasarkan response time
    const level = durationMs > 3000 ? 'warn' : 
                  durationMs > 1000 ? 'info' : 'http';

    logger.log(level, 'Request completed', {
      statusCode: res.statusCode,
      duration: `${durationMs.toFixed(2)}ms`
    });

    // Warn for slow requests
    if (durationMs > 5000) {
      logger.warn('Slow request detected', {
        duration: `${durationMs.toFixed(2)}ms`,
        threshold: '5000ms'
      });
    }

    originalEnd.call(this, chunk, encoding);
  };

  next();
};

function sanitizeBody(body) {
  if (!body) return undefined;
  
  const sensitiveFields = ['password', 'token', 'secret', 'creditCard'];
  const sanitized = { ...body };
  
  sensitiveFields.forEach(field => {
    if (sanitized[field]) {
      sanitized[field] = '[REDACTED]';
    }
  });
  
  return sanitized;
}

module.exports = performanceLogger;
```

### Database Query Logging

```javascript
// src/lib/prisma.js
const { PrismaClient } = require('@prisma/client');
const logger = require('./logger');

const prisma = new PrismaClient({
  log: [
    {
      emit: 'event',
      level: 'query',
    },
    {
      emit: 'event',
      level: 'error',
    },
    {
      emit: 'event',
      level: 'warn',
    },
  ],
});

// Log queries
prisma.$on('query', (e) => {
  logger.debug('Database query', {
    query: e.query,
    params: e.params,
    duration: `${e.duration}ms`
  });

  // Warn slow queries
  if (e.duration > 1000) {
    logger.warn('Slow query detected', {
      query: e.query,
      duration: `${e.duration}ms`
    });
  }
});

prisma.$on('error', (e) => {
  logger.error('Database error', { error: e.message });
});

prisma.$on('warn', (e) => {
  logger.warn('Database warning', { warning: e.message });
});

module.exports = prisma;
```

---

## 6️⃣ SENIOR LEVEL - Audit Logging

### Audit Logger

```javascript
// src/lib/auditLogger.js
const logger = require('./logger');

const AUDIT_ACTIONS = {
  CREATE: 'CREATE',
  READ: 'READ',
  UPDATE: 'UPDATE',
  DELETE: 'DELETE',
  LOGIN: 'LOGIN',
  LOGOUT: 'LOGOUT',
  FAILED_LOGIN: 'FAILED_LOGIN'
};

const auditLog = (action, details) => {
  logger.info('AUDIT', {
    type: 'audit',
    action,
    timestamp: new Date().toISOString(),
    ...details
  });
};

// Middleware untuk audit
const auditMiddleware = (action, getResourceInfo) => {
  return (req, res, next) => {
    // Log after response
    const originalEnd = res.end;
    res.end = function(chunk, encoding) {
      // Only audit successful operations
      if (res.statusCode < 400) {
        const resourceInfo = getResourceInfo ? getResourceInfo(req, res) : {};
        
        auditLog(action, {
          userId: req.user?.id,
          userEmail: req.user?.email,
          ip: req.ip,
          userAgent: req.get('User-Agent'),
          statusCode: res.statusCode,
          ...resourceInfo
        });
      }
      
      originalEnd.call(this, chunk, encoding);
    };
    
    next();
  };
};

module.exports = { auditLog, auditMiddleware, AUDIT_ACTIONS };
```

### Usage

```javascript
// src/routes/user.routes.js
const { auditMiddleware, AUDIT_ACTIONS } = require('../lib/auditLogger');

router.delete('/:id',
  auth,
  authorize('admin'),
  auditMiddleware(AUDIT_ACTIONS.DELETE, (req) => ({
    resource: 'user',
    resourceId: req.params.id
  })),
  userController.delete
);

router.put('/:id',
  auth,
  auditMiddleware(AUDIT_ACTIONS.UPDATE, (req) => ({
    resource: 'user',
    resourceId: req.params.id,
    changes: Object.keys(req.body)
  })),
  userController.update
);
```

---

## 7️⃣ EXPERT LEVEL - Structured Logging

### Log Levels & Severity

```javascript
// src/lib/structuredLogger.js
const winston = require('winston');

const levels = {
  error: 0,    // Error yang butuh immediate attention
  warn: 1,     // Warning, potential issue
  info: 2,     // Important events (user actions, etc)
  http: 3,     // HTTP requests
  debug: 4,    // Debug information
  trace: 5     // Very detailed logs
};

const colors = {
  error: 'red',
  warn: 'yellow',
  info: 'green',
  http: 'magenta',
  debug: 'blue',
  trace: 'gray'
};

winston.addColors(colors);

// Structured log helper
const createStructuredLog = (level, event, data = {}) => ({
  timestamp: new Date().toISOString(),
  level,
  event,
  environment: process.env.NODE_ENV,
  service: process.env.SERVICE_NAME || 'api',
  version: process.env.npm_package_version,
  ...data
});

module.exports = { levels, createStructuredLog };
```

### Log Aggregation Format

```javascript
// src/lib/elkLogger.js (untuk ELK Stack)
const winston = require('winston');
const ecsFormat = require('@elastic/ecs-winston-format');

const elkLogger = winston.createLogger({
  format: ecsFormat(),
  transports: [
    new winston.transports.Console()
  ]
});

// Log dengan ECS format
elkLogger.info('User logged in', {
  user: { id: '123', name: 'John' },
  event: { action: 'login', outcome: 'success' }
});
```

---

## 8️⃣ EXPERT LEVEL - Error Tracking

### Error Handler with Logging

```javascript
// src/middleware/errorHandler.js
const { contextLogger: logger } = require('../lib/contextLogger');
const ApiError = require('../utils/ApiError');

const errorHandler = (err, req, res, next) => {
  // Default values
  let statusCode = 500;
  let message = 'Internal Server Error';
  let isOperational = false;

  if (err instanceof ApiError) {
    statusCode = err.statusCode;
    message = err.message;
    isOperational = err.isOperational;
  }

  // Log error
  const errorLog = {
    error: {
      name: err.name,
      message: err.message,
      stack: err.stack,
      isOperational
    },
    request: {
      url: req.originalUrl,
      method: req.method,
      body: sanitizeBody(req.body),
      query: req.query,
      params: req.params
    }
  };

  if (statusCode >= 500) {
    logger.error('Server error occurred', errorLog);
  } else if (statusCode >= 400) {
    logger.warn('Client error occurred', errorLog);
  }

  // Response
  res.status(statusCode).json({
    success: false,
    message,
    ...(process.env.NODE_ENV === 'development' && {
      stack: err.stack
    })
  });
};

module.exports = errorHandler;
```

### Uncaught Exception Handling

```javascript
// src/index.js
const logger = require('./lib/logger');

// Uncaught exceptions
process.on('uncaughtException', (error) => {
  logger.error('Uncaught Exception', {
    error: error.message,
    stack: error.stack
  });
  
  // Exit after logging
  process.exit(1);
});

// Unhandled rejections
process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled Rejection', {
    reason: reason instanceof Error ? reason.message : reason,
    stack: reason instanceof Error ? reason.stack : undefined
  });
});

// SIGTERM
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  server.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });
});
```

---

## 📊 Complete Setup

```javascript
// src/app.js
const express = require('express');
const requestId = require('./middleware/requestId');
const requestLogger = require('./middleware/requestLogger');
const { loggerContext } = require('./lib/contextLogger');
const performanceLogger = require('./middleware/performanceLogger');
const errorHandler = require('./middleware/errorHandler');
const logger = require('./lib/logger');

const app = express();

// Request ID (first!)
app.use(requestId);

// Logger context
app.use(loggerContext);

// HTTP logging
app.use(requestLogger);

// Performance logging
app.use(performanceLogger);

// Body parser
app.use(express.json());

// Routes
app.use('/api/v1', routes);

// Error handler (last!)
app.use(errorHandler);

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  logger.info(`Server started on port ${PORT}`, {
    environment: process.env.NODE_ENV,
    port: PORT
  });
});

module.exports = app;
```

---

## 📝 Log Output Examples

### Console (Development)

```
2024-01-15 10:30:45 [INFO]: Server started on port 3000 {"environment":"development","port":3000}
2024-01-15 10:30:50 [HTTP]: POST /api/v1/auth/login 200 45.23ms
2024-01-15 10:30:50 [INFO]: AUDIT {"type":"audit","action":"LOGIN","userId":"123"}
```

### JSON (Production)

```json
{"timestamp":"2024-01-15T10:30:45.123Z","level":"info","message":"Server started","service":"api","port":3000}
{"timestamp":"2024-01-15T10:30:50.456Z","level":"http","message":"Request completed","requestId":"abc-123","method":"POST","path":"/api/v1/auth/login","statusCode":200,"duration":"45.23ms"}
```

---

## 💡 Summary

| Level | Focus |
|-------|-------|
| **Junior** | Winston setup, Morgan HTTP logging |
| **Mid** | File rotation, request context |
| **Senior** | Performance logging, audit logs |
| **Expert** | Structured logging, error tracking |

**Best Practices:**
- ✅ Use log levels correctly
- ✅ Include request ID di semua logs
- ✅ Jangan log sensitive data
- ✅ Rotate log files
- ✅ Log async errors properly
- ✅ Use structured JSON untuk production
- ❌ Don't log passwords/tokens
- ❌ Don't over-log (too verbose)
