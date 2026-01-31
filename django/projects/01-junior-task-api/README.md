# 📋 Project 01: Task Management API

**Level:** Junior  
**Durasi:** 1-2 Minggu  
**Difficulty:** ⭐⭐☆☆☆

---

## 🎯 Tujuan Project

Membuat REST API untuk manajemen task dengan fitur lengkap authentication dan CRUD operations. Project ini adalah fondasi untuk memahami Django REST Framework.

---

## 📋 Fitur yang Akan Dibuat

### Authentication
- [x] User registration
- [x] Login dengan JWT token
- [x] Logout & token refresh
- [x] Password reset

### Task Management
- [x] Create, Read, Update, Delete tasks
- [x] Task categories/tags
- [x] Task priority levels
- [x] Due date & reminders
- [x] Mark as complete

### Advanced
- [x] Filter tasks by status, priority, date
- [x] Search tasks by title/description
- [x] Pagination
- [x] Soft delete

---

## 🏗️ Tech Stack

```
Django 4.2+
Django REST Framework 3.14+
PostgreSQL (atau SQLite untuk development)
JWT Authentication (djangorestframework-simplejwt)
```

---

## 📊 Database Schema

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    User     │       │    Task     │       │   Category  │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id          │──────<│ user_id     │       │ id          │
│ email       │       │ category_id │>──────│ name        │
│ password    │       │ title       │       │ color       │
│ name        │       │ description │       │ user_id     │
│ created_at  │       │ priority    │       └─────────────┘
└─────────────┘       │ status      │
                      │ due_date    │
                      │ is_deleted  │
                      │ created_at  │
                      │ updated_at  │
                      └─────────────┘
```

---

## 📁 Struktur Folder

```
task-api/
├── manage.py
├── requirements.txt
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
└── apps/
    ├── authentication/
    │   ├── models.py      # Custom User model
    │   ├── serializers.py
    │   ├── views.py
    │   ├── urls.py
    │   └── tests.py
    ├── tasks/
    │   ├── models.py      # Task, Category models
    │   ├── serializers.py
    │   ├── views.py
    │   ├── urls.py
    │   ├── filters.py     # django-filter
    │   └── tests.py
    └── core/
        ├── pagination.py   # Custom pagination
        ├── permissions.py  # Custom permissions
        └── utils.py
```

---

## 📚 Step-by-Step Guide

Ikuti panduan ini secara berurutan:

| Step | File | Deskripsi | Waktu |
|------|------|-----------|-------|
| 1 | [01-PROJECT_SETUP.md](docs/01-PROJECT_SETUP.md) | Setup project & struktur folder | 2-3 jam |
| 2 | [02-USER_AUTH.md](docs/02-USER_AUTH.md) | Custom user & JWT auth | 4-6 jam |
| 3 | [03-TASK_CRUD.md](docs/03-TASK_CRUD.md) | Task model & CRUD API | 4-6 jam |
| 4 | [04-FILTERING_PAGINATION.md](docs/04-FILTERING_PAGINATION.md) | Filter, search, pagination | 3-4 jam |
| 5 | [05-TESTING.md](docs/05-TESTING.md) | Unit & integration tests | 4-6 jam |

---

## 🎯 API Endpoints

```
Authentication:
POST   /api/auth/register/           # Register user
POST   /api/auth/login/              # Login, get JWT
POST   /api/auth/logout/             # Blacklist token
POST   /api/auth/token/refresh/      # Refresh token
POST   /api/auth/password-reset/     # Request reset
POST   /api/auth/password-reset/confirm/  # Confirm reset

Tasks:
GET    /api/tasks/                   # List tasks (with filter/search)
POST   /api/tasks/                   # Create task
GET    /api/tasks/{id}/              # Get task detail
PUT    /api/tasks/{id}/              # Update task
DELETE /api/tasks/{id}/              # Soft delete task
POST   /api/tasks/{id}/complete/     # Mark complete
POST   /api/tasks/{id}/restore/      # Restore deleted

Categories:
GET    /api/categories/              # List categories
POST   /api/categories/              # Create category
PUT    /api/categories/{id}/         # Update
DELETE /api/categories/{id}/         # Delete
```

---

## ✅ Checklist Penyelesaian

### Week 1
- [ ] Project setup selesai
- [ ] Custom User model berjalan
- [ ] JWT authentication berfungsi
- [ ] Task CRUD API selesai

### Week 2
- [ ] Category model & API
- [ ] Filter & search berfungsi
- [ ] Pagination implemented
- [ ] Semua tests passing
- [ ] API documentation (Swagger/ReDoc)

---

## 🔗 Referensi Dokumentasi

- [ARCHITECTURE.md](../../docs/01-fundamentals/ARCHITECTURE.md) - Struktur project
- [SERIALIZERS.md](../../docs/02-database/SERIALIZERS.md) - Serializers guide
- [FILTERING_SEARCH.md](../../docs/02-database/FILTERING_SEARCH.md) - Django-filter
- [PAGINATION.md](../../docs/02-database/PAGINATION.md) - Pagination patterns
- [SECURITY.md](../../docs/03-authentication/SECURITY.md) - JWT best practices
- [TESTS.md](../../docs/05-testing/TESTS.md) - Testing guide

---

## 🚀 Setelah Selesai

1. Deploy ke Railway/Render (gratis)
2. Tambahkan ke portfolio GitHub
3. Lanjut ke **Project 02: E-Commerce API**
