# 🚀 EXPRESS.JS - Web Framework (Junior → Senior)

Dokumentasi lengkap Express.js - framework web paling populer untuk Node.js.

---

## 🎯 Apa itu Express.js?

```
Express.js = Minimal & flexible Node.js web framework

Features:
- Routing
- Middleware
- Template engines
- Static files
- Error handling
```

---

## 1️⃣ JUNIOR LEVEL - Getting Started

### Installation

```bash
mkdir my-api
cd my-api
npm init -y
npm install express
npm install -D nodemon
```

### Package.json Scripts

```json
{
  "scripts": {
    "start": "node src/index.js",
    "dev": "nodemon src/index.js"
  }
}
```

### Hello World

```javascript
// src/index.js
const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

// Middleware untuk parsing JSON
app.use(express.json());

// Route sederhana
app.get('/', (req, res) => {
  res.json({ message: 'Hello World!' });
});

// Start server
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
```

```bash
npm run dev
```

---

## 2️⃣ JUNIOR LEVEL - Routing Basics

### HTTP Methods

```javascript
const express = require('express');
const app = express();

app.use(express.json());

// GET - Ambil data
app.get('/users', (req, res) => {
  res.json({ users: [] });
});

// GET dengan parameter
app.get('/users/:id', (req, res) => {
  const { id } = req.params;
  res.json({ id });
});

// POST - Buat data baru
app.post('/users', (req, res) => {
  const { name, email } = req.body;
  res.status(201).json({ id: 1, name, email });
});

// PUT - Update semua field
app.put('/users/:id', (req, res) => {
  const { id } = req.params;
  const { name, email } = req.body;
  res.json({ id, name, email });
});

// PATCH - Update sebagian field
app.patch('/users/:id', (req, res) => {
  const { id } = req.params;
  res.json({ id, ...req.body });
});

// DELETE - Hapus data
app.delete('/users/:id', (req, res) => {
  res.status(204).send(); // No content
});

app.listen(3000);
```

### Query Parameters

```javascript
// GET /search?q=john&page=1&limit=10
app.get('/search', (req, res) => {
  const { q, page = 1, limit = 10 } = req.query;
  
  res.json({
    query: q,
    page: parseInt(page),
    limit: parseInt(limit)
  });
});
```

### Route Parameters

```javascript
// GET /users/123/posts/456
app.get('/users/:userId/posts/:postId', (req, res) => {
  const { userId, postId } = req.params;
  res.json({ userId, postId });
});

// Optional parameter
app.get('/files/:name.:ext?', (req, res) => {
  const { name, ext } = req.params;
  res.json({ name, ext: ext || 'txt' });
});
```

---

## 3️⃣ MID LEVEL - Router & Project Structure

### Project Structure

```
my-api/
├── src/
│   ├── index.js          # Entry point
│   ├── app.js            # Express app
│   ├── config/
│   │   └── index.js      # Configuration
│   ├── routes/
│   │   ├── index.js      # Route aggregator
│   │   ├── auth.routes.js
│   │   └── user.routes.js
│   ├── controllers/
│   │   ├── auth.controller.js
│   │   └── user.controller.js
│   ├── services/
│   │   ├── auth.service.js
│   │   └── user.service.js
│   ├── middlewares/
│   │   ├── auth.middleware.js
│   │   ├── error.middleware.js
│   │   └── validate.middleware.js
│   ├── models/           # Database models
│   ├── utils/
│   │   └── ApiError.js
│   └── validations/
│       └── user.validation.js
├── .env
├── .gitignore
└── package.json
```

### Express Router

```javascript
// src/routes/user.routes.js
const express = require('express');
const router = express.Router();
const userController = require('../controllers/user.controller');
const auth = require('../middlewares/auth.middleware');

router.get('/', userController.getUsers);
router.get('/:id', userController.getUser);
router.post('/', auth, userController.createUser);
router.put('/:id', auth, userController.updateUser);
router.delete('/:id', auth, userController.deleteUser);

module.exports = router;
```

```javascript
// src/routes/index.js
const express = require('express');
const router = express.Router();

const userRoutes = require('./user.routes');
const authRoutes = require('./auth.routes');

router.use('/auth', authRoutes);
router.use('/users', userRoutes);

module.exports = router;
```

```javascript
// src/app.js
const express = require('express');
const routes = require('./routes');

const app = express();

app.use(express.json());
app.use('/api/v1', routes);

module.exports = app;
```

```javascript
// src/index.js
const app = require('./app');
const config = require('./config');

app.listen(config.port, () => {
  console.log(`Server running on port ${config.port}`);
});
```

---

## 4️⃣ MID LEVEL - Middleware

### Built-in Middleware

```javascript
const express = require('express');
const path = require('path');
const app = express();

// Parse JSON body
app.use(express.json({ limit: '10mb' }));

// Parse URL-encoded body (form data)
app.use(express.urlencoded({ extended: true }));

// Serve static files
app.use(express.static(path.join(__dirname, 'public')));
```

### Third-party Middleware

```bash
npm install cors helmet morgan compression
```

```javascript
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const compression = require('compression');

const app = express();

// Security headers
app.use(helmet());

// CORS
app.use(cors({
  origin: ['http://localhost:3000', 'https://myapp.com'],
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  credentials: true
}));

// Logging
app.use(morgan('dev')); // Development
// app.use(morgan('combined')); // Production

// Compress responses
app.use(compression());

// Parse JSON
app.use(express.json());
```

### Custom Middleware

```javascript
// src/middlewares/logger.middleware.js
const logger = (req, res, next) => {
  const start = Date.now();
  
  res.on('finish', () => {
    const duration = Date.now() - start;
    console.log(`${req.method} ${req.url} ${res.statusCode} - ${duration}ms`);
  });
  
  next();
};

module.exports = logger;
```

```javascript
// src/middlewares/requestId.middleware.js
const { v4: uuidv4 } = require('uuid');

const requestId = (req, res, next) => {
  req.id = req.headers['x-request-id'] || uuidv4();
  res.setHeader('X-Request-ID', req.id);
  next();
};

module.exports = requestId;
```

### Async Middleware (Error Handling)

```javascript
// src/utils/asyncHandler.js
const asyncHandler = (fn) => (req, res, next) => {
  Promise.resolve(fn(req, res, next)).catch(next);
};

module.exports = asyncHandler;

// Usage in controller
const asyncHandler = require('../utils/asyncHandler');

const getUser = asyncHandler(async (req, res) => {
  const user = await userService.findById(req.params.id);
  res.json({ data: user });
});
```

---

## 5️⃣ MID-SENIOR LEVEL - Error Handling

### Custom Error Class

```javascript
// src/utils/ApiError.js
class ApiError extends Error {
  constructor(statusCode, message, errors = []) {
    super(message);
    this.statusCode = statusCode;
    this.status = `${statusCode}`.startsWith('4') ? 'fail' : 'error';
    this.isOperational = true;
    this.errors = errors;

    Error.captureStackTrace(this, this.constructor);
  }

  static badRequest(message, errors = []) {
    return new ApiError(400, message, errors);
  }

  static unauthorized(message = 'Unauthorized') {
    return new ApiError(401, message);
  }

  static forbidden(message = 'Forbidden') {
    return new ApiError(403, message);
  }

  static notFound(message = 'Resource not found') {
    return new ApiError(404, message);
  }

  static conflict(message = 'Conflict') {
    return new ApiError(409, message);
  }

  static internal(message = 'Internal server error') {
    return new ApiError(500, message);
  }
}

module.exports = ApiError;
```

### Error Middleware

```javascript
// src/middlewares/error.middleware.js
const ApiError = require('../utils/ApiError');

// 404 Handler
const notFound = (req, res, next) => {
  next(ApiError.notFound(`Cannot ${req.method} ${req.url}`));
};

// Global Error Handler
const errorHandler = (err, req, res, next) => {
  let error = { ...err };
  error.message = err.message;
  error.stack = err.stack;

  // Log error
  console.error('Error:', {
    message: err.message,
    stack: err.stack,
    url: req.url,
    method: req.method
  });

  // Mongoose bad ObjectId
  if (err.name === 'CastError') {
    error = ApiError.badRequest('Invalid ID format');
  }

  // Mongoose duplicate key
  if (err.code === 11000) {
    error = ApiError.conflict('Duplicate field value');
  }

  // Mongoose validation error
  if (err.name === 'ValidationError') {
    const errors = Object.values(err.errors).map(e => e.message);
    error = ApiError.badRequest('Validation Error', errors);
  }

  // JWT errors
  if (err.name === 'JsonWebTokenError') {
    error = ApiError.unauthorized('Invalid token');
  }

  if (err.name === 'TokenExpiredError') {
    error = ApiError.unauthorized('Token expired');
  }

  const statusCode = error.statusCode || 500;
  const response = {
    success: false,
    status: error.status || 'error',
    message: error.message || 'Internal Server Error',
    ...(error.errors?.length && { errors: error.errors }),
    ...(process.env.NODE_ENV === 'development' && { stack: error.stack })
  };

  res.status(statusCode).json(response);
};

module.exports = { notFound, errorHandler };
```

### Using Error Handler

```javascript
// src/app.js
const express = require('express');
const routes = require('./routes');
const { notFound, errorHandler } = require('./middlewares/error.middleware');

const app = express();

app.use(express.json());

// Routes
app.use('/api/v1', routes);

// Error handling (MUST be last)
app.use(notFound);
app.use(errorHandler);

module.exports = app;
```

```javascript
// src/controllers/user.controller.js
const asyncHandler = require('../utils/asyncHandler');
const ApiError = require('../utils/ApiError');
const userService = require('../services/user.service');

const getUser = asyncHandler(async (req, res) => {
  const user = await userService.findById(req.params.id);
  
  if (!user) {
    throw ApiError.notFound('User not found');
  }
  
  res.json({ success: true, data: user });
});

const createUser = asyncHandler(async (req, res) => {
  const { email } = req.body;
  
  const existingUser = await userService.findByEmail(email);
  if (existingUser) {
    throw ApiError.conflict('Email already registered');
  }
  
  const user = await userService.create(req.body);
  res.status(201).json({ success: true, data: user });
});

module.exports = { getUser, createUser };
```

---

## 6️⃣ SENIOR LEVEL - Validation

### Using Joi

```bash
npm install joi
```

```javascript
// src/validations/user.validation.js
const Joi = require('joi');

const createUser = Joi.object({
  name: Joi.string()
    .min(2)
    .max(50)
    .required()
    .messages({
      'string.min': 'Name must be at least 2 characters',
      'any.required': 'Name is required'
    }),
  email: Joi.string()
    .email()
    .required()
    .messages({
      'string.email': 'Invalid email format',
      'any.required': 'Email is required'
    }),
  password: Joi.string()
    .min(8)
    .pattern(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/)
    .required()
    .messages({
      'string.min': 'Password must be at least 8 characters',
      'string.pattern.base': 'Password must contain uppercase, lowercase and number'
    }),
  role: Joi.string()
    .valid('user', 'admin')
    .default('user')
});

const updateUser = Joi.object({
  name: Joi.string().min(2).max(50),
  email: Joi.string().email()
}).min(1);

const getUser = Joi.object({
  id: Joi.string().uuid().required()
});

module.exports = {
  createUser,
  updateUser,
  getUser
};
```

### Validation Middleware

```javascript
// src/middlewares/validate.middleware.js
const ApiError = require('../utils/ApiError');

const validate = (schema, property = 'body') => {
  return (req, res, next) => {
    const { error, value } = schema.validate(req[property], {
      abortEarly: false,
      stripUnknown: true
    });

    if (error) {
      const errors = error.details.map(detail => ({
        field: detail.path.join('.'),
        message: detail.message
      }));
      return next(ApiError.badRequest('Validation Error', errors));
    }

    req[property] = value;
    next();
  };
};

module.exports = validate;
```

### Using in Routes

```javascript
// src/routes/user.routes.js
const express = require('express');
const router = express.Router();
const userController = require('../controllers/user.controller');
const validate = require('../middlewares/validate.middleware');
const { createUser, updateUser, getUser } = require('../validations/user.validation');

router.get('/', userController.getUsers);
router.get('/:id', validate(getUser, 'params'), userController.getUser);
router.post('/', validate(createUser), userController.createUser);
router.put('/:id', validate(updateUser), userController.updateUser);
router.delete('/:id', validate(getUser, 'params'), userController.deleteUser);

module.exports = router;
```

---

## 7️⃣ SENIOR LEVEL - Response Format

### Standard Response

```javascript
// src/utils/response.js
class ApiResponse {
  static success(res, data, message = 'Success', statusCode = 200) {
    return res.status(statusCode).json({
      success: true,
      message,
      data
    });
  }

  static created(res, data, message = 'Created successfully') {
    return this.success(res, data, message, 201);
  }

  static noContent(res) {
    return res.status(204).send();
  }

  static paginated(res, data, pagination, message = 'Success') {
    return res.status(200).json({
      success: true,
      message,
      data,
      pagination
    });
  }
}

module.exports = ApiResponse;
```

### Using in Controller

```javascript
// src/controllers/user.controller.js
const asyncHandler = require('../utils/asyncHandler');
const ApiResponse = require('../utils/response');
const userService = require('../services/user.service');

const getUsers = asyncHandler(async (req, res) => {
  const { page = 1, limit = 10 } = req.query;
  const result = await userService.findAll({ page, limit });
  
  ApiResponse.paginated(res, result.data, result.pagination);
});

const getUser = asyncHandler(async (req, res) => {
  const user = await userService.findById(req.params.id);
  ApiResponse.success(res, user);
});

const createUser = asyncHandler(async (req, res) => {
  const user = await userService.create(req.body);
  ApiResponse.created(res, user, 'User created successfully');
});

const deleteUser = asyncHandler(async (req, res) => {
  await userService.delete(req.params.id);
  ApiResponse.noContent(res);
});

module.exports = { getUsers, getUser, createUser, deleteUser };
```

---

## 8️⃣ EXPERT LEVEL - Rate Limiting & Security

### Rate Limiting

```bash
npm install express-rate-limit
```

```javascript
// src/middlewares/rateLimiter.middleware.js
const rateLimit = require('express-rate-limit');
const ApiError = require('../utils/ApiError');

// General rate limiter
const generalLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // 100 requests per window
  message: { success: false, message: 'Too many requests' },
  standardHeaders: true,
  legacyHeaders: false
});

// Auth rate limiter (stricter)
const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5,
  message: { success: false, message: 'Too many login attempts' },
  skipSuccessfulRequests: true
});

// API rate limiter
const apiLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 60, // 60 requests per minute
  keyGenerator: (req) => {
    return req.user?.id || req.ip;
  }
});

module.exports = { generalLimiter, authLimiter, apiLimiter };
```

### Complete Security Setup

```javascript
// src/app.js
const express = require('express');
const helmet = require('helmet');
const cors = require('cors');
const mongoSanitize = require('express-mongo-sanitize');
const xss = require('xss-clean');
const hpp = require('hpp');
const { generalLimiter } = require('./middlewares/rateLimiter.middleware');

const app = express();

// Security headers
app.use(helmet());

// CORS
app.use(cors({
  origin: process.env.CORS_ORIGIN?.split(',') || '*',
  credentials: true
}));

// Rate limiting
app.use('/api', generalLimiter);

// Body parser
app.use(express.json({ limit: '10kb' }));
app.use(express.urlencoded({ extended: true, limit: '10kb' }));

// Data sanitization against NoSQL injection
app.use(mongoSanitize());

// Data sanitization against XSS
app.use(xss());

// Prevent parameter pollution
app.use(hpp({
  whitelist: ['sort', 'fields', 'page', 'limit']
}));

// Trust proxy (for rate limiter behind reverse proxy)
app.set('trust proxy', 1);

// Routes
app.use('/api/v1', require('./routes'));

// Error handling
app.use(require('./middlewares/error.middleware').notFound);
app.use(require('./middlewares/error.middleware').errorHandler);

module.exports = app;
```

---

## 📊 Express Cheat Sheet

### Request Object

| Property | Description |
|----------|-------------|
| `req.params` | Route parameters (`:id`) |
| `req.query` | Query string (`?key=value`) |
| `req.body` | Request body (POST/PUT) |
| `req.headers` | Request headers |
| `req.method` | HTTP method |
| `req.url` | Request URL |
| `req.ip` | Client IP |
| `req.cookies` | Cookies (with cookie-parser) |

### Response Methods

| Method | Description |
|--------|-------------|
| `res.json(data)` | Send JSON response |
| `res.status(code)` | Set status code |
| `res.send(data)` | Send response |
| `res.redirect(url)` | Redirect |
| `res.setHeader(key, value)` | Set header |
| `res.cookie(name, value)` | Set cookie |

### Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 422 | Unprocessable Entity |
| 500 | Internal Server Error |

---

## 💡 Summary

| Level | Focus |
|-------|-------|
| **Junior** | Routing, HTTP methods |
| **Mid** | Project structure, middleware |
| **Mid-Senior** | Error handling, validation |
| **Senior** | Response format, Joi |
| **Expert** | Rate limiting, security |

**Best Practices:**
- ✅ Use async/await dengan error handling
- ✅ Validate semua input
- ✅ Gunakan middleware untuk reusability
- ✅ Consistent response format
- ✅ Proper error handling
- ❌ Don't trust user input
- ❌ Don't expose stack traces in production
- ❌ Don't skip rate limiting
