# 🧪 Testing Task CRUD API

## Setup & Menjalankan Server

```bash
# Aktivasi virtual environment
source venv/bin/activate

# Jalankan development server
python manage.py runserver
```

Server akan berjalan di: `http://localhost:8000`

---

## 📋 Persiapan: Login & Get Token

Sebelum test endpoints, Anda perlu login untuk mendapatkan access token:

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "SecurePass123!"
  }'
```

**Simpan `access` token dari response untuk request selanjutnya!**

```bash
# Simpan ke variable (Linux/Mac)
export TOKEN="your_access_token_here"
```

---

## 📂 Category Endpoints

### 1. Create Category

**POST** `/api/categories/`

```bash
curl -X POST http://localhost:8000/api/categories/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Work",
    "color": "#EF4444"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Category created successfully",
  "data": {
    "id": 1,
    "name": "Work",
    "color": "#EF4444",
    "created_at": "2026-02-18T10:30:00.000000"
  }
}
```

### 2. List All Categories

**GET** `/api/categories/`

```bash
curl http://localhost:8000/api/categories/ \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Get Category Detail

**GET** `/api/categories/{id}/`

```bash
curl http://localhost:8000/api/categories/1/ \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Update Category

**PATCH** `/api/categories/{id}/`

```bash
curl -X PATCH http://localhost:8000/api/categories/1/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Work Projects"
  }'
```

### 5. Delete Category

**DELETE** `/api/categories/{id}/`

```bash
curl -X DELETE http://localhost:8000/api/categories/1/ \
  -H "Authorization: Bearer $TOKEN"
```

---

## ✅ Task Endpoints

### 1. Create Task

**POST** `/api/tasks/`

```bash
curl -X POST http://localhost:8000/api/tasks/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Complete project documentation",
    "description": "Write comprehensive API documentation",
    "priority": "high",
    "status": "pending",
    "category": 1,
    "due_date": "2026-02-20T17:00:00Z"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Task created successfully",
  "data": {
    "id": 1,
    "title": "Complete project documentation",
    "description": "Write comprehensive API documentation",
    "priority": "high",
    "status": "pending",
    "due_date": "2026-02-20T17:00:00Z",
    "completed_at": null,
    "category": {
      "id": 1,
      "name": "Work",
      "color": "#EF4444"
    },
    "created_at": "2026-02-18T10:35:00.000000",
    "updated_at": "2026-02-18T10:35:00.000000"
  }
}
```

### 2. List All Tasks

**GET** `/api/tasks/`

```bash
curl http://localhost:8000/api/tasks/ \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Get Task Detail

**GET** `/api/tasks/{id}/`

```bash
curl http://localhost:8000/api/tasks/1/ \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Update Task

**PATCH** `/api/tasks/{id}/`

```bash
curl -X PATCH http://localhost:8000/api/tasks/1/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_progress",
    "priority": "medium"
  }'
```

### 5. Mark Task as Complete

**POST** `/api/tasks/{id}/complete/`

```bash
curl -X POST http://localhost:8000/api/tasks/1/complete/ \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "success": true,
  "message": "Task marked as complete",
  "data": {
    "id": 1,
    "title": "Complete project documentation",
    "status": "done",
    "completed_at": "2026-02-18T10:40:00.000000",
    ...
  }
}
```

### 6. Delete Task (Soft Delete)

**DELETE** `/api/tasks/{id}/`

```bash
curl -X DELETE http://localhost:8000/api/tasks/1/ \
  -H "Authorization: Bearer $TOKEN"
```

**Note:** Task tidak dihapus permanen, hanya di-soft delete (is_deleted=True)

### 7. Restore Deleted Task

**POST** `/api/tasks/{id}/restore/`

```bash
curl -X POST http://localhost:8000/api/tasks/1/restore/ \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🎯 Priority & Status Values

### Priority Options:
- `low` - Low priority
- `medium` - Medium priority (default)
- `high` - High priority

### Status Options:
- `pending` - Task not started (default)
- `in_progress` - Task in progress
- `done` - Task completed

---

## 📊 API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| **Categories** |  |  |
| GET | `/api/categories/` | List all categories |
| POST | `/api/categories/` | Create new category |
| GET | `/api/categories/{id}/` | Get category detail |
| PATCH | `/api/categories/{id}/` | Update category |
| DELETE | `/api/categories/{id}/` | Delete category |
| **Tasks** |  |  |
| GET | `/api/tasks/` | List all tasks |
| POST | `/api/tasks/` | Create new task |
| GET | `/api/tasks/{id}/` | Get task detail |
| PATCH | `/api/tasks/{id}/` | Update task |
| DELETE | `/api/tasks/{id}/` | Soft delete task |
| POST | `/api/tasks/{id}/complete/` | Mark task complete |
| POST | `/api/tasks/{id}/restore/` | Restore deleted task |

---

## ✅ Testing Checklist

### Categories:
- [ ] Create category dengan valid data
- [ ] Create category dengan nama duplicate (harus error)
- [ ] Create category dengan color invalid format (harus error)
- [ ] List categories (hanya milik user sendiri)
- [ ] Update category
- [ ] Delete category
- [ ] User tidak bisa akses category user lain

### Tasks:
- [ ] Create task tanpa category
- [ ] Create task dengan category
- [ ] Create task dengan due_date di masa lalu (harus error)
- [ ] Create task dengan category milik user lain (harus error)
- [ ] List tasks (hanya milik user sendiri)
- [ ] Update task
- [ ] Update task status ke 'done' (completed_at otomatis terisi)
- [ ] Mark task as complete
- [ ] Soft delete task
- [ ] Verify deleted task tidak muncul di list
- [ ] Restore deleted task
- [ ] User tidak bisa akses task user lain

---

## 🔧 Testing dengan API Documentation

Untuk testing lebih mudah dengan UI interaktif:

1. **Swagger UI**: http://localhost:8000/api/docs/
2. **ReDoc**: http://localhost:8000/api/redoc/

**Cara pakai:**
1. Klik "Authorize" button
2. Masukkan token: `Bearer your_access_token`
3. Klik "Authorize"
4. Sekarang bisa test semua endpoints dari UI

---

## 🐛 Common Issues

### Issue: "Authentication credentials were not provided"
**Solution:** Pastikan header Authorization ada: `Authorization: Bearer <token>`

### Issue: "You already have a category named 'Work'"
**Solution:** Nama category harus unique per user. Gunakan nama lain.

### Issue: "You can only assign tasks to your own categories"
**Solution:** Category yang di-assign harus milik user yang sama.

### Issue: "Due date cannot be in the past"
**Solution:** Saat create task, due_date harus di masa depan.

---

## 📖 Next Steps

Setelah Task CRUD berfungsi dengan baik, lanjut ke:
- **Step 4**: Filtering, Search & Pagination
- **Step 5**: Testing & Deployment
