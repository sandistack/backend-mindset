# 🔐 AUTHENTICATION - Auth di Express (Junior → Senior)

Dokumentasi lengkap tentang authentication di Express.js - JWT, bcrypt, dan RBAC.

---

## 🎯 Auth Flow

```
Registration:
User → Password Hash → Store DB

Login:
User → Validate Password → Generate JWT → Send to Client

Protected Route:
Request + Token → Validate Token → Allow/Deny
```

---

## 1️⃣ JUNIOR LEVEL - Password Hashing

### Setup bcrypt

```bash
npm install bcrypt
```

### Hash Password

```javascript
// src/utils/password.js
const bcrypt = require('bcrypt');

const SALT_ROUNDS = 12;

// Hash password
const hashPassword = async (password) => {
  return bcrypt.hash(password, SALT_ROUNDS);
};

// Compare password
const comparePassword = async (password, hash) => {
  return bcrypt.compare(password, hash);
};

module.exports = { hashPassword, comparePassword };
```

### Usage

```javascript
const { hashPassword, comparePassword } = require('./utils/password');

// Register
const hashedPassword = await hashPassword('user123');
// Store hashedPassword di database

// Login
const isValid = await comparePassword('user123', hashedPassword);
// true jika password cocok
```

---

## 2️⃣ JUNIOR LEVEL - JWT Basics

### Setup

```bash
npm install jsonwebtoken
```

### JWT Service

```javascript
// src/services/token.service.js
const jwt = require('jsonwebtoken');

const config = {
  accessSecret: process.env.JWT_ACCESS_SECRET || 'access-secret',
  refreshSecret: process.env.JWT_REFRESH_SECRET || 'refresh-secret',
  accessExpiresIn: '15m',
  refreshExpiresIn: '7d'
};

const generateAccessToken = (payload) => {
  return jwt.sign(payload, config.accessSecret, {
    expiresIn: config.accessExpiresIn
  });
};

const generateRefreshToken = (payload) => {
  return jwt.sign(payload, config.refreshSecret, {
    expiresIn: config.refreshExpiresIn
  });
};

const generateTokens = (user) => {
  const payload = {
    sub: user.id,
    email: user.email,
    role: user.role
  };

  return {
    accessToken: generateAccessToken(payload),
    refreshToken: generateRefreshToken(payload),
    expiresIn: 900 // 15 minutes in seconds
  };
};

const verifyAccessToken = (token) => {
  return jwt.verify(token, config.accessSecret);
};

const verifyRefreshToken = (token) => {
  return jwt.verify(token, config.refreshSecret);
};

module.exports = {
  generateTokens,
  generateAccessToken,
  generateRefreshToken,
  verifyAccessToken,
  verifyRefreshToken
};
```

---

## 3️⃣ MID LEVEL - Auth Service

### Complete Auth Service

```javascript
// src/services/auth.service.js
const prisma = require('../lib/prisma');
const { hashPassword, comparePassword } = require('../utils/password');
const tokenService = require('./token.service');
const ApiError = require('../utils/ApiError');

class AuthService {
  async register(data) {
    const { email, password, name } = data;

    // Check if email exists
    const existingUser = await prisma.user.findUnique({
      where: { email }
    });

    if (existingUser) {
      throw ApiError.conflict('Email already registered');
    }

    // Hash password
    const hashedPassword = await hashPassword(password);

    // Create user
    const user = await prisma.user.create({
      data: {
        email,
        name,
        password: hashedPassword
      },
      select: {
        id: true,
        email: true,
        name: true,
        role: true,
        createdAt: true
      }
    });

    // Generate tokens
    const tokens = tokenService.generateTokens(user);

    return { user, ...tokens };
  }

  async login(email, password) {
    // Find user with password
    const user = await prisma.user.findUnique({
      where: { email }
    });

    if (!user) {
      throw ApiError.unauthorized('Invalid email or password');
    }

    // Compare password
    const isPasswordValid = await comparePassword(password, user.password);

    if (!isPasswordValid) {
      throw ApiError.unauthorized('Invalid email or password');
    }

    // Generate tokens
    const tokens = tokenService.generateTokens(user);

    // Remove password from response
    const { password: _, ...userWithoutPassword } = user;

    return { user: userWithoutPassword, ...tokens };
  }

  async refreshToken(refreshToken) {
    try {
      const payload = tokenService.verifyRefreshToken(refreshToken);

      const user = await prisma.user.findUnique({
        where: { id: payload.sub },
        select: {
          id: true,
          email: true,
          role: true
        }
      });

      if (!user) {
        throw ApiError.unauthorized('User not found');
      }

      const tokens = tokenService.generateTokens(user);

      return tokens;
    } catch (error) {
      throw ApiError.unauthorized('Invalid refresh token');
    }
  }

  async logout(userId, refreshToken) {
    // Optional: Store refresh token in blacklist
    // await prisma.tokenBlacklist.create({
    //   data: { token: refreshToken, userId }
    // });
    return { message: 'Logged out successfully' };
  }

  async getMe(userId) {
    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: {
        id: true,
        email: true,
        name: true,
        role: true,
        createdAt: true,
        profile: true
      }
    });

    if (!user) {
      throw ApiError.notFound('User not found');
    }

    return user;
  }

  async changePassword(userId, currentPassword, newPassword) {
    const user = await prisma.user.findUnique({
      where: { id: userId }
    });

    const isPasswordValid = await comparePassword(currentPassword, user.password);

    if (!isPasswordValid) {
      throw ApiError.badRequest('Current password is incorrect');
    }

    const hashedPassword = await hashPassword(newPassword);

    await prisma.user.update({
      where: { id: userId },
      data: { password: hashedPassword }
    });

    return { message: 'Password changed successfully' };
  }
}

module.exports = new AuthService();
```

### Auth Controller

```javascript
// src/controllers/auth.controller.js
const asyncHandler = require('../utils/asyncHandler');
const ApiResponse = require('../utils/response');
const authService = require('../services/auth.service');

const register = asyncHandler(async (req, res) => {
  const result = await authService.register(req.body);
  ApiResponse.created(res, result, 'Registration successful');
});

const login = asyncHandler(async (req, res) => {
  const { email, password } = req.body;
  const result = await authService.login(email, password);
  ApiResponse.success(res, result, 'Login successful');
});

const refreshToken = asyncHandler(async (req, res) => {
  const { refreshToken } = req.body;
  const tokens = await authService.refreshToken(refreshToken);
  ApiResponse.success(res, tokens);
});

const logout = asyncHandler(async (req, res) => {
  const { refreshToken } = req.body;
  await authService.logout(req.user.sub, refreshToken);
  ApiResponse.success(res, null, 'Logged out successfully');
});

const getMe = asyncHandler(async (req, res) => {
  const user = await authService.getMe(req.user.sub);
  ApiResponse.success(res, user);
});

const changePassword = asyncHandler(async (req, res) => {
  const { currentPassword, newPassword } = req.body;
  const result = await authService.changePassword(
    req.user.sub,
    currentPassword,
    newPassword
  );
  ApiResponse.success(res, result);
});

module.exports = {
  register,
  login,
  refreshToken,
  logout,
  getMe,
  changePassword
};
```

---

## 4️⃣ MID LEVEL - Auth Middleware

### JWT Authentication

```javascript
// src/middlewares/auth.middleware.js
const tokenService = require('../services/token.service');
const ApiError = require('../utils/ApiError');

const authenticate = (req, res, next) => {
  try {
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      throw ApiError.unauthorized('Access token required');
    }

    const token = authHeader.split(' ')[1];
    const payload = tokenService.verifyAccessToken(token);

    req.user = payload;
    next();
  } catch (error) {
    if (error.name === 'TokenExpiredError') {
      next(ApiError.unauthorized('Token expired'));
    } else if (error.name === 'JsonWebTokenError') {
      next(ApiError.unauthorized('Invalid token'));
    } else {
      next(error);
    }
  }
};

module.exports = authenticate;
```

### Optional Authentication

```javascript
// src/middlewares/optionalAuth.middleware.js
const tokenService = require('../services/token.service');

const optionalAuth = (req, res, next) => {
  try {
    const authHeader = req.headers.authorization;

    if (authHeader && authHeader.startsWith('Bearer ')) {
      const token = authHeader.split(' ')[1];
      const payload = tokenService.verifyAccessToken(token);
      req.user = payload;
    }

    next();
  } catch (error) {
    // Token invalid, but continue without user
    next();
  }
};

module.exports = optionalAuth;
```

---

## 5️⃣ SENIOR LEVEL - Role-Based Access Control (RBAC)

### Role Middleware

```javascript
// src/middlewares/authorize.middleware.js
const ApiError = require('../utils/ApiError');

// Check role
const authorize = (...allowedRoles) => {
  return (req, res, next) => {
    if (!req.user) {
      return next(ApiError.unauthorized('Authentication required'));
    }

    if (!allowedRoles.includes(req.user.role)) {
      return next(
        ApiError.forbidden(
          `Role '${req.user.role}' is not authorized to access this resource`
        )
      );
    }

    next();
  };
};

// Check ownership or role
const authorizeOwnerOrRole = (ownerIdParam = 'id', ...allowedRoles) => {
  return (req, res, next) => {
    if (!req.user) {
      return next(ApiError.unauthorized('Authentication required'));
    }

    const resourceOwnerId = req.params[ownerIdParam];
    const isOwner = req.user.sub === resourceOwnerId;
    const hasRole = allowedRoles.includes(req.user.role);

    if (!isOwner && !hasRole) {
      return next(ApiError.forbidden('Not authorized to access this resource'));
    }

    next();
  };
};

module.exports = { authorize, authorizeOwnerOrRole };
```

### Using in Routes

```javascript
// src/routes/user.routes.js
const express = require('express');
const router = express.Router();
const userController = require('../controllers/user.controller');
const authenticate = require('../middlewares/auth.middleware');
const { authorize, authorizeOwnerOrRole } = require('../middlewares/authorize.middleware');

// Public routes
router.get('/', userController.getUsers);
router.get('/:id', userController.getUser);

// Protected routes - any authenticated user
router.use(authenticate);

// User can update their own profile, Admin can update anyone
router.put('/:id', authorizeOwnerOrRole('id', 'ADMIN'), userController.updateUser);

// Admin only routes
router.delete('/:id', authorize('ADMIN'), userController.deleteUser);
router.post('/', authorize('ADMIN'), userController.createUser);

module.exports = router;
```

### Permission-Based Access

```javascript
// src/config/permissions.js
const PERMISSIONS = {
  // Users
  USER_READ: 'user:read',
  USER_CREATE: 'user:create',
  USER_UPDATE: 'user:update',
  USER_DELETE: 'user:delete',
  
  // Posts
  POST_READ: 'post:read',
  POST_CREATE: 'post:create',
  POST_UPDATE: 'post:update',
  POST_DELETE: 'post:delete',
  POST_PUBLISH: 'post:publish'
};

const ROLE_PERMISSIONS = {
  USER: [
    PERMISSIONS.USER_READ,
    PERMISSIONS.POST_READ,
    PERMISSIONS.POST_CREATE
  ],
  MODERATOR: [
    PERMISSIONS.USER_READ,
    PERMISSIONS.POST_READ,
    PERMISSIONS.POST_CREATE,
    PERMISSIONS.POST_UPDATE,
    PERMISSIONS.POST_DELETE
  ],
  ADMIN: Object.values(PERMISSIONS) // All permissions
};

module.exports = { PERMISSIONS, ROLE_PERMISSIONS };
```

```javascript
// src/middlewares/permission.middleware.js
const { ROLE_PERMISSIONS } = require('../config/permissions');
const ApiError = require('../utils/ApiError');

const hasPermission = (...requiredPermissions) => {
  return (req, res, next) => {
    if (!req.user) {
      return next(ApiError.unauthorized('Authentication required'));
    }

    const userPermissions = ROLE_PERMISSIONS[req.user.role] || [];

    const hasAllPermissions = requiredPermissions.every(permission =>
      userPermissions.includes(permission)
    );

    if (!hasAllPermissions) {
      return next(
        ApiError.forbidden('You do not have permission to perform this action')
      );
    }

    next();
  };
};

module.exports = hasPermission;
```

```javascript
// Usage in routes
const hasPermission = require('../middlewares/permission.middleware');
const { PERMISSIONS } = require('../config/permissions');

router.post('/posts', 
  authenticate,
  hasPermission(PERMISSIONS.POST_CREATE),
  postController.create
);

router.post('/posts/:id/publish',
  authenticate,
  hasPermission(PERMISSIONS.POST_PUBLISH),
  postController.publish
);
```

---

## 6️⃣ SENIOR LEVEL - Auth Routes

### Complete Auth Routes

```javascript
// src/routes/auth.routes.js
const express = require('express');
const router = express.Router();
const authController = require('../controllers/auth.controller');
const authenticate = require('../middlewares/auth.middleware');
const validate = require('../middlewares/validate.middleware');
const { authLimiter } = require('../middlewares/rateLimiter.middleware');
const {
  registerSchema,
  loginSchema,
  refreshTokenSchema,
  changePasswordSchema
} = require('../validations/auth.validation');

// Public routes with rate limiting
router.post('/register', authLimiter, validate(registerSchema), authController.register);
router.post('/login', authLimiter, validate(loginSchema), authController.login);
router.post('/refresh-token', validate(refreshTokenSchema), authController.refreshToken);

// Protected routes
router.use(authenticate);
router.get('/me', authController.getMe);
router.post('/logout', authController.logout);
router.post('/change-password', validate(changePasswordSchema), authController.changePassword);

module.exports = router;
```

### Auth Validation

```javascript
// src/validations/auth.validation.js
const Joi = require('joi');

const registerSchema = Joi.object({
  name: Joi.string().min(2).max(50).required(),
  email: Joi.string().email().required(),
  password: Joi.string()
    .min(8)
    .pattern(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/)
    .required()
    .messages({
      'string.pattern.base': 'Password must contain uppercase, lowercase and number'
    })
});

const loginSchema = Joi.object({
  email: Joi.string().email().required(),
  password: Joi.string().required()
});

const refreshTokenSchema = Joi.object({
  refreshToken: Joi.string().required()
});

const changePasswordSchema = Joi.object({
  currentPassword: Joi.string().required(),
  newPassword: Joi.string()
    .min(8)
    .pattern(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/)
    .required()
});

module.exports = {
  registerSchema,
  loginSchema,
  refreshTokenSchema,
  changePasswordSchema
};
```

---

## 7️⃣ EXPERT LEVEL - Token Blacklist & Refresh

### Token Blacklist Schema

```prisma
// prisma/schema.prisma
model RefreshToken {
  id        String   @id @default(uuid())
  token     String   @unique
  userId    String
  user      User     @relation(fields: [userId], references: [id], onDelete: Cascade)
  expiresAt DateTime
  createdAt DateTime @default(now())

  @@index([token])
  @@index([userId])
}
```

### Enhanced Token Service

```javascript
// src/services/token.service.js
const jwt = require('jsonwebtoken');
const prisma = require('../lib/prisma');
const ApiError = require('../utils/ApiError');

class TokenService {
  constructor() {
    this.accessSecret = process.env.JWT_ACCESS_SECRET;
    this.refreshSecret = process.env.JWT_REFRESH_SECRET;
    this.accessExpiresIn = '15m';
    this.refreshExpiresIn = '7d';
  }

  generateAccessToken(payload) {
    return jwt.sign(payload, this.accessSecret, {
      expiresIn: this.accessExpiresIn
    });
  }

  generateRefreshToken(payload) {
    return jwt.sign(payload, this.refreshSecret, {
      expiresIn: this.refreshExpiresIn
    });
  }

  async generateTokens(user) {
    const payload = {
      sub: user.id,
      email: user.email,
      role: user.role
    };

    const accessToken = this.generateAccessToken(payload);
    const refreshToken = this.generateRefreshToken(payload);

    // Store refresh token in database
    const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000); // 7 days
    
    await prisma.refreshToken.create({
      data: {
        token: refreshToken,
        userId: user.id,
        expiresAt
      }
    });

    return {
      accessToken,
      refreshToken,
      expiresIn: 900
    };
  }

  verifyAccessToken(token) {
    return jwt.verify(token, this.accessSecret);
  }

  verifyRefreshToken(token) {
    return jwt.verify(token, this.refreshSecret);
  }

  async refreshTokens(refreshToken) {
    // Verify token
    let payload;
    try {
      payload = this.verifyRefreshToken(refreshToken);
    } catch (error) {
      throw ApiError.unauthorized('Invalid refresh token');
    }

    // Check if token exists in database
    const storedToken = await prisma.refreshToken.findUnique({
      where: { token: refreshToken },
      include: { user: true }
    });

    if (!storedToken) {
      throw ApiError.unauthorized('Refresh token not found');
    }

    if (storedToken.expiresAt < new Date()) {
      await prisma.refreshToken.delete({ where: { id: storedToken.id } });
      throw ApiError.unauthorized('Refresh token expired');
    }

    // Delete old refresh token
    await prisma.refreshToken.delete({ where: { id: storedToken.id } });

    // Generate new tokens
    return this.generateTokens(storedToken.user);
  }

  async revokeRefreshToken(refreshToken) {
    await prisma.refreshToken.deleteMany({
      where: { token: refreshToken }
    });
  }

  async revokeAllUserTokens(userId) {
    await prisma.refreshToken.deleteMany({
      where: { userId }
    });
  }

  // Clean up expired tokens (run as cron job)
  async cleanupExpiredTokens() {
    const result = await prisma.refreshToken.deleteMany({
      where: {
        expiresAt: { lt: new Date() }
      }
    });
    console.log(`Cleaned up ${result.count} expired tokens`);
  }
}

module.exports = new TokenService();
```

---

## 📊 Auth Response Examples

### Register Response

```json
{
  "success": true,
  "message": "Registration successful",
  "data": {
    "user": {
      "id": "uuid",
      "email": "john@example.com",
      "name": "John Doe",
      "role": "USER",
      "createdAt": "2024-01-15T10:30:00.000Z"
    },
    "accessToken": "eyJhbGciOiJIUzI1NiIs...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIs...",
    "expiresIn": 900
  }
}
```

### Login Response

```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "user": {
      "id": "uuid",
      "email": "john@example.com",
      "name": "John Doe",
      "role": "USER"
    },
    "accessToken": "eyJhbGciOiJIUzI1NiIs...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIs...",
    "expiresIn": 900
  }
}
```

---

## 💡 Summary

| Level | Focus |
|-------|-------|
| **Junior** | Password hashing, JWT basics |
| **Mid** | Auth service, Auth controller |
| **Mid-Senior** | Auth middleware, Protected routes |
| **Senior** | RBAC, Permissions |
| **Expert** | Token blacklist, Refresh rotation |

**Best Practices:**
- ✅ Hash passwords dengan bcrypt (12+ rounds)
- ✅ Short-lived access tokens (15m)
- ✅ Long-lived refresh tokens (7d)
- ✅ Store refresh tokens di database
- ✅ Rotate refresh tokens
- ✅ Rate limit auth endpoints
- ❌ Don't store passwords in plain text
- ❌ Don't put sensitive data in JWT
- ❌ Don't use same secret for access & refresh
