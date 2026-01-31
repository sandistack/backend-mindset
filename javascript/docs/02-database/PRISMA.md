# 🗄️ DATABASE - Prisma & Database di Express (Junior → Senior)

Dokumentasi lengkap tentang database operations di Express menggunakan Prisma ORM.

---

## 🎯 Kenapa Prisma?

```
Prisma = Modern ORM untuk Node.js/TypeScript

Keunggulan:
✅ Type-safe queries
✅ Auto-generated client
✅ Migrations
✅ Prisma Studio (GUI)
✅ Excellent TypeScript support
```

---

## 1️⃣ JUNIOR LEVEL - Setup Prisma

### Installation

```bash
npm install prisma @prisma/client
npx prisma init
```

### Prisma Schema

```prisma
// prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

// Models
model User {
  id        String   @id @default(uuid())
  email     String   @unique
  name      String
  password  String
  role      Role     @default(USER)
  posts     Post[]
  profile   Profile?
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}

model Profile {
  id     String  @id @default(uuid())
  bio    String?
  avatar String?
  userId String  @unique
  user   User    @relation(fields: [userId], references: [id], onDelete: Cascade)
}

model Post {
  id        String     @id @default(uuid())
  title     String
  content   String?
  published Boolean    @default(false)
  authorId  String
  author    User       @relation(fields: [authorId], references: [id], onDelete: Cascade)
  categories Category[]
  createdAt DateTime   @default(now())
  updatedAt DateTime   @updatedAt
}

model Category {
  id    String @id @default(uuid())
  name  String @unique
  posts Post[]
}

enum Role {
  USER
  ADMIN
  MODERATOR
}
```

### Environment

```bash
# .env
DATABASE_URL="postgresql://user:password@localhost:5432/mydb?schema=public"
```

### Generate & Migrate

```bash
# Generate Prisma Client
npx prisma generate

# Create migration
npx prisma migrate dev --name init

# Apply migrations (production)
npx prisma migrate deploy

# Open Prisma Studio
npx prisma studio
```

---

## 2️⃣ JUNIOR LEVEL - Basic CRUD

### Prisma Client Setup

```javascript
// src/lib/prisma.js
const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient({
  log: process.env.NODE_ENV === 'development' 
    ? ['query', 'info', 'warn', 'error']
    : ['error']
});

module.exports = prisma;
```

### Create (INSERT)

```javascript
const prisma = require('../lib/prisma');

// Create single record
const user = await prisma.user.create({
  data: {
    email: 'john@example.com',
    name: 'John Doe',
    password: 'hashedPassword'
  }
});

// Create with relation
const userWithProfile = await prisma.user.create({
  data: {
    email: 'jane@example.com',
    name: 'Jane Doe',
    password: 'hashedPassword',
    profile: {
      create: {
        bio: 'Hello World',
        avatar: 'https://...'
      }
    }
  },
  include: {
    profile: true
  }
});

// Create many
const users = await prisma.user.createMany({
  data: [
    { email: 'user1@example.com', name: 'User 1', password: 'hash1' },
    { email: 'user2@example.com', name: 'User 2', password: 'hash2' }
  ],
  skipDuplicates: true
});
```

### Read (SELECT)

```javascript
// Find unique
const user = await prisma.user.findUnique({
  where: { id: 'uuid' }
});

const userByEmail = await prisma.user.findUnique({
  where: { email: 'john@example.com' }
});

// Find first
const admin = await prisma.user.findFirst({
  where: { role: 'ADMIN' }
});

// Find many
const users = await prisma.user.findMany();

// With conditions
const activeUsers = await prisma.user.findMany({
  where: {
    role: 'USER',
    email: { contains: '@gmail.com' }
  }
});

// With relations
const userWithPosts = await prisma.user.findUnique({
  where: { id: 'uuid' },
  include: {
    posts: true,
    profile: true
  }
});

// Select specific fields
const userNames = await prisma.user.findMany({
  select: {
    id: true,
    name: true,
    email: true
  }
});
```

### Update

```javascript
// Update single
const user = await prisma.user.update({
  where: { id: 'uuid' },
  data: { name: 'Updated Name' }
});

// Update many
const result = await prisma.user.updateMany({
  where: { role: 'USER' },
  data: { role: 'MODERATOR' }
});
console.log(`Updated ${result.count} users`);

// Upsert (update or create)
const user = await prisma.user.upsert({
  where: { email: 'john@example.com' },
  update: { name: 'John Updated' },
  create: {
    email: 'john@example.com',
    name: 'John',
    password: 'hash'
  }
});
```

### Delete

```javascript
// Delete single
const user = await prisma.user.delete({
  where: { id: 'uuid' }
});

// Delete many
const result = await prisma.user.deleteMany({
  where: { role: 'USER' }
});

// Delete all
await prisma.user.deleteMany();
```

---

## 3️⃣ MID LEVEL - Advanced Queries

### Filtering

```javascript
// Multiple conditions (AND)
const users = await prisma.user.findMany({
  where: {
    AND: [
      { role: 'USER' },
      { email: { contains: '@gmail.com' } }
    ]
  }
});

// OR conditions
const users = await prisma.user.findMany({
  where: {
    OR: [
      { role: 'ADMIN' },
      { role: 'MODERATOR' }
    ]
  }
});

// NOT
const users = await prisma.user.findMany({
  where: {
    NOT: { role: 'USER' }
  }
});

// String filters
const users = await prisma.user.findMany({
  where: {
    name: { contains: 'john', mode: 'insensitive' },
    email: { startsWith: 'admin' },
    // endsWith, equals, not
  }
});

// Number/Date filters
const posts = await prisma.post.findMany({
  where: {
    createdAt: { gte: new Date('2024-01-01') },
    // gt, lt, lte, gte
  }
});

// In array
const users = await prisma.user.findMany({
  where: {
    role: { in: ['ADMIN', 'MODERATOR'] },
    // notIn
  }
});
```

### Sorting & Pagination

```javascript
// Sorting
const users = await prisma.user.findMany({
  orderBy: { createdAt: 'desc' }
});

// Multiple sort
const users = await prisma.user.findMany({
  orderBy: [
    { role: 'asc' },
    { name: 'asc' }
  ]
});

// Pagination (offset-based)
const page = 1;
const limit = 10;

const users = await prisma.user.findMany({
  skip: (page - 1) * limit,
  take: limit,
  orderBy: { createdAt: 'desc' }
});

const total = await prisma.user.count();

// Cursor-based pagination
const users = await prisma.user.findMany({
  take: 10,
  cursor: { id: 'last-id-from-previous-page' },
  orderBy: { createdAt: 'desc' }
});
```

### Relation Queries

```javascript
// Include all relations
const user = await prisma.user.findUnique({
  where: { id: 'uuid' },
  include: {
    posts: true,
    profile: true
  }
});

// Nested include
const user = await prisma.user.findUnique({
  where: { id: 'uuid' },
  include: {
    posts: {
      include: {
        categories: true
      }
    }
  }
});

// Filter on relations
const users = await prisma.user.findMany({
  where: {
    posts: {
      some: { published: true }
    }
  },
  include: {
    posts: {
      where: { published: true },
      orderBy: { createdAt: 'desc' },
      take: 5
    }
  }
});

// Count relations
const users = await prisma.user.findMany({
  include: {
    _count: {
      select: { posts: true }
    }
  }
});
```

---

## 4️⃣ SENIOR LEVEL - Service Pattern

### User Service

```javascript
// src/services/user.service.js
const prisma = require('../lib/prisma');
const bcrypt = require('bcrypt');
const ApiError = require('../utils/ApiError');

class UserService {
  async findAll({ page = 1, limit = 10, search, role }) {
    const where = {};
    
    if (search) {
      where.OR = [
        { name: { contains: search, mode: 'insensitive' } },
        { email: { contains: search, mode: 'insensitive' } }
      ];
    }
    
    if (role) {
      where.role = role;
    }

    const [users, total] = await Promise.all([
      prisma.user.findMany({
        where,
        skip: (page - 1) * limit,
        take: limit,
        select: {
          id: true,
          name: true,
          email: true,
          role: true,
          createdAt: true,
          _count: { select: { posts: true } }
        },
        orderBy: { createdAt: 'desc' }
      }),
      prisma.user.count({ where })
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
  }

  async findById(id) {
    const user = await prisma.user.findUnique({
      where: { id },
      select: {
        id: true,
        name: true,
        email: true,
        role: true,
        createdAt: true,
        profile: true,
        _count: { select: { posts: true } }
      }
    });

    if (!user) {
      throw ApiError.notFound('User not found');
    }

    return user;
  }

  async findByEmail(email) {
    return prisma.user.findUnique({
      where: { email }
    });
  }

  async create(data) {
    const { email, password, name, role } = data;

    const existingUser = await this.findByEmail(email);
    if (existingUser) {
      throw ApiError.conflict('Email already registered');
    }

    const hashedPassword = await bcrypt.hash(password, 12);

    const user = await prisma.user.create({
      data: {
        email,
        name,
        password: hashedPassword,
        role: role || 'USER'
      },
      select: {
        id: true,
        name: true,
        email: true,
        role: true,
        createdAt: true
      }
    });

    return user;
  }

  async update(id, data) {
    await this.findById(id); // Check exists

    if (data.email) {
      const existingUser = await this.findByEmail(data.email);
      if (existingUser && existingUser.id !== id) {
        throw ApiError.conflict('Email already in use');
      }
    }

    if (data.password) {
      data.password = await bcrypt.hash(data.password, 12);
    }

    return prisma.user.update({
      where: { id },
      data,
      select: {
        id: true,
        name: true,
        email: true,
        role: true,
        updatedAt: true
      }
    });
  }

  async delete(id) {
    await this.findById(id); // Check exists

    return prisma.user.delete({
      where: { id }
    });
  }
}

module.exports = new UserService();
```

### User Controller

```javascript
// src/controllers/user.controller.js
const asyncHandler = require('../utils/asyncHandler');
const ApiResponse = require('../utils/response');
const userService = require('../services/user.service');

const getUsers = asyncHandler(async (req, res) => {
  const { page, limit, search, role } = req.query;
  const result = await userService.findAll({ 
    page: parseInt(page) || 1, 
    limit: parseInt(limit) || 10,
    search,
    role
  });
  ApiResponse.paginated(res, result.data, result.pagination);
});

const getUser = asyncHandler(async (req, res) => {
  const user = await userService.findById(req.params.id);
  ApiResponse.success(res, user);
});

const createUser = asyncHandler(async (req, res) => {
  const user = await userService.create(req.body);
  ApiResponse.created(res, user);
});

const updateUser = asyncHandler(async (req, res) => {
  const user = await userService.update(req.params.id, req.body);
  ApiResponse.success(res, user, 'User updated successfully');
});

const deleteUser = asyncHandler(async (req, res) => {
  await userService.delete(req.params.id);
  ApiResponse.noContent(res);
});

module.exports = {
  getUsers,
  getUser,
  createUser,
  updateUser,
  deleteUser
};
```

---

## 5️⃣ SENIOR LEVEL - Transactions

### Basic Transaction

```javascript
// All or nothing
const result = await prisma.$transaction([
  prisma.user.create({ data: { ... } }),
  prisma.post.create({ data: { ... } }),
  prisma.profile.create({ data: { ... } })
]);
```

### Interactive Transaction

```javascript
// src/services/order.service.js
async createOrder(userId, items) {
  return prisma.$transaction(async (tx) => {
    // Check stock
    for (const item of items) {
      const product = await tx.product.findUnique({
        where: { id: item.productId }
      });
      
      if (!product || product.stock < item.quantity) {
        throw ApiError.badRequest(`Insufficient stock for ${product?.name}`);
      }
    }

    // Create order
    const order = await tx.order.create({
      data: {
        userId,
        status: 'PENDING',
        items: {
          create: items.map(item => ({
            productId: item.productId,
            quantity: item.quantity,
            price: item.price
          }))
        }
      },
      include: { items: true }
    });

    // Update stock
    for (const item of items) {
      await tx.product.update({
        where: { id: item.productId },
        data: {
          stock: { decrement: item.quantity }
        }
      });
    }

    return order;
  });
}

async transferBalance(fromUserId, toUserId, amount) {
  return prisma.$transaction(async (tx) => {
    // Deduct from sender
    const sender = await tx.user.update({
      where: { id: fromUserId },
      data: { balance: { decrement: amount } }
    });

    if (sender.balance < 0) {
      throw ApiError.badRequest('Insufficient balance');
    }

    // Add to receiver
    await tx.user.update({
      where: { id: toUserId },
      data: { balance: { increment: amount } }
    });

    // Create transaction record
    return tx.transaction.create({
      data: {
        fromUserId,
        toUserId,
        amount,
        type: 'TRANSFER'
      }
    });
  }, {
    maxWait: 5000,
    timeout: 10000,
    isolationLevel: 'Serializable'
  });
}
```

---

## 6️⃣ EXPERT LEVEL - Soft Delete & Hooks

### Soft Delete dengan Middleware

```javascript
// src/lib/prisma.js
const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient().$extends({
  query: {
    user: {
      // Exclude soft-deleted records
      async findMany({ args, query }) {
        args.where = { ...args.where, deletedAt: null };
        return query(args);
      },
      async findFirst({ args, query }) {
        args.where = { ...args.where, deletedAt: null };
        return query(args);
      },
      async findUnique({ args, query }) {
        args.where = { ...args.where, deletedAt: null };
        return query(args);
      },
      // Soft delete instead of hard delete
      async delete({ args, query }) {
        return prisma.user.update({
          ...args,
          data: { deletedAt: new Date() }
        });
      },
      async deleteMany({ args, query }) {
        return prisma.user.updateMany({
          ...args,
          data: { deletedAt: new Date() }
        });
      }
    }
  }
});

module.exports = prisma;
```

### Schema dengan Soft Delete

```prisma
model User {
  id        String    @id @default(uuid())
  email     String    @unique
  name      String
  deletedAt DateTime?
  createdAt DateTime  @default(now())
  updatedAt DateTime  @updatedAt

  @@index([deletedAt])
}
```

### Custom Methods Extension

```javascript
const prisma = new PrismaClient().$extends({
  model: {
    user: {
      async findByEmailWithPassword(email) {
        return prisma.user.findUnique({
          where: { email }
        });
      },
      async softDelete(id) {
        return prisma.user.update({
          where: { id },
          data: { deletedAt: new Date() }
        });
      },
      async restore(id) {
        return prisma.user.update({
          where: { id },
          data: { deletedAt: null }
        });
      }
    }
  }
});

// Usage
const user = await prisma.user.findByEmailWithPassword('john@example.com');
await prisma.user.softDelete('uuid');
await prisma.user.restore('uuid');
```

---

## 7️⃣ EXPERT LEVEL - Raw Queries

### Raw SQL

```javascript
// Raw query
const users = await prisma.$queryRaw`
  SELECT * FROM users WHERE role = ${role}
`;

// With template literal
const searchTerm = `%${search}%`;
const users = await prisma.$queryRaw`
  SELECT id, name, email 
  FROM users 
  WHERE name ILIKE ${searchTerm}
  ORDER BY created_at DESC
  LIMIT ${limit} OFFSET ${offset}
`;

// Execute (INSERT, UPDATE, DELETE)
await prisma.$executeRaw`
  UPDATE users SET last_login = NOW() WHERE id = ${userId}
`;

// Aggregation
const stats = await prisma.$queryRaw`
  SELECT 
    role,
    COUNT(*) as count,
    DATE_TRUNC('month', created_at) as month
  FROM users
  GROUP BY role, month
  ORDER BY month DESC
`;
```

### Aggregations

```javascript
// Count
const count = await prisma.user.count({
  where: { role: 'USER' }
});

// Aggregate
const result = await prisma.order.aggregate({
  _sum: { total: true },
  _avg: { total: true },
  _min: { total: true },
  _max: { total: true },
  _count: true,
  where: { status: 'COMPLETED' }
});

// Group by
const usersByRole = await prisma.user.groupBy({
  by: ['role'],
  _count: true,
  orderBy: {
    _count: { role: 'desc' }
  }
});

// Group with having
const activeUsers = await prisma.user.groupBy({
  by: ['role'],
  _count: { id: true },
  having: {
    id: { _count: { gt: 10 } }
  }
});
```

---

## 📊 Prisma Cheat Sheet

### Schema Types

| Prisma Type | PostgreSQL | Description |
|-------------|------------|-------------|
| `String` | VARCHAR | String |
| `Int` | INTEGER | Integer |
| `Float` | FLOAT | Float |
| `Boolean` | BOOLEAN | Boolean |
| `DateTime` | TIMESTAMP | Date/time |
| `Json` | JSONB | JSON |
| `BigInt` | BIGINT | Large integer |
| `Decimal` | DECIMAL | Decimal |

### Attributes

| Attribute | Description |
|-----------|-------------|
| `@id` | Primary key |
| `@unique` | Unique constraint |
| `@default()` | Default value |
| `@updatedAt` | Auto-update timestamp |
| `@relation()` | Define relation |
| `@@index()` | Create index |
| `@@unique()` | Compound unique |

### Prisma CLI

```bash
npx prisma init          # Initialize Prisma
npx prisma generate      # Generate client
npx prisma migrate dev   # Create migration
npx prisma migrate deploy # Apply migrations
npx prisma db push       # Push schema (dev)
npx prisma db pull       # Pull from db
npx prisma studio        # Open GUI
npx prisma format        # Format schema
```

---

## 💡 Summary

| Level | Focus |
|-------|-------|
| **Junior** | Setup, Basic CRUD |
| **Mid** | Filtering, Pagination, Relations |
| **Senior** | Service pattern, Transactions |
| **Expert** | Soft delete, Hooks, Raw queries |

**Best Practices:**
- ✅ Use service pattern
- ✅ Transactions untuk operasi multi-table
- ✅ Select hanya field yang dibutuhkan
- ✅ Index untuk query yang sering dipakai
- ✅ Connection pooling
- ❌ Don't use `findMany` tanpa limit
- ❌ Don't ignore migration conflicts
- ❌ Don't expose password di response
