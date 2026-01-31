# 📄 PAGINATION - Pagination & Filtering di Go (Junior → Senior)

Dokumentasi lengkap tentang pagination, filtering, dan sorting di Go.

---

## 🎯 Mengapa Pagination Penting?

```
Tanpa Pagination:
- Memory overload (load semua data)
- Slow response (transfer banyak data)
- Bad UX (user kewalahan)

Dengan Pagination:
- Controlled memory usage
- Fast response
- Better UX

Tipe Pagination:
1. Offset-based: ?page=1&limit=10 (simple, traditional)
2. Cursor-based: ?cursor=abc123 (scalable, real-time)
```

---

## 1️⃣ JUNIOR LEVEL - Basic Pagination

### Offset-Based Pagination

```go
package main

import (
    "math"
    "net/http"
    "strconv"
    
    "github.com/gin-gonic/gin"
    "gorm.io/gorm"
)

type User struct {
    ID    uint   `json:"id"`
    Name  string `json:"name"`
    Email string `json:"email"`
}

type PaginationMeta struct {
    Page       int   `json:"page"`
    PerPage    int   `json:"per_page"`
    Total      int64 `json:"total"`
    TotalPages int   `json:"total_pages"`
}

type PaginatedResponse struct {
    Success bool           `json:"success"`
    Data    interface{}    `json:"data"`
    Meta    PaginationMeta `json:"meta"`
}

func getUsers(c *gin.Context, db *gorm.DB) {
    // Parse query params
    page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
    limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
    
    // Validate
    if page < 1 {
        page = 1
    }
    if limit < 1 || limit > 100 {
        limit = 10
    }
    
    offset := (page - 1) * limit
    
    // Count total
    var total int64
    db.Model(&User{}).Count(&total)
    
    // Get paginated data
    var users []User
    db.Offset(offset).Limit(limit).Find(&users)
    
    // Calculate total pages
    totalPages := int(math.Ceil(float64(total) / float64(limit)))
    
    c.JSON(http.StatusOK, PaginatedResponse{
        Success: true,
        Data:    users,
        Meta: PaginationMeta{
            Page:       page,
            PerPage:    limit,
            Total:      total,
            TotalPages: totalPages,
        },
    })
}
```

### Response Example

```json
{
  "success": true,
  "data": [
    {"id": 1, "name": "John", "email": "john@example.com"},
    {"id": 2, "name": "Jane", "email": "jane@example.com"}
  ],
  "meta": {
    "page": 1,
    "per_page": 10,
    "total": 100,
    "total_pages": 10
  }
}
```

---

## 2️⃣ MID LEVEL - Reusable Pagination

### Pagination Helper

```go
// pkg/pagination/pagination.go
package pagination

import (
    "math"
    "strconv"
    
    "github.com/gin-gonic/gin"
    "gorm.io/gorm"
)

type Pagination struct {
    Page       int   `json:"page"`
    PerPage    int   `json:"per_page"`
    Total      int64 `json:"total"`
    TotalPages int   `json:"total_pages"`
    HasNext    bool  `json:"has_next"`
    HasPrev    bool  `json:"has_prev"`
}

type Config struct {
    DefaultPage    int
    DefaultPerPage int
    MaxPerPage     int
}

var DefaultConfig = Config{
    DefaultPage:    1,
    DefaultPerPage: 10,
    MaxPerPage:     100,
}

// Parse from request
func Parse(c *gin.Context) (page, perPage int) {
    page, _ = strconv.Atoi(c.DefaultQuery("page", strconv.Itoa(DefaultConfig.DefaultPage)))
    perPage, _ = strconv.Atoi(c.DefaultQuery("per_page", strconv.Itoa(DefaultConfig.DefaultPerPage)))
    
    // Also support "limit" as alias
    if limitStr := c.Query("limit"); limitStr != "" {
        perPage, _ = strconv.Atoi(limitStr)
    }
    
    // Validate
    if page < 1 {
        page = 1
    }
    if perPage < 1 {
        perPage = DefaultConfig.DefaultPerPage
    }
    if perPage > DefaultConfig.MaxPerPage {
        perPage = DefaultConfig.MaxPerPage
    }
    
    return page, perPage
}

// Create pagination meta
func NewPagination(page, perPage int, total int64) Pagination {
    totalPages := int(math.Ceil(float64(total) / float64(perPage)))
    
    return Pagination{
        Page:       page,
        PerPage:    perPage,
        Total:      total,
        TotalPages: totalPages,
        HasNext:    page < totalPages,
        HasPrev:    page > 1,
    }
}

// Apply to GORM query
func Apply(page, perPage int) func(db *gorm.DB) *gorm.DB {
    return func(db *gorm.DB) *gorm.DB {
        offset := (page - 1) * perPage
        return db.Offset(offset).Limit(perPage)
    }
}

// Paginate executes query with pagination
func Paginate[T any](db *gorm.DB, page, perPage int) ([]T, Pagination, error) {
    var items []T
    var total int64
    
    // Count total
    if err := db.Model(new(T)).Count(&total).Error; err != nil {
        return nil, Pagination{}, err
    }
    
    // Get paginated data
    offset := (page - 1) * perPage
    if err := db.Offset(offset).Limit(perPage).Find(&items).Error; err != nil {
        return nil, Pagination{}, err
    }
    
    return items, NewPagination(page, perPage, total), nil
}
```

### Usage

```go
package main

import (
    "net/http"
    
    "github.com/gin-gonic/gin"
    "github.com/username/myapp/pkg/pagination"
)

func getUsers(c *gin.Context) {
    page, perPage := pagination.Parse(c)
    
    users, meta, err := pagination.Paginate[User](db, page, perPage)
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }
    
    c.JSON(http.StatusOK, gin.H{
        "success": true,
        "data":    users,
        "meta":    meta,
    })
}

// Alternative: Using scope
func getUsersWithScope(c *gin.Context) {
    page, perPage := pagination.Parse(c)
    
    var users []User
    var total int64
    
    db.Model(&User{}).Count(&total)
    db.Scopes(pagination.Apply(page, perPage)).Find(&users)
    
    c.JSON(http.StatusOK, gin.H{
        "success": true,
        "data":    users,
        "meta":    pagination.NewPagination(page, perPage, total),
    })
}
```

---

## 3️⃣ MID LEVEL - Filtering

### Basic Filtering

```go
package main

import (
    "net/http"
    "strings"
    
    "github.com/gin-gonic/gin"
    "gorm.io/gorm"
)

type UserFilter struct {
    Name     string `form:"name"`
    Email    string `form:"email"`
    Status   string `form:"status"`
    Role     string `form:"role"`
    IsActive *bool  `form:"is_active"`
    AgeMin   int    `form:"age_min"`
    AgeMax   int    `form:"age_max"`
}

func (f *UserFilter) Apply(db *gorm.DB) *gorm.DB {
    if f.Name != "" {
        db = db.Where("name ILIKE ?", "%"+f.Name+"%")
    }
    if f.Email != "" {
        db = db.Where("email ILIKE ?", "%"+f.Email+"%")
    }
    if f.Status != "" {
        db = db.Where("status = ?", f.Status)
    }
    if f.Role != "" {
        db = db.Where("role = ?", f.Role)
    }
    if f.IsActive != nil {
        db = db.Where("is_active = ?", *f.IsActive)
    }
    if f.AgeMin > 0 {
        db = db.Where("age >= ?", f.AgeMin)
    }
    if f.AgeMax > 0 {
        db = db.Where("age <= ?", f.AgeMax)
    }
    return db
}

func getUsers(c *gin.Context) {
    var filter UserFilter
    if err := c.ShouldBindQuery(&filter); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }
    
    page, perPage := pagination.Parse(c)
    
    var users []User
    var total int64
    
    query := db.Model(&User{})
    query = filter.Apply(query)
    
    query.Count(&total)
    query.Scopes(pagination.Apply(page, perPage)).Find(&users)
    
    c.JSON(http.StatusOK, gin.H{
        "success": true,
        "data":    users,
        "meta":    pagination.NewPagination(page, perPage, total),
    })
}
```

### Request Examples

```bash
# Filter by name
GET /users?name=john

# Filter by multiple fields
GET /users?name=john&status=active&role=admin

# Filter with pagination
GET /users?name=john&page=1&per_page=20

# Filter by boolean
GET /users?is_active=true

# Filter by range
GET /users?age_min=18&age_max=30
```

---

## 4️⃣ MID LEVEL - Sorting

### Basic Sorting

```go
package main

import (
    "net/http"
    "strings"
    
    "github.com/gin-gonic/gin"
    "gorm.io/gorm"
)

type SortConfig struct {
    AllowedFields []string
    DefaultField  string
    DefaultOrder  string
}

var userSortConfig = SortConfig{
    AllowedFields: []string{"id", "name", "email", "created_at", "updated_at"},
    DefaultField:  "created_at",
    DefaultOrder:  "desc",
}

func parseSort(c *gin.Context, config SortConfig) string {
    sortBy := c.DefaultQuery("sort_by", config.DefaultField)
    order := strings.ToLower(c.DefaultQuery("order", config.DefaultOrder))
    
    // Validate sort field
    validField := false
    for _, field := range config.AllowedFields {
        if sortBy == field {
            validField = true
            break
        }
    }
    if !validField {
        sortBy = config.DefaultField
    }
    
    // Validate order
    if order != "asc" && order != "desc" {
        order = config.DefaultOrder
    }
    
    return sortBy + " " + order
}

func getUsers(c *gin.Context) {
    page, perPage := pagination.Parse(c)
    sortOrder := parseSort(c, userSortConfig)
    
    var filter UserFilter
    c.ShouldBindQuery(&filter)
    
    var users []User
    var total int64
    
    query := db.Model(&User{})
    query = filter.Apply(query)
    
    query.Count(&total)
    query.Order(sortOrder).Scopes(pagination.Apply(page, perPage)).Find(&users)
    
    c.JSON(http.StatusOK, gin.H{
        "success": true,
        "data":    users,
        "meta":    pagination.NewPagination(page, perPage, total),
    })
}
```

### Request Examples

```bash
# Sort by name ascending
GET /users?sort_by=name&order=asc

# Sort by created_at descending (newest first)
GET /users?sort_by=created_at&order=desc

# Combined with filter and pagination
GET /users?name=john&sort_by=name&order=asc&page=1&per_page=10
```

---

## 5️⃣ SENIOR LEVEL - Advanced Query Builder

### Query Builder Pattern

```go
// pkg/query/builder.go
package query

import (
    "strings"
    
    "github.com/gin-gonic/gin"
    "gorm.io/gorm"
)

type QueryBuilder struct {
    db         *gorm.DB
    page       int
    perPage    int
    sortField  string
    sortOrder  string
    filters    map[string]interface{}
    search     string
    searchCols []string
}

func NewBuilder(db *gorm.DB) *QueryBuilder {
    return &QueryBuilder{
        db:      db,
        page:    1,
        perPage: 10,
        filters: make(map[string]interface{}),
    }
}

func (b *QueryBuilder) Paginate(page, perPage int) *QueryBuilder {
    b.page = page
    b.perPage = perPage
    return b
}

func (b *QueryBuilder) Sort(field, order string) *QueryBuilder {
    b.sortField = field
    b.sortOrder = order
    return b
}

func (b *QueryBuilder) Where(field string, value interface{}) *QueryBuilder {
    b.filters[field] = value
    return b
}

func (b *QueryBuilder) Search(query string, columns ...string) *QueryBuilder {
    b.search = query
    b.searchCols = columns
    return b
}

func (b *QueryBuilder) Apply() *gorm.DB {
    query := b.db
    
    // Apply filters
    for field, value := range b.filters {
        query = query.Where(field+" = ?", value)
    }
    
    // Apply search
    if b.search != "" && len(b.searchCols) > 0 {
        searchConditions := make([]string, len(b.searchCols))
        searchValues := make([]interface{}, len(b.searchCols))
        
        for i, col := range b.searchCols {
            searchConditions[i] = col + " ILIKE ?"
            searchValues[i] = "%" + b.search + "%"
        }
        
        query = query.Where(
            strings.Join(searchConditions, " OR "),
            searchValues...,
        )
    }
    
    // Apply sort
    if b.sortField != "" {
        order := b.sortOrder
        if order == "" {
            order = "asc"
        }
        query = query.Order(b.sortField + " " + order)
    }
    
    // Apply pagination
    offset := (b.page - 1) * b.perPage
    query = query.Offset(offset).Limit(b.perPage)
    
    return query
}

func (b *QueryBuilder) Count() int64 {
    var count int64
    query := b.db
    
    // Apply filters (same as Apply, without pagination)
    for field, value := range b.filters {
        query = query.Where(field+" = ?", value)
    }
    
    if b.search != "" && len(b.searchCols) > 0 {
        searchConditions := make([]string, len(b.searchCols))
        searchValues := make([]interface{}, len(b.searchCols))
        
        for i, col := range b.searchCols {
            searchConditions[i] = col + " ILIKE ?"
            searchValues[i] = "%" + b.search + "%"
        }
        
        query = query.Where(
            strings.Join(searchConditions, " OR "),
            searchValues...,
        )
    }
    
    query.Count(&count)
    return count
}
```

### Usage

```go
func getUsers(c *gin.Context) {
    page, perPage := pagination.Parse(c)
    search := c.Query("search")
    status := c.Query("status")
    
    builder := query.NewBuilder(db.Model(&User{})).
        Paginate(page, perPage).
        Sort("created_at", "desc").
        Search(search, "name", "email")
    
    if status != "" {
        builder.Where("status", status)
    }
    
    total := builder.Count()
    
    var users []User
    builder.Apply().Find(&users)
    
    c.JSON(http.StatusOK, gin.H{
        "success": true,
        "data":    users,
        "meta":    pagination.NewPagination(page, perPage, total),
    })
}
```

---

## 6️⃣ SENIOR LEVEL - Cursor-Based Pagination

### Why Cursor Pagination?

```
Offset Pagination Problems:
- Slow for large offsets (OFFSET 10000)
- Inconsistent results if data changes
- Can skip/duplicate items

Cursor Pagination Benefits:
- Consistent performance
- No skipped/duplicate items
- Better for real-time data
```

### Implementation

```go
package pagination

import (
    "encoding/base64"
    "encoding/json"
    "fmt"
    "time"
    
    "github.com/gin-gonic/gin"
    "gorm.io/gorm"
)

type Cursor struct {
    ID        uint      `json:"id"`
    CreatedAt time.Time `json:"created_at"`
}

type CursorPagination struct {
    NextCursor string `json:"next_cursor,omitempty"`
    PrevCursor string `json:"prev_cursor,omitempty"`
    HasMore    bool   `json:"has_more"`
    Limit      int    `json:"limit"`
}

func EncodeCursor(id uint, createdAt time.Time) string {
    cursor := Cursor{ID: id, CreatedAt: createdAt}
    data, _ := json.Marshal(cursor)
    return base64.URLEncoding.EncodeToString(data)
}

func DecodeCursor(encoded string) (*Cursor, error) {
    if encoded == "" {
        return nil, nil
    }
    
    data, err := base64.URLEncoding.DecodeString(encoded)
    if err != nil {
        return nil, err
    }
    
    var cursor Cursor
    if err := json.Unmarshal(data, &cursor); err != nil {
        return nil, err
    }
    
    return &cursor, nil
}

func CursorPaginate[T any](
    db *gorm.DB,
    cursorStr string,
    limit int,
    idField, createdAtField string,
) ([]T, CursorPagination, error) {
    
    cursor, err := DecodeCursor(cursorStr)
    if err != nil {
        return nil, CursorPagination{}, err
    }
    
    // Limit validation
    if limit <= 0 || limit > 100 {
        limit = 10
    }
    
    query := db
    
    // Apply cursor
    if cursor != nil {
        query = query.Where(
            fmt.Sprintf("(%s, %s) < (?, ?)", createdAtField, idField),
            cursor.CreatedAt,
            cursor.ID,
        )
    }
    
    // Order by created_at DESC, id DESC for consistent ordering
    query = query.Order(fmt.Sprintf("%s DESC, %s DESC", createdAtField, idField))
    
    // Fetch one extra to check if there are more
    var items []T
    if err := query.Limit(limit + 1).Find(&items).Error; err != nil {
        return nil, CursorPagination{}, err
    }
    
    hasMore := len(items) > limit
    if hasMore {
        items = items[:limit] // Remove extra item
    }
    
    var nextCursor string
    if hasMore && len(items) > 0 {
        // Get last item's cursor
        // This requires reflection or interface for generic approach
        // Simplified: assume items have ID and CreatedAt
    }
    
    return items, CursorPagination{
        NextCursor: nextCursor,
        HasMore:    hasMore,
        Limit:      limit,
    }, nil
}
```

### Simplified Cursor Implementation

```go
package main

import (
    "encoding/base64"
    "net/http"
    "strconv"
    
    "github.com/gin-gonic/gin"
    "gorm.io/gorm"
)

type User struct {
    ID        uint      `json:"id"`
    Name      string    `json:"name"`
    CreatedAt time.Time `json:"created_at"`
}

type CursorResponse struct {
    Success    bool        `json:"success"`
    Data       interface{} `json:"data"`
    NextCursor string      `json:"next_cursor,omitempty"`
    HasMore    bool        `json:"has_more"`
}

func getUsersWithCursor(c *gin.Context, db *gorm.DB) {
    limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
    cursorStr := c.Query("cursor")
    
    if limit <= 0 || limit > 100 {
        limit = 10
    }
    
    query := db.Model(&User{}).Order("id DESC")
    
    // Decode cursor (cursor is just base64 encoded ID)
    if cursorStr != "" {
        decoded, err := base64.URLEncoding.DecodeString(cursorStr)
        if err == nil {
            lastID, _ := strconv.Atoi(string(decoded))
            query = query.Where("id < ?", lastID)
        }
    }
    
    // Fetch one extra
    var users []User
    query.Limit(limit + 1).Find(&users)
    
    hasMore := len(users) > limit
    if hasMore {
        users = users[:limit]
    }
    
    var nextCursor string
    if hasMore && len(users) > 0 {
        lastUser := users[len(users)-1]
        nextCursor = base64.URLEncoding.EncodeToString(
            []byte(strconv.Itoa(int(lastUser.ID))),
        )
    }
    
    c.JSON(http.StatusOK, CursorResponse{
        Success:    true,
        Data:       users,
        NextCursor: nextCursor,
        HasMore:    hasMore,
    })
}
```

### Request Examples

```bash
# First page
GET /users?limit=10

# Next page with cursor
GET /users?limit=10&cursor=MTIz

# Response
{
  "success": true,
  "data": [...],
  "next_cursor": "MTIz",
  "has_more": true
}
```

---

## 7️⃣ EXPERT LEVEL - Complete Query Service

```go
// internal/service/query_service.go
package service

import (
    "math"
    "strings"
    
    "github.com/gin-gonic/gin"
    "gorm.io/gorm"
)

type QueryParams struct {
    Page      int               `form:"page"`
    PerPage   int               `form:"per_page"`
    SortBy    string            `form:"sort_by"`
    Order     string            `form:"order"`
    Search    string            `form:"search"`
    Filters   map[string]string `form:"-"`
}

type QueryResult[T any] struct {
    Items      []T         `json:"items"`
    Pagination *Pagination `json:"pagination"`
}

type Pagination struct {
    Page       int   `json:"page"`
    PerPage    int   `json:"per_page"`
    Total      int64 `json:"total"`
    TotalPages int   `json:"total_pages"`
    HasNext    bool  `json:"has_next"`
    HasPrev    bool  `json:"has_prev"`
}

type QueryConfig struct {
    DefaultPerPage   int
    MaxPerPage       int
    AllowedSortBy    []string
    DefaultSortBy    string
    DefaultOrder     string
    SearchableFields []string
    FilterableFields []string
}

type QueryService[T any] struct {
    db     *gorm.DB
    config QueryConfig
}

func NewQueryService[T any](db *gorm.DB, config QueryConfig) *QueryService[T] {
    if config.DefaultPerPage == 0 {
        config.DefaultPerPage = 10
    }
    if config.MaxPerPage == 0 {
        config.MaxPerPage = 100
    }
    if config.DefaultOrder == "" {
        config.DefaultOrder = "desc"
    }
    
    return &QueryService[T]{db: db, config: config}
}

func (s *QueryService[T]) ParseParams(c *gin.Context) QueryParams {
    params := QueryParams{
        Page:    1,
        PerPage: s.config.DefaultPerPage,
        SortBy:  s.config.DefaultSortBy,
        Order:   s.config.DefaultOrder,
        Filters: make(map[string]string),
    }
    
    c.ShouldBindQuery(&params)
    
    // Validate
    if params.Page < 1 {
        params.Page = 1
    }
    if params.PerPage < 1 || params.PerPage > s.config.MaxPerPage {
        params.PerPage = s.config.DefaultPerPage
    }
    
    // Validate sort
    if !s.isAllowedSort(params.SortBy) {
        params.SortBy = s.config.DefaultSortBy
    }
    if params.Order != "asc" && params.Order != "desc" {
        params.Order = s.config.DefaultOrder
    }
    
    // Extract filters
    for _, field := range s.config.FilterableFields {
        if value := c.Query(field); value != "" {
            params.Filters[field] = value
        }
    }
    
    return params
}

func (s *QueryService[T]) isAllowedSort(field string) bool {
    for _, allowed := range s.config.AllowedSortBy {
        if field == allowed {
            return true
        }
    }
    return false
}

func (s *QueryService[T]) Execute(params QueryParams) (*QueryResult[T], error) {
    query := s.db.Model(new(T))
    
    // Apply search
    if params.Search != "" && len(s.config.SearchableFields) > 0 {
        conditions := make([]string, len(s.config.SearchableFields))
        values := make([]interface{}, len(s.config.SearchableFields))
        
        for i, field := range s.config.SearchableFields {
            conditions[i] = field + " ILIKE ?"
            values[i] = "%" + params.Search + "%"
        }
        
        query = query.Where(strings.Join(conditions, " OR "), values...)
    }
    
    // Apply filters
    for field, value := range params.Filters {
        query = query.Where(field+" = ?", value)
    }
    
    // Count
    var total int64
    if err := query.Count(&total).Error; err != nil {
        return nil, err
    }
    
    // Apply sort
    if params.SortBy != "" {
        query = query.Order(params.SortBy + " " + params.Order)
    }
    
    // Apply pagination
    offset := (params.Page - 1) * params.PerPage
    query = query.Offset(offset).Limit(params.PerPage)
    
    // Execute
    var items []T
    if err := query.Find(&items).Error; err != nil {
        return nil, err
    }
    
    totalPages := int(math.Ceil(float64(total) / float64(params.PerPage)))
    
    return &QueryResult[T]{
        Items: items,
        Pagination: &Pagination{
            Page:       params.Page,
            PerPage:    params.PerPage,
            Total:      total,
            TotalPages: totalPages,
            HasNext:    params.Page < totalPages,
            HasPrev:    params.Page > 1,
        },
    }, nil
}
```

### Usage

```go
package main

func main() {
    userQueryService := service.NewQueryService[User](db, service.QueryConfig{
        DefaultPerPage:   10,
        MaxPerPage:       50,
        AllowedSortBy:    []string{"id", "name", "email", "created_at"},
        DefaultSortBy:    "created_at",
        DefaultOrder:     "desc",
        SearchableFields: []string{"name", "email"},
        FilterableFields: []string{"status", "role", "is_active"},
    })
    
    r.GET("/users", func(c *gin.Context) {
        params := userQueryService.ParseParams(c)
        result, err := userQueryService.Execute(params)
        
        if err != nil {
            c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
            return
        }
        
        c.JSON(http.StatusOK, gin.H{
            "success": true,
            "data":    result.Items,
            "meta":    result.Pagination,
        })
    })
}
```

---

## 📊 Pagination Comparison

| Type | Pros | Cons | Use Case |
|------|------|------|----------|
| **Offset** | Simple, random access | Slow for large offsets | Admin panels, small datasets |
| **Cursor** | Consistent, fast | No random access | Feeds, real-time data |
| **Keyset** | Best performance | Complex implementation | Large datasets |

---

## 💡 Summary

| Level | Focus |
|-------|-------|
| **Junior** | Basic offset pagination |
| **Mid** | Reusable helpers, filtering, sorting |
| **Mid-Senior** | Query builder pattern |
| **Senior** | Cursor pagination |
| **Expert** | Complete query service |

**Best Practices:**
- ✅ Always limit maximum per_page
- ✅ Validate and sanitize sort fields
- ✅ Use indexes on filtered/sorted columns
- ✅ Use cursor for large/real-time datasets
- ✅ Include metadata in response
- ❌ Don't allow arbitrary sort fields (SQL injection)
- ❌ Don't use offset for very large datasets
