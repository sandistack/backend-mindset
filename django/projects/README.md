# 🚀 Django Projects - Learning Path

Project-based learning dari Junior hingga Senior level. Setiap project dirancang untuk mengimplementasikan konsep dari dokumentasi yang sudah ada.

---

## 📊 Overview

| Level | Project | Durasi | Skill yang Dipelajari |
|-------|---------|--------|----------------------|
| **Junior** | Task Management API | 1-2 minggu | CRUD, Auth, Serializers, Basic Testing |
| **Mid** | E-Commerce API | 3-4 minggu | File Upload, Email, Export, Payment Integration |
| **Senior** | Collaboration Platform | 4-6 minggu | WebSocket, Caching, Background Jobs, Microservices |

---

## 🎯 Cara Menggunakan

### 1. Pilih Level Sesuai Kemampuan

```
Junior Developer (0-1 tahun):
└── Mulai dari Project 01 - Task Management API

Mid Developer (1-3 tahun):
└── Langsung ke Project 02 - E-Commerce API

Senior Developer (3+ tahun):
└── Challenge diri dengan Project 03 - Collaboration Platform
```

### 2. Ikuti Step-by-Step Guide

Setiap project memiliki folder `docs/` dengan panduan bertahap:
- Baca README.md project untuk overview
- Ikuti setiap file di `docs/` secara berurutan
- Referensi ke dokumentasi utama untuk detail lebih lanjut

### 3. Implementasi Sendiri

Panduan hanya berisi instruksi dan referensi, **bukan copy-paste code**.
Tujuannya: memaksa kamu untuk benar-benar memahami dan menulis sendiri.

---

## 📁 Project Structure

```
django/projects/
├── README.md                          # File ini
├── 01-junior-task-api/
│   ├── README.md                      # Overview project
│   └── docs/
│       ├── 01-PROJECT_SETUP.md        # Setup Django project
│       ├── 02-USER_AUTH.md            # Authentication system
│       ├── 03-TASK_CRUD.md            # Task CRUD operations
│       ├── 04-FILTERING_PAGINATION.md # Filter & pagination
│       └── 05-TESTING.md              # Unit & integration tests
│
├── 02-mid-ecommerce-api/
│   ├── README.md
│   └── docs/
│       ├── 01-PROJECT_SETUP.md        # Multi-app architecture
│       ├── 02-PRODUCT_CATALOG.md      # Product management
│       ├── 03-SHOPPING_CART.md        # Cart & checkout
│       ├── 04-ORDER_MANAGEMENT.md     # Order processing
│       ├── 05-FILE_UPLOAD.md          # Product images
│       ├── 06-EMAIL_NOTIFICATION.md   # Order emails
│       ├── 07-EXPORT_REPORTS.md       # Sales reports
│       └── 08-PAYMENT_INTEGRATION.md  # Payment gateway
│
└── 03-senior-collab-platform/
    ├── README.md
    └── docs/
        ├── 01-ARCHITECTURE.md         # System design
        ├── 02-REALTIME_WEBSOCKET.md   # Real-time features
        ├── 03-CACHING_STRATEGY.md     # Redis caching
        ├── 04-BACKGROUND_JOBS.md      # Celery tasks
        ├── 05-NOTIFICATION_SYSTEM.md  # Push & email notifications
        ├── 06-FILE_COLLABORATION.md   # Shared file storage
        ├── 07-SEARCH_ENGINE.md        # Elasticsearch
        └── 08-DEPLOYMENT.md           # Docker & CI/CD
```

---

## 🔗 Referensi Dokumentasi

Setiap panduan project akan merujuk ke dokumentasi berikut:

### Fundamentals
- [ARCHITECTURE.md](../docs/01-fundamentals/ARCHITECTURE.md)
- [RESPONSE_SCHEMA.md](../docs/01-fundamentals/RESPONSE_SCHEMA.md)
- [ERROR_HANDLING.md](../docs/01-fundamentals/ERROR_HANDLING.md)
- [MIDDLEWARE.md](../docs/01-fundamentals/MIDDLEWARE.md)

### Database
- [SERIALIZERS.md](../docs/02-database/SERIALIZERS.md)
- [FILTERING_SEARCH.md](../docs/02-database/FILTERING_SEARCH.md)
- [PAGINATION.md](../docs/02-database/PAGINATION.md)
- [MIGRATIONS.md](../docs/02-database/MIGRATIONS.md)

### Authentication
- [SECURITY.md](../docs/03-authentication/SECURITY.md)
- [GROUPS.md](../docs/03-authentication/GROUPS.md)

### Advanced
- [FILE_UPLOAD.md](../docs/04-advanced/FILE_UPLOAD.md)
- [EMAIL.md](../docs/04-advanced/EMAIL.md)
- [EXPORT.md](../docs/04-advanced/EXPORT.md)
- [WEBSOCKET.md](../docs/04-advanced/WEBSOCKET.md)
- [CACHING.md](../docs/04-advanced/CACHING.md)
- [BACKGROUND_JOBS.md](../docs/04-advanced/BACKGROUND_JOBS.md)
- [SIGNALS.md](../docs/04-advanced/SIGNALS.md)
- [DECORATOR.md](../docs/04-advanced/DECORATOR.md)

### Testing & Operations
- [TESTS.md](../docs/05-testing/TESTS.md)
- [DEPLOYMENT.md](../docs/06-operations/DEPLOYMENT.md)
- [LOG.md](../docs/06-operations/LOG.md)

---

## ⚡ Quick Start

```bash
# Clone dan masuk ke folder
cd backend-mindset/django/projects

# Pilih project sesuai level
cd 01-junior-task-api   # atau 02-mid-ecommerce-api, 03-senior-collab-platform

# Baca README.md untuk overview
# Kemudian ikuti docs/ secara berurutan
```

---

## 💡 Tips

1. **Jangan Skip Level** - Meski terasa mudah, Junior project membangun fondasi
2. **Tulis Sendiri** - Jangan copy-paste, ketik manual untuk muscle memory
3. **Baca Dokumentasi** - Setiap panduan merujuk ke docs utama
4. **Commit Sering** - Praktekkan git workflow yang baik
5. **Test First** - Biasakan TDD dari project pertama

---

## 🎓 Setelah Menyelesaikan Semua Project

Kamu akan memiliki:
- 3 portfolio projects production-ready
- Pemahaman mendalam Django + DRF
- Pengalaman dengan tools production (Redis, Celery, WebSocket)
- Kemampuan deploy ke cloud

**Next Step:** Contribute ke open source atau buat SaaS sendiri!
