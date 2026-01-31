# 📁 STRUKTUR FOLDER - Express/Node.js Project Structure

Best practices untuk mengorganisir project Express.js dari small hingga large scale.

---

## 🎯 Overview

```
Node.js tidak memiliki konvensi struktur folder yang ketat.
Dokumen ini menjelaskan patterns yang umum digunakan di production.
```

---

## 1️⃣ SMALL PROJECT (Simple API)

Untuk project kecil dengan sedikit endpoint:

```
my_api/
├── package.json
├── package-lock.json
├── .env
├── .env.example
├── .gitignore
├── README.md
│
├── src/
│   ├── index.js                # Entry point
│   ├── app.js                  # Express app setup
│   ├── config.js               # Configuration
│   │
│   ├── routes/
│   │   ├── index.js            # Route aggregator
│   │   ├── user.routes.js
│   │   └── auth.routes.js
│   │
│   ├── controllers/
│   │   ├── user.controller.js
│   │   └── auth.controller.js
│   │
│   ├── models/                 # Prisma atau Mongoose
│   │   └── index.js
│   │
│   ├── middleware/
│   │   ├── auth.js
│   │   └── errorHandler.js
│   │
│   └── utils/
│       └── helpers.js
│
└── prisma/                     # Jika pakai Prisma
    └── schema.prisma
```

---

## 2️⃣ MEDIUM PROJECT (Standard API)

Untuk REST API dengan beberapa domain:

```
my_api/
├── package.json
├── package-lock.json
├── .env
├── .env.example
├── .gitignore
├── README.md
├── Dockerfile
├── docker-compose.yml
├── jest.config.js
├── .eslintrc.js
├── .prettierrc
│
├── src/
│   ├── index.js                # Server entry
│   ├── app.js                  # Express app
│   │
│   ├── config/
│   │   ├── index.js            # Config aggregator
│   │   ├── database.js
│   │   ├── redis.js
│   │   └── jwt.js
│   │
│   ├── routes/
│   │   ├── index.js
│   │   ├── v1/                 # API versioning
│   │   │   ├── index.js
│   │   │   ├── auth.routes.js
│   │   │   ├── user.routes.js
│   │   │   └── product.routes.js
│   │   └── v2/
│   │       └── ...
│   │
│   ├── controllers/
│   │   ├── auth.controller.js
│   │   ├── user.controller.js
│   │   └── product.controller.js
│   │
│   ├── services/               # Business logic
│   │   ├── auth.service.js
│   │   ├── user.service.js
│   │   └── product.service.js
│   │
│   ├── repositories/           # Data access (optional)
│   │   ├── user.repository.js
│   │   └── product.repository.js
│   │
│   ├── models/                 # Prisma models atau entities
│   │   └── index.js
│   │
│   ├── middleware/
│   │   ├── auth.js
│   │   ├── validate.js
│   │   ├── errorHandler.js
│   │   └── rateLimiter.js
│   │
│   ├── validators/             # Request validation (Joi)
│   │   ├── auth.validator.js
│   │   ├── user.validator.js
│   │   └── product.validator.js
│   │
│   ├── utils/
│   │   ├── ApiError.js
│   │   ├── response.js
│   │   ├── logger.js
│   │   └── helpers.js
│   │
│   └── lib/                    # External service clients
│       ├── prisma.js
│       ├── redis.js
│       └── email.js
│
├── prisma/
│   ├── schema.prisma
│   └── migrations/
│
├── tests/
│   ├── setup.js
│   ├── fixtures/
│   ├── unit/
│   │   ├── services/
│   │   └── utils/
│   └── integration/
│       └── routes/
│
├── logs/
│
└── docs/
    └── api.md
```

---

## 3️⃣ LARGE PROJECT (Enterprise)

Untuk project besar dengan multiple modules:

```
my_api/
├── package.json
├── package-lock.json
├── .env
├── .env.example
├── .env.test
├── .gitignore
├── README.md
├── Dockerfile
├── docker-compose.yml
├── docker-compose.prod.yml
├── jest.config.js
├── .eslintrc.js
├── .prettierrc
├── tsconfig.json               # Jika TypeScript
│
├── src/
│   ├── index.js                # Entry point
│   ├── app.js                  # Express app
│   ├── server.js               # HTTP server
│   │
│   ├── config/
│   │   ├── index.js
│   │   ├── app.config.js
│   │   ├── database.config.js
│   │   ├── redis.config.js
│   │   ├── jwt.config.js
│   │   ├── email.config.js
│   │   └── storage.config.js
│   │
│   ├── api/                    # API layer
│   │   ├── index.js
│   │   ├── v1/
│   │   │   ├── index.js
│   │   │   │
│   │   │   ├── auth/
│   │   │   │   ├── auth.routes.js
│   │   │   │   ├── auth.controller.js
│   │   │   │   ├── auth.validator.js
│   │   │   │   └── auth.test.js
│   │   │   │
│   │   │   ├── users/
│   │   │   │   ├── user.routes.js
│   │   │   │   ├── user.controller.js
│   │   │   │   ├── user.validator.js
│   │   │   │   └── user.test.js
│   │   │   │
│   │   │   ├── products/
│   │   │   │   └── ...
│   │   │   │
│   │   │   └── orders/
│   │   │       └── ...
│   │   │
│   │   └── v2/
│   │       └── ...
│   │
│   ├── modules/                # Feature modules
│   │   ├── auth/
│   │   │   ├── auth.service.js
│   │   │   ├── auth.repository.js
│   │   │   ├── strategies/
│   │   │   │   ├── jwt.strategy.js
│   │   │   │   └── oauth.strategy.js
│   │   │   └── __tests__/
│   │   │       └── auth.service.test.js
│   │   │
│   │   ├── users/
│   │   │   ├── user.service.js
│   │   │   ├── user.repository.js
│   │   │   ├── user.events.js
│   │   │   └── __tests__/
│   │   │
│   │   ├── products/
│   │   │   └── ...
│   │   │
│   │   ├── orders/
│   │   │   └── ...
│   │   │
│   │   ├── payments/
│   │   │   ├── payment.service.js
│   │   │   ├── providers/
│   │   │   │   ├── stripe.provider.js
│   │   │   │   └── midtrans.provider.js
│   │   │   └── __tests__/
│   │   │
│   │   └── notifications/
│   │       ├── notification.service.js
│   │       ├── channels/
│   │       │   ├── email.channel.js
│   │       │   └── push.channel.js
│   │       └── templates/
│   │
│   ├── core/                   # Shared core
│   │   ├── database/
│   │   │   ├── prisma.js
│   │   │   └── redis.js
│   │   │
│   │   ├── middleware/
│   │   │   ├── auth.middleware.js
│   │   │   ├── validate.middleware.js
│   │   │   ├── errorHandler.middleware.js
│   │   │   ├── rateLimiter.middleware.js
│   │   │   ├── requestId.middleware.js
│   │   │   └── cors.middleware.js
│   │   │
│   │   ├── errors/
│   │   │   ├── ApiError.js
│   │   │   ├── ValidationError.js
│   │   │   └── AuthError.js
│   │   │
│   │   ├── utils/
│   │   │   ├── response.js
│   │   │   ├── pagination.js
│   │   │   ├── encryption.js
│   │   │   └── helpers.js
│   │   │
│   │   └── constants/
│   │       ├── httpStatus.js
│   │       └── permissions.js
│   │
│   ├── infrastructure/         # External services
│   │   ├── cache/
│   │   │   └── redis.cache.js
│   │   ├── queue/
│   │   │   ├── bull.js
│   │   │   └── jobs/
│   │   │       ├── email.job.js
│   │   │       └── notification.job.js
│   │   ├── storage/
│   │   │   ├── s3.storage.js
│   │   │   └── local.storage.js
│   │   ├── email/
│   │   │   ├── email.service.js
│   │   │   └── templates/
│   │   └── external/
│   │       ├── stripe.client.js
│   │       └── firebase.client.js
│   │
│   ├── jobs/                   # Background jobs
│   │   ├── processor.js
│   │   ├── sendEmail.job.js
│   │   └── cleanupTokens.job.js
│   │
│   └── events/                 # Event handlers
│       ├── emitter.js
│       ├── userEvents.js
│       └── orderEvents.js
│
├── prisma/
│   ├── schema.prisma
│   ├── seed.js
│   └── migrations/
│
├── tests/
│   ├── setup.js
│   ├── teardown.js
│   ├── helpers/
│   │   ├── auth.helper.js
│   │   └── db.helper.js
│   ├── factories/
│   │   ├── user.factory.js
│   │   └── product.factory.js
│   ├── fixtures/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── scripts/
│   ├── seed.js
│   ├── migrate.js
│   └── generate-docs.js
│
├── logs/
│
├── docs/
│   ├── api/
│   ├── architecture/
│   └── deployment/
│
└── .github/
    └── workflows/
        ├── ci.yml
        └── deploy.yml
```

---

## 4️⃣ MODULAR STRUCTURE (Feature-Based)

Struktur berdasarkan fitur/domain:

```
src/
├── modules/
│   ├── auth/
│   │   ├── index.js            # Module exports
│   │   ├── auth.routes.js
│   │   ├── auth.controller.js
│   │   ├── auth.service.js
│   │   ├── auth.repository.js
│   │   ├── auth.validator.js
│   │   ├── auth.middleware.js
│   │   ├── auth.constants.js
│   │   └── __tests__/
│   │       ├── auth.service.test.js
│   │       └── auth.routes.test.js
│   │
│   ├── users/
│   │   ├── index.js
│   │   ├── user.routes.js
│   │   ├── user.controller.js
│   │   ├── user.service.js
│   │   ├── user.repository.js
│   │   ├── user.validator.js
│   │   ├── user.events.js
│   │   └── __tests__/
│   │
│   └── products/
│       └── ...
│
└── shared/                     # Shared utilities
    ├── middleware/
    ├── utils/
    ├── errors/
    └── constants/
```

**Module Export Pattern:**

```javascript
// src/modules/users/index.js
const userRoutes = require('./user.routes');
const userService = require('./user.service');
const userRepository = require('./user.repository');

module.exports = {
  routes: userRoutes,
  service: userService,
  repository: userRepository
};
```

---

## 5️⃣ CLEAN ARCHITECTURE STRUCTURE

```
src/
├── domain/                     # Enterprise Business Rules
│   ├── entities/
│   │   ├── User.js
│   │   └── Product.js
│   ├── value-objects/
│   │   ├── Email.js
│   │   └── Money.js
│   └── errors/
│       └── DomainError.js
│
├── application/                # Application Business Rules
│   ├── use-cases/
│   │   ├── user/
│   │   │   ├── CreateUser.js
│   │   │   ├── GetUser.js
│   │   │   └── UpdateUser.js
│   │   └── product/
│   │       └── ...
│   ├── interfaces/             # Ports
│   │   ├── IUserRepository.js
│   │   └── IEmailService.js
│   └── dto/
│       ├── CreateUserDTO.js
│       └── UserResponseDTO.js
│
├── infrastructure/             # Frameworks & Drivers
│   ├── database/
│   │   ├── prisma/
│   │   └── repositories/
│   │       └── UserRepository.js
│   ├── services/
│   │   └── EmailService.js
│   └── http/
│       ├── express/
│       │   ├── app.js
│       │   └── server.js
│       ├── controllers/
│       │   └── UserController.js
│       ├── routes/
│       │   └── user.routes.js
│       └── middleware/
│
└── main/                       # Composition Root
    ├── index.js
    ├── container.js            # DI Container
    └── factories/
        └── userFactory.js
```

---

## 6️⃣ FILE NAMING CONVENTIONS

| Type | Convention | Example |
|------|------------|---------|
| Routes | .routes.js | `user.routes.js` |
| Controller | .controller.js | `user.controller.js` |
| Service | .service.js | `user.service.js` |
| Repository | .repository.js | `user.repository.js` |
| Validator | .validator.js | `user.validator.js` |
| Middleware | .middleware.js | `auth.middleware.js` |
| Test | .test.js | `user.service.test.js` |
| Config | .config.js | `database.config.js` |

---

## 7️⃣ COMMON PATTERNS

### Route → Controller → Service Pattern

```javascript
// routes/user.routes.js
router.get('/:id', userController.getById);

// controllers/user.controller.js
const getById = async (req, res, next) => {
  try {
    const user = await userService.findById(req.params.id);
    res.json({ success: true, data: user });
  } catch (error) {
    next(error);
  }
};

// services/user.service.js
const findById = async (id) => {
  const user = await prisma.user.findUnique({ where: { id } });
  if (!user) throw new ApiError(404, 'User not found');
  return user;
};
```

### Index Barrel Export

```javascript
// src/services/index.js
module.exports = {
  userService: require('./user.service'),
  authService: require('./auth.service'),
  productService: require('./product.service')
};

// Usage
const { userService, authService } = require('./services');
```

### Route Aggregation

```javascript
// src/routes/v1/index.js
const express = require('express');
const router = express.Router();

router.use('/auth', require('./auth.routes'));
router.use('/users', require('./user.routes'));
router.use('/products', require('./product.routes'));

module.exports = router;

// src/routes/index.js
const express = require('express');
const router = express.Router();

router.use('/v1', require('./v1'));
router.use('/v2', require('./v2'));

module.exports = router;

// src/app.js
app.use('/api', require('./routes'));
// Results in: /api/v1/users, /api/v1/products, etc.
```

---

## 8️⃣ PACKAGE.JSON SCRIPTS

```json
{
  "scripts": {
    "start": "node src/index.js",
    "dev": "nodemon src/index.js",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "lint": "eslint src/",
    "lint:fix": "eslint src/ --fix",
    "format": "prettier --write src/",
    "db:migrate": "prisma migrate dev",
    "db:push": "prisma db push",
    "db:seed": "prisma db seed",
    "db:studio": "prisma studio",
    "build": "npm run lint && npm test",
    "docker:up": "docker-compose up -d",
    "docker:down": "docker-compose down"
  }
}
```

---

## 📊 Comparison Table

| Aspect | Small | Medium | Large |
|--------|-------|--------|-------|
| Folders | Flat | Layered | Modular/Clean |
| Routes versioning | ❌ | ✅ | ✅ |
| Services layer | Optional | ✅ | ✅ |
| Repository pattern | ❌ | Optional | ✅ |
| Separate tests folder | ❌ | ✅ | ✅ |
| Feature modules | ❌ | Optional | ✅ |
| DI Container | ❌ | ❌ | Optional |

---

## 💡 Best Practices

### ✅ DO

- Consistent naming conventions
- Group by feature untuk project besar
- Separate concerns (routes, controllers, services)
- Use index.js untuk barrel exports
- Environment-based config
- Tests dekat dengan source (atau folder terpisah)

### ❌ DON'T

- Jangan terlalu banyak nesting (max 3-4 level)
- Jangan circular dependencies
- Jangan hardcode config
- Jangan business logic di controllers
- Jangan skip validation
- Jangan mix concerns

---

## 🔗 Related Docs

- [EXPRESS.md](01-fundamentals/EXPRESS.md) - Express basics
- [PRISMA.md](02-database/PRISMA.md) - Database patterns
- [TESTS.md](05-testing/TESTS.md) - Testing structure
