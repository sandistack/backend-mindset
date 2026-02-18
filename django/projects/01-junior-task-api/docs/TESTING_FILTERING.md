# 🔍 Testing Filtering, Search & Pagination

## Setup & Persiapan

Pastikan server berjalan dan Anda sudah punya access token:

```bash
# Jalankan server
python manage.py runserver

# Login untuk mendapatkan token
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "testuser@example.com", "password": "SecurePass123!"}'

# Simpan token
export TOKEN="your_access_token_here"
```

---

## 📊 Category Filtering & Search

### 1. Search Categories

**Cari berdasarkan nama (case-insensitive):**

```bash
curl "http://localhost:8000/api/categories/?search=work" \
  -H "Authorization: Bearer $TOKEN"
```

### 2. Filter by Name (contains)

```bash
curl "http://localhost:8000/api/categories/?name=personal" \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Filter by Color

```bash
curl "http://localhost:8000/api/categories/?color=%23EF4444" \
  -H "Authorization: Bearer $TOKEN"
```

**Note:** `#` harus di-encode jadi `%23`

### 4. Order Categories

```bash
# Ascending by name
curl "http://localhost:8000/api/categories/?ordering=name" \
  -H "Authorization: Bearer $TOKEN"

# Descending by created date
curl "http://localhost:8000/api/categories/?ordering=-created_at" \
  -H "Authorization: Bearer $TOKEN"
```

---

## ✅ Task Filtering

### 1. Filter by Status

```bash
# Pending tasks
curl "http://localhost:8000/api/tasks/?status=pending" \
  -H "Authorization: Bearer $TOKEN"

# In progress tasks
curl "http://localhost:8000/api/tasks/?status=in_progress" \
  -H "Authorization: Bearer $TOKEN"

# Completed tasks
curl "http://localhost:8000/api/tasks/?status=done" \
  -H "Authorization: Bearer $TOKEN"
```

### 2. Filter by Priority

```bash
# High priority
curl "http://localhost:8000/api/tasks/?priority=high" \
  -H "Authorization: Bearer $TOKEN"

# Medium priority
curl "http://localhost:8000/api/tasks/?priority=medium" \
  -H "Authorization: Bearer $TOKEN"

# Low priority
curl "http://localhost:8000/api/tasks/?priority=low" \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Filter by Category

```bash
# Tasks in category 1
curl "http://localhost:8000/api/tasks/?category=1" \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Date Range Filters

**Due Date Range:**

```bash
# Tasks due between Jan - Dec 2026
curl "http://localhost:8000/api/tasks/?due_date_from=2026-01-01&due_date_to=2026-12-31" \
  -H "Authorization: Bearer $TOKEN"

# Tasks due in next 7 days
curl "http://localhost:8000/api/tasks/?due_date_from=2026-02-18&due_date_to=2026-02-25" \
  -H "Authorization: Bearer $TOKEN"
```

**Created Date Range:**

```bash
# Tasks created this month
curl "http://localhost:8000/api/tasks/?created_from=2026-02-01&created_to=2026-02-28" \
  -H "Authorization: Bearer $TOKEN"
```

### 5. Boolean Filters

**Completed Tasks:**

```bash
# Show only completed tasks
curl "http://localhost:8000/api/tasks/?is_completed=true" \
  -H "Authorization: Bearer $TOKEN"

# Show only uncompleted tasks
curl "http://localhost:8000/api/tasks/?is_completed=false" \
  -H "Authorization: Bearer $TOKEN"
```

**Overdue Tasks:**

```bash
# Show only overdue tasks (past due_date and not completed)
curl "http://localhost:8000/api/tasks/?is_overdue=true" \
  -H "Authorization: Bearer $TOKEN"
```

**Has Category:**

```bash
# Tasks with category
curl "http://localhost:8000/api/tasks/?has_category=true" \
  -H "Authorization: Bearer $TOKEN"

# Tasks without category
curl "http://localhost:8000/api/tasks/?has_category=false" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🔍 Search

Search in task title and description:

```bash
# Search for "meeting"
curl "http://localhost:8000/api/tasks/?search=meeting" \
  -H "Authorization: Bearer $TOKEN"

# Search for "project"
curl "http://localhost:8000/api/tasks/?search=project" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📈 Ordering (Sorting)

### Single Field Ordering

```bash
# Ascending by created date (oldest first)
curl "http://localhost:8000/api/tasks/?ordering=created_at" \
  -H "Authorization: Bearer $TOKEN"

# Descending by created date (newest first) - DEFAULT
curl "http://localhost:8000/api/tasks/?ordering=-created_at" \
  -H "Authorization: Bearer $TOKEN"

# By due date (earliest first)
curl "http://localhost:8000/api/tasks/?ordering=due_date" \
  -H "Authorization: Bearer $TOKEN"

# By priority
curl "http://localhost:8000/api/tasks/?ordering=priority" \
  -H "Authorization: Bearer $TOKEN"

# By status
curl "http://localhost:8000/api/tasks/?ordering=status" \
  -H "Authorization: Bearer $TOKEN"
```

### Multiple Field Ordering

```bash
# High priority first, then by due date
curl "http://localhost:8000/api/tasks/?ordering=priority,-due_date" \
  -H "Authorization: Bearer $TOKEN"

# Status first, then newest first
curl "http://localhost:8000/api/tasks/?ordering=status,-created_at" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📄 Pagination

### Basic Pagination

```bash
# Page 1 (default page_size=10)
curl "http://localhost:8000/api/tasks/?page=1" \
  -H "Authorization: Bearer $TOKEN"

# Page 2
curl "http://localhost:8000/api/tasks/?page=2" \
  -H "Authorization: Bearer $TOKEN"
```

### Custom Page Size

```bash
# 20 items per page
curl "http://localhost:8000/api/tasks/?page_size=20" \
  -H "Authorization: Bearer $TOKEN"

# 5 items per page
curl "http://localhost:8000/api/tasks/?page_size=5" \
  -H "Authorization: Bearer $TOKEN"

# Max 100 items per page
curl "http://localhost:8000/api/tasks/?page_size=100" \
  -H "Authorization: Bearer $TOKEN"
```

### Pagination Response Format

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "title": "Task 1",
      ...
    }
  ],
  "pagination": {
    "count": 25,           // Total items
    "page": 1,             // Current page
    "page_size": 10,       // Items per page
    "total_pages": 3,      // Total pages
    "has_next": true,      // Has next page?
    "has_previous": false, // Has previous page?
    "next": "http://localhost:8000/api/tasks/?page=2",
    "previous": null
  }
}
```

---

## 🎯 Combined Filters

### Example 1: High Priority Pending Tasks

```bash
curl "http://localhost:8000/api/tasks/?priority=high&status=pending&ordering=-due_date" \
  -H "Authorization: Bearer $TOKEN"
```

### Example 2: Overdue Tasks, High Priority First

```bash
curl "http://localhost:8000/api/tasks/?is_overdue=true&ordering=priority,-due_date" \
  -H "Authorization: Bearer $TOKEN"
```

### Example 3: Search + Filter + Order + Pagination

```bash
curl "http://localhost:8000/api/tasks/?search=meeting&status=pending&priority=high&ordering=-created_at&page=1&page_size=5" \
  -H "Authorization: Bearer $TOKEN"
```

### Example 4: Category Tasks Due This Week

```bash
curl "http://localhost:8000/api/tasks/?category=1&due_date_from=2026-02-18&due_date_to=2026-02-25&ordering=due_date" \
  -H "Authorization: Bearer $TOKEN"
```

### Example 5: Completed Tasks This Month

```bash
curl "http://localhost:8000/api/tasks/?is_completed=true&created_from=2026-02-01&created_to=2026-02-28&ordering=-completed_at" \
  -H "Authorization: Bearer $TOKEN"
```

---

## ✅ Testing Checklist

### Filtering:
- [ ] Filter by status (pending, in_progress, done)
- [ ] Filter by priority (low, medium, high)
- [ ] Filter by category
- [ ] Filter by due_date range
- [ ] Filter by created_at range
- [ ] Filter is_completed (true/false)
- [ ] Filter is_overdue (true/false)
- [ ] Filter has_category (true/false)
- [ ] Combine multiple filters

### Search:
- [ ] Search tasks by title
- [ ] Search tasks by description
- [ ] Search case-insensitive
- [ ] Search categories by name

### Ordering:
- [ ] Order by created_at (asc/desc)
- [ ] Order by due_date (asc/desc)
- [ ] Order by priority
- [ ] Order by status
- [ ] Order by updated_at
- [ ] Multiple field ordering

### Pagination:
- [ ] Default pagination (10 items)
- [ ] Custom page_size
- [ ] Navigate between pages
- [ ] Pagination with filters
- [ ] Pagination response format correct
- [ ] Max page_size limit (100) enforced

---

## 🔧 Testing dengan Swagger UI

Untuk testing lebih mudah dengan UI interaktif:

**http://localhost:8000/api/docs/**

1. Klik "Authorize"
2. Input: `Bearer your_token`
3. Test semua endpoints dengan filter UI

**Tips:** Swagger UI akan menampilkan semua filter options secara otomatis!

---

## 📚 Query Parameter Reference

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `status` | string | Filter by status | `?status=pending` |
| `priority` | string | Filter by priority | `?priority=high` |
| `category` | integer | Filter by category ID | `?category=1` |
| `due_date_from` | datetime | Due date from | `?due_date_from=2026-01-01` |
| `due_date_to` | datetime | Due date to | `?due_date_to=2026-12-31` |
| `created_from` | datetime | Created from | `?created_from=2026-02-01` |
| `created_to` | datetime | Created to | `?created_to=2026-02-28` |
| `is_completed` | boolean | Completed status | `?is_completed=true` |
| `is_overdue` | boolean | Overdue status | `?is_overdue=true` |
| `has_category` | boolean | Has category | `?has_category=true` |
| `search` | string | Search in title/description | `?search=meeting` |
| `ordering` | string | Sort fields | `?ordering=-created_at` |
| `page` | integer | Page number | `?page=2` |
| `page_size` | integer | Items per page (max 100) | `?page_size=20` |

---

## 🐛 Common Issues

### Issue: No results with filters
**Solution:** Check if filter values are correct (e.g., status values: pending, in_progress, done)

### Issue: Date filters not working
**Solution:** Use ISO format: `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SSZ`

### Issue: Ordering not applied
**Solution:** Use `-` prefix for descending order (e.g., `-created_at`)

### Issue: Pagination returns empty
**Solution:** Check if page number exists (e.g., don't request page 10 if only 2 pages exist)

---

## 📖 Next Steps

Semua fitur filtering, search, dan pagination sudah berfungsi! Lanjut ke:
- **Step 5**: Unit Testing & Integration Testing
- Atau lanjut improve dengan custom analytics endpoints
