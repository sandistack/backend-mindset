# 🧪 TESTING - Testing di Express (Junior → Senior)

Dokumentasi lengkap tentang testing di Express.js - unit tests, integration tests, dan mocking.

---

## 🎯 Testing Pyramid

```
        /\
       /  \      E2E Tests (few)
      /----\     
     /      \    Integration Tests
    /--------\   
   /          \  Unit Tests (many)
  /------------\

Tools:
- Jest (test runner & assertions)
- Supertest (HTTP testing)
- Faker (fake data)
- jest-mock-extended (mocking)
```

---

## 1️⃣ JUNIOR LEVEL - Setup Jest

### Installation

```bash
npm install -D jest @types/jest
npm install -D supertest @types/supertest
npm install -D @faker-js/faker
```

### Jest Configuration

```javascript
// jest.config.js
module.exports = {
  testEnvironment: 'node',
  testMatch: ['**/__tests__/**/*.test.js', '**/*.test.js'],
  collectCoverageFrom: [
    'src/**/*.js',
    '!src/index.js',
    '!src/**/*.test.js'
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  },
  setupFilesAfterEnv: ['./jest.setup.js'],
  testTimeout: 10000,
  verbose: true
};
```

```javascript
// jest.setup.js
jest.setTimeout(10000);

// Global cleanup
afterAll(async () => {
  // Close connections, etc.
});
```

### Package.json Scripts

```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:unit": "jest --testPathPattern=unit",
    "test:integration": "jest --testPathPattern=integration"
  }
}
```

---

## 2️⃣ JUNIOR LEVEL - Basic Unit Tests

### Testing Pure Functions

```javascript
// src/utils/helpers.js
const formatPrice = (price) => {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR'
  }).format(price);
};

const slugify = (text) => {
  return text
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '');
};

const paginate = (page, limit, total) => {
  const totalPages = Math.ceil(total / limit);
  return {
    page,
    limit,
    total,
    totalPages,
    hasNext: page < totalPages,
    hasPrev: page > 1
  };
};

module.exports = { formatPrice, slugify, paginate };
```

```javascript
// src/utils/__tests__/helpers.test.js
const { formatPrice, slugify, paginate } = require('../helpers');

describe('Helper Functions', () => {
  describe('formatPrice', () => {
    it('should format price to IDR currency', () => {
      expect(formatPrice(100000)).toBe('Rp 100.000');
      expect(formatPrice(1500000)).toBe('Rp 1.500.000');
    });

    it('should handle zero', () => {
      expect(formatPrice(0)).toBe('Rp 0');
    });

    it('should handle decimals', () => {
      expect(formatPrice(100000.5)).toContain('100.000');
    });
  });

  describe('slugify', () => {
    it('should convert text to slug', () => {
      expect(slugify('Hello World')).toBe('hello-world');
      expect(slugify('Hello  World')).toBe('hello-world');
    });

    it('should remove special characters', () => {
      expect(slugify('Hello! World?')).toBe('hello-world');
    });

    it('should handle already slugified text', () => {
      expect(slugify('hello-world')).toBe('hello-world');
    });

    it('should trim whitespace', () => {
      expect(slugify('  Hello World  ')).toBe('hello-world');
    });
  });

  describe('paginate', () => {
    it('should calculate pagination correctly', () => {
      const result = paginate(1, 10, 100);
      
      expect(result).toEqual({
        page: 1,
        limit: 10,
        total: 100,
        totalPages: 10,
        hasNext: true,
        hasPrev: false
      });
    });

    it('should handle last page', () => {
      const result = paginate(10, 10, 100);
      
      expect(result.hasNext).toBe(false);
      expect(result.hasPrev).toBe(true);
    });

    it('should handle single page', () => {
      const result = paginate(1, 10, 5);
      
      expect(result.totalPages).toBe(1);
      expect(result.hasNext).toBe(false);
      expect(result.hasPrev).toBe(false);
    });
  });
});
```

---

## 3️⃣ MID LEVEL - Testing Services with Mocks

### Mocking Prisma

```javascript
// src/__mocks__/prisma.js
const prisma = {
  user: {
    findUnique: jest.fn(),
    findMany: jest.fn(),
    create: jest.fn(),
    update: jest.fn(),
    delete: jest.fn(),
    count: jest.fn()
  },
  post: {
    findUnique: jest.fn(),
    findMany: jest.fn(),
    create: jest.fn(),
    update: jest.fn(),
    delete: jest.fn(),
    count: jest.fn()
  },
  $transaction: jest.fn()
};

module.exports = prisma;
```

### Testing User Service

```javascript
// src/services/__tests__/user.service.test.js
const userService = require('../user.service');
const prisma = require('../../lib/prisma');
const bcrypt = require('bcrypt');
const ApiError = require('../../utils/ApiError');

// Mock Prisma
jest.mock('../../lib/prisma');

// Mock bcrypt
jest.mock('bcrypt', () => ({
  hash: jest.fn(() => 'hashed_password'),
  compare: jest.fn(() => true)
}));

describe('UserService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('findById', () => {
    it('should return user when found', async () => {
      const mockUser = {
        id: '1',
        name: 'John',
        email: 'john@example.com',
        role: 'USER'
      };

      prisma.user.findUnique.mockResolvedValue(mockUser);

      const result = await userService.findById('1');

      expect(result).toEqual(mockUser);
      expect(prisma.user.findUnique).toHaveBeenCalledWith({
        where: { id: '1' },
        select: expect.any(Object)
      });
    });

    it('should throw NotFound when user not exists', async () => {
      prisma.user.findUnique.mockResolvedValue(null);

      await expect(userService.findById('999'))
        .rejects
        .toThrow(ApiError);
    });
  });

  describe('create', () => {
    const userData = {
      email: 'new@example.com',
      name: 'New User',
      password: 'password123'
    };

    it('should create user successfully', async () => {
      prisma.user.findUnique.mockResolvedValue(null); // Email not taken
      prisma.user.create.mockResolvedValue({
        id: '1',
        ...userData,
        password: 'hashed_password'
      });

      const result = await userService.create(userData);

      expect(result.email).toBe(userData.email);
      expect(bcrypt.hash).toHaveBeenCalledWith('password123', 12);
      expect(prisma.user.create).toHaveBeenCalled();
    });

    it('should throw Conflict when email exists', async () => {
      prisma.user.findUnique.mockResolvedValue({ id: '1', email: userData.email });

      await expect(userService.create(userData))
        .rejects
        .toThrow(ApiError);
    });
  });

  describe('findAll', () => {
    it('should return paginated users', async () => {
      const mockUsers = [
        { id: '1', name: 'User 1' },
        { id: '2', name: 'User 2' }
      ];

      prisma.user.findMany.mockResolvedValue(mockUsers);
      prisma.user.count.mockResolvedValue(2);

      const result = await userService.findAll({ page: 1, limit: 10 });

      expect(result.data).toEqual(mockUsers);
      expect(result.pagination.total).toBe(2);
    });

    it('should apply search filter', async () => {
      prisma.user.findMany.mockResolvedValue([]);
      prisma.user.count.mockResolvedValue(0);

      await userService.findAll({ page: 1, limit: 10, search: 'john' });

      expect(prisma.user.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: expect.objectContaining({
            OR: expect.arrayContaining([
              { name: expect.any(Object) },
              { email: expect.any(Object) }
            ])
          })
        })
      );
    });
  });
});
```

---

## 4️⃣ MID LEVEL - HTTP Testing with Supertest

### Testing Express App

```javascript
// src/__tests__/app.test.js
const request = require('supertest');
const app = require('../app');

describe('App', () => {
  it('should return 404 for unknown routes', async () => {
    const res = await request(app)
      .get('/api/v1/unknown')
      .expect(404);

    expect(res.body.success).toBe(false);
  });

  it('should have health check endpoint', async () => {
    const res = await request(app)
      .get('/health')
      .expect(200);

    expect(res.body.status).toBe('ok');
  });
});
```

### Testing Routes

```javascript
// src/routes/__tests__/user.routes.test.js
const request = require('supertest');
const app = require('../../app');
const prisma = require('../../lib/prisma');
const tokenService = require('../../services/token.service');

jest.mock('../../lib/prisma');

describe('User Routes', () => {
  let authToken;
  
  beforeAll(() => {
    // Generate test token
    authToken = tokenService.generateAccessToken({
      sub: 'user-1',
      email: 'admin@test.com',
      role: 'ADMIN'
    });
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('GET /api/v1/users', () => {
    it('should return users list', async () => {
      const mockUsers = [
        { id: '1', name: 'User 1', email: 'user1@test.com' }
      ];

      prisma.user.findMany.mockResolvedValue(mockUsers);
      prisma.user.count.mockResolvedValue(1);

      const res = await request(app)
        .get('/api/v1/users')
        .expect(200);

      expect(res.body.success).toBe(true);
      expect(res.body.data).toHaveLength(1);
    });

    it('should support pagination', async () => {
      prisma.user.findMany.mockResolvedValue([]);
      prisma.user.count.mockResolvedValue(0);

      const res = await request(app)
        .get('/api/v1/users?page=2&limit=5')
        .expect(200);

      expect(prisma.user.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          skip: 5,
          take: 5
        })
      );
    });
  });

  describe('GET /api/v1/users/:id', () => {
    it('should return user by id', async () => {
      const mockUser = { id: '1', name: 'John', email: 'john@test.com' };
      prisma.user.findUnique.mockResolvedValue(mockUser);

      const res = await request(app)
        .get('/api/v1/users/1')
        .expect(200);

      expect(res.body.data.name).toBe('John');
    });

    it('should return 404 for non-existent user', async () => {
      prisma.user.findUnique.mockResolvedValue(null);

      const res = await request(app)
        .get('/api/v1/users/999')
        .expect(404);

      expect(res.body.success).toBe(false);
    });
  });

  describe('POST /api/v1/users', () => {
    const newUser = {
      name: 'New User',
      email: 'new@test.com',
      password: 'Password123!'
    };

    it('should create user when authenticated as admin', async () => {
      prisma.user.findUnique.mockResolvedValue(null);
      prisma.user.create.mockResolvedValue({ id: '1', ...newUser });

      const res = await request(app)
        .post('/api/v1/users')
        .set('Authorization', `Bearer ${authToken}`)
        .send(newUser)
        .expect(201);

      expect(res.body.data.email).toBe(newUser.email);
    });

    it('should reject without auth token', async () => {
      await request(app)
        .post('/api/v1/users')
        .send(newUser)
        .expect(401);
    });

    it('should validate input', async () => {
      const res = await request(app)
        .post('/api/v1/users')
        .set('Authorization', `Bearer ${authToken}`)
        .send({ email: 'invalid' })
        .expect(400);

      expect(res.body.success).toBe(false);
      expect(res.body.errors).toBeDefined();
    });
  });

  describe('PUT /api/v1/users/:id', () => {
    it('should update user', async () => {
      const mockUser = { id: '1', name: 'John', email: 'john@test.com' };
      prisma.user.findUnique.mockResolvedValue(mockUser);
      prisma.user.update.mockResolvedValue({ ...mockUser, name: 'John Updated' });

      const res = await request(app)
        .put('/api/v1/users/1')
        .set('Authorization', `Bearer ${authToken}`)
        .send({ name: 'John Updated' })
        .expect(200);

      expect(res.body.data.name).toBe('John Updated');
    });
  });

  describe('DELETE /api/v1/users/:id', () => {
    it('should delete user', async () => {
      prisma.user.findUnique.mockResolvedValue({ id: '1' });
      prisma.user.delete.mockResolvedValue({ id: '1' });

      await request(app)
        .delete('/api/v1/users/1')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(204);
    });
  });
});
```

---

## 5️⃣ SENIOR LEVEL - Testing Auth

### Auth Routes Testing

```javascript
// src/routes/__tests__/auth.routes.test.js
const request = require('supertest');
const app = require('../../app');
const prisma = require('../../lib/prisma');
const bcrypt = require('bcrypt');

jest.mock('../../lib/prisma');

describe('Auth Routes', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('POST /api/v1/auth/register', () => {
    const validUser = {
      name: 'John Doe',
      email: 'john@example.com',
      password: 'Password123!'
    };

    it('should register new user', async () => {
      prisma.user.findUnique.mockResolvedValue(null);
      prisma.user.create.mockResolvedValue({
        id: '1',
        ...validUser,
        role: 'USER'
      });

      const res = await request(app)
        .post('/api/v1/auth/register')
        .send(validUser)
        .expect(201);

      expect(res.body.success).toBe(true);
      expect(res.body.data.accessToken).toBeDefined();
      expect(res.body.data.refreshToken).toBeDefined();
      expect(res.body.data.user.email).toBe(validUser.email);
    });

    it('should reject duplicate email', async () => {
      prisma.user.findUnique.mockResolvedValue({ id: '1', email: validUser.email });

      const res = await request(app)
        .post('/api/v1/auth/register')
        .send(validUser)
        .expect(409);

      expect(res.body.message).toContain('already registered');
    });

    it('should validate password requirements', async () => {
      const res = await request(app)
        .post('/api/v1/auth/register')
        .send({ ...validUser, password: 'weak' })
        .expect(400);

      expect(res.body.errors).toBeDefined();
    });
  });

  describe('POST /api/v1/auth/login', () => {
    const credentials = {
      email: 'john@example.com',
      password: 'Password123!'
    };

    it('should login with valid credentials', async () => {
      const hashedPassword = await bcrypt.hash(credentials.password, 12);
      
      prisma.user.findUnique.mockResolvedValue({
        id: '1',
        email: credentials.email,
        password: hashedPassword,
        role: 'USER'
      });

      const res = await request(app)
        .post('/api/v1/auth/login')
        .send(credentials)
        .expect(200);

      expect(res.body.data.accessToken).toBeDefined();
    });

    it('should reject invalid email', async () => {
      prisma.user.findUnique.mockResolvedValue(null);

      const res = await request(app)
        .post('/api/v1/auth/login')
        .send(credentials)
        .expect(401);

      expect(res.body.message).toContain('Invalid');
    });

    it('should reject invalid password', async () => {
      prisma.user.findUnique.mockResolvedValue({
        id: '1',
        email: credentials.email,
        password: 'different_hash',
        role: 'USER'
      });

      // bcrypt.compare will return false for wrong password
      const res = await request(app)
        .post('/api/v1/auth/login')
        .send({ ...credentials, password: 'WrongPassword123!' })
        .expect(401);

      expect(res.body.message).toContain('Invalid');
    });
  });

  describe('GET /api/v1/auth/me', () => {
    it('should return current user with valid token', async () => {
      const mockUser = { id: '1', name: 'John', email: 'john@example.com', role: 'USER' };
      prisma.user.findUnique.mockResolvedValue(mockUser);

      // Get token first
      prisma.user.findUnique.mockResolvedValueOnce(null);
      prisma.user.create.mockResolvedValue(mockUser);

      const registerRes = await request(app)
        .post('/api/v1/auth/register')
        .send({ name: 'John', email: 'john@example.com', password: 'Password123!' });

      const token = registerRes.body.data.accessToken;

      prisma.user.findUnique.mockResolvedValue(mockUser);

      const res = await request(app)
        .get('/api/v1/auth/me')
        .set('Authorization', `Bearer ${token}`)
        .expect(200);

      expect(res.body.data.email).toBe('john@example.com');
    });

    it('should reject without token', async () => {
      await request(app)
        .get('/api/v1/auth/me')
        .expect(401);
    });
  });
});
```

---

## 6️⃣ SENIOR LEVEL - Integration Testing

### Database Integration Tests

```javascript
// src/__tests__/integration/user.integration.test.js
const request = require('supertest');
const app = require('../../app');
const prisma = require('../../lib/prisma');

// Use real database (test database)
// Dont mock prisma for integration tests

describe('User Integration Tests', () => {
  beforeAll(async () => {
    // Connect to test database
    await prisma.$connect();
  });

  beforeEach(async () => {
    // Clean database before each test
    await prisma.user.deleteMany();
  });

  afterAll(async () => {
    await prisma.$disconnect();
  });

  describe('User CRUD', () => {
    it('should create and retrieve user', async () => {
      // Create user
      const createRes = await request(app)
        .post('/api/v1/auth/register')
        .send({
          name: 'Integration Test User',
          email: 'integration@test.com',
          password: 'Password123!'
        })
        .expect(201);

      const userId = createRes.body.data.user.id;
      const token = createRes.body.data.accessToken;

      // Retrieve user
      const getRes = await request(app)
        .get(`/api/v1/users/${userId}`)
        .set('Authorization', `Bearer ${token}`)
        .expect(200);

      expect(getRes.body.data.email).toBe('integration@test.com');

      // Verify in database
      const dbUser = await prisma.user.findUnique({
        where: { id: userId }
      });
      expect(dbUser).toBeDefined();
      expect(dbUser.email).toBe('integration@test.com');
    });

    it('should update user', async () => {
      // Create user first
      const user = await prisma.user.create({
        data: {
          name: 'Original Name',
          email: 'update@test.com',
          password: 'hashedpassword'
        }
      });

      // Get admin token
      const admin = await prisma.user.create({
        data: {
          name: 'Admin',
          email: 'admin@test.com',
          password: 'hashedpassword',
          role: 'ADMIN'
        }
      });

      const tokenService = require('../../services/token.service');
      const token = tokenService.generateAccessToken({
        sub: admin.id,
        email: admin.email,
        role: admin.role
      });

      // Update
      const res = await request(app)
        .put(`/api/v1/users/${user.id}`)
        .set('Authorization', `Bearer ${token}`)
        .send({ name: 'Updated Name' })
        .expect(200);

      expect(res.body.data.name).toBe('Updated Name');

      // Verify in database
      const dbUser = await prisma.user.findUnique({
        where: { id: user.id }
      });
      expect(dbUser.name).toBe('Updated Name');
    });
  });
});
```

---

## 7️⃣ EXPERT LEVEL - Test Helpers & Factories

### Test Factory

```javascript
// src/__tests__/factories/user.factory.js
const { faker } = require('@faker-js/faker');
const bcrypt = require('bcrypt');

const createUserData = (overrides = {}) => ({
  name: faker.person.fullName(),
  email: faker.internet.email().toLowerCase(),
  password: 'Password123!',
  role: 'USER',
  ...overrides
});

const createUser = async (prisma, overrides = {}) => {
  const data = createUserData(overrides);
  const hashedPassword = await bcrypt.hash(data.password, 12);
  
  return prisma.user.create({
    data: {
      ...data,
      password: hashedPassword
    }
  });
};

const createUsers = async (prisma, count = 5, overrides = {}) => {
  const users = [];
  for (let i = 0; i < count; i++) {
    users.push(await createUser(prisma, overrides));
  }
  return users;
};

module.exports = { createUserData, createUser, createUsers };
```

### Test Helpers

```javascript
// src/__tests__/helpers/auth.helper.js
const request = require('supertest');
const app = require('../../app');
const tokenService = require('../../services/token.service');

const getAuthToken = async (user) => {
  return tokenService.generateAccessToken({
    sub: user.id,
    email: user.email,
    role: user.role
  });
};

const authenticatedRequest = async (user) => {
  const token = await getAuthToken(user);
  
  return {
    get: (url) => request(app).get(url).set('Authorization', `Bearer ${token}`),
    post: (url) => request(app).post(url).set('Authorization', `Bearer ${token}`),
    put: (url) => request(app).put(url).set('Authorization', `Bearer ${token}`),
    delete: (url) => request(app).delete(url).set('Authorization', `Bearer ${token}`)
  };
};

module.exports = { getAuthToken, authenticatedRequest };
```

### Using Factories & Helpers

```javascript
// src/__tests__/integration/posts.integration.test.js
const { createUser, createUsers } = require('../factories/user.factory');
const { authenticatedRequest } = require('../helpers/auth.helper');
const prisma = require('../../lib/prisma');

describe('Posts Integration', () => {
  let admin;
  let regularUser;
  let adminRequest;

  beforeAll(async () => {
    await prisma.$connect();
  });

  beforeEach(async () => {
    await prisma.post.deleteMany();
    await prisma.user.deleteMany();

    admin = await createUser(prisma, { role: 'ADMIN' });
    regularUser = await createUser(prisma);
    adminRequest = await authenticatedRequest(admin);
  });

  afterAll(async () => {
    await prisma.$disconnect();
  });

  it('should create post as authenticated user', async () => {
    const userRequest = await authenticatedRequest(regularUser);

    const res = await userRequest.post('/api/v1/posts')
      .send({ title: 'Test Post', content: 'Test content' })
      .expect(201);

    expect(res.body.data.title).toBe('Test Post');
    expect(res.body.data.authorId).toBe(regularUser.id);
  });

  it('admin can delete any post', async () => {
    // Create post as regular user
    const post = await prisma.post.create({
      data: {
        title: 'User Post',
        content: 'Content',
        authorId: regularUser.id
      }
    });

    // Admin deletes it
    await adminRequest.delete(`/api/v1/posts/${post.id}`)
      .expect(204);

    const deletedPost = await prisma.post.findUnique({
      where: { id: post.id }
    });
    expect(deletedPost).toBeNull();
  });
});
```

---

## 📊 Testing Cheat Sheet

### Jest Matchers

| Matcher | Description |
|---------|-------------|
| `toBe(value)` | Exact equality |
| `toEqual(value)` | Deep equality |
| `toBeDefined()` | Not undefined |
| `toBeNull()` | Is null |
| `toBeTruthy()` | Truthy value |
| `toContain(item)` | Array/string contains |
| `toThrow()` | Throws error |
| `toHaveLength(n)` | Array/string length |
| `toHaveBeenCalled()` | Mock was called |
| `toHaveBeenCalledWith()` | Mock called with args |

### Mock Functions

```javascript
// Create mock
const mockFn = jest.fn();
const mockFn = jest.fn(() => 'return value');

// Mock return value
mockFn.mockReturnValue('value');
mockFn.mockResolvedValue('async value');
mockFn.mockRejectedValue(new Error('error'));

// Verify calls
expect(mockFn).toHaveBeenCalled();
expect(mockFn).toHaveBeenCalledTimes(2);
expect(mockFn).toHaveBeenCalledWith(arg1, arg2);

// Clear mocks
jest.clearAllMocks();
jest.resetAllMocks();
```

### Test Structure

```javascript
describe('Feature', () => {
  beforeAll(() => { /* Run once before all tests */ });
  beforeEach(() => { /* Run before each test */ });
  afterEach(() => { /* Run after each test */ });
  afterAll(() => { /* Run once after all tests */ });

  describe('Sub-feature', () => {
    it('should do something', () => {
      // Arrange
      // Act
      // Assert
    });

    it.skip('skip this test', () => {});
    it.only('run only this test', () => {});
  });
});
```

---

## 💡 Summary

| Level | Focus |
|-------|-------|
| **Junior** | Jest setup, basic unit tests |
| **Mid** | Service mocking, HTTP tests |
| **Senior** | Auth testing, integration tests |
| **Expert** | Factories, helpers, test patterns |

**Best Practices:**
- ✅ Test behavior, not implementation
- ✅ Use factories for test data
- ✅ Clean up after tests
- ✅ Aim for 80%+ coverage
- ✅ Test error cases
- ✅ Use descriptive test names
- ❌ Don't test external libraries
- ❌ Don't share state between tests
- ❌ Don't test private methods
