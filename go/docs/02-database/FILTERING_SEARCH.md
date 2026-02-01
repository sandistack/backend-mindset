# 🔍 Filtering & Search di Go

## Kenapa Penting?

API yang baik memungkinkan client untuk:
- ✅ Filter data berdasarkan kriteria
- ✅ Search dengan keyword
- ✅ Sort berdasarkan field
- ✅ Combine multiple filters

---

## 📚 Daftar Isi

1. [Basic Filtering](#1️⃣-basic-filtering)
2. [Query Builder Pattern](#2️⃣-query-builder-pattern)
3. [GORM Filtering](#3️⃣-gorm-filtering)
4. [Search Implementation](#4️⃣-search-implementation)
5. [Full-Text Search](#5️⃣-full-text-search)
6. [Advanced Filters](#6️⃣-advanced-filters)

---

## 1️⃣ Basic Filtering

### Parse Query Parameters

```go
// internal/api/handlers/task.go
func (h *TaskHandler) List(w http.ResponseWriter, r *http.Request) {
    // Parse filters from query params
    filter := TaskFilter{
        Status:   r.URL.Query().Get("status"),
        Priority: r.URL.Query().Get("priority"),
        Search:   r.URL.Query().Get("search"),
    }
    
    // Parse pagination
    page, _ := strconv.Atoi(r.URL.Query().Get("page"))
    if page < 1 {
        page = 1
    }
    
    pageSize, _ := strconv.Atoi(r.URL.Query().Get("page_size"))
    if pageSize < 1 || pageSize > 100 {
        pageSize = 20
    }
    
    // Parse sorting
    sortBy := r.URL.Query().Get("sort_by")
    sortOrder := r.URL.Query().Get("sort_order")
    
    tasks, total, err := h.service.List(r.Context(), filter, page, pageSize, sortBy, sortOrder)
    if err != nil {
        response.HandleError(w, err)
        return
    }
    
    response.Paginated(w, tasks, page, pageSize, total)
}
```

### Filter Struct

```go
// internal/domain/task.go
package domain

type TaskFilter struct {
    Status    string
    Priority  string
    UserID    *int
    Search    string
    DateFrom  *time.Time
    DateTo    *time.Time
    Tags      []string
}

func (f *TaskFilter) Validate() error {
    if f.Status != "" && !isValidStatus(f.Status) {
        return errors.New("invalid status")
    }
    if f.Priority != "" && !isValidPriority(f.Priority) {
        return errors.New("invalid priority")
    }
    return nil
}
```

---

## 2️⃣ Query Builder Pattern

### Raw SQL Builder

```go
// internal/repository/task_repo.go
package repository

import (
    "database/sql"
    "fmt"
    "strings"
)

type TaskRepository struct {
    db *sql.DB
}

func (r *TaskRepository) List(ctx context.Context, filter TaskFilter, page, pageSize int, sortBy, sortOrder string) ([]Task, int, error) {
    // Build WHERE clause
    conditions := []string{"1=1"}
    args := []interface{}{}
    argIndex := 1
    
    if filter.Status != "" {
        conditions = append(conditions, fmt.Sprintf("status = $%d", argIndex))
        args = append(args, filter.Status)
        argIndex++
    }
    
    if filter.Priority != "" {
        conditions = append(conditions, fmt.Sprintf("priority = $%d", argIndex))
        args = append(args, filter.Priority)
        argIndex++
    }
    
    if filter.UserID != nil {
        conditions = append(conditions, fmt.Sprintf("user_id = $%d", argIndex))
        args = append(args, *filter.UserID)
        argIndex++
    }
    
    if filter.Search != "" {
        conditions = append(conditions, fmt.Sprintf("(title ILIKE $%d OR description ILIKE $%d)", argIndex, argIndex))
        args = append(args, "%"+filter.Search+"%")
        argIndex++
    }
    
    if filter.DateFrom != nil {
        conditions = append(conditions, fmt.Sprintf("created_at >= $%d", argIndex))
        args = append(args, *filter.DateFrom)
        argIndex++
    }
    
    if filter.DateTo != nil {
        conditions = append(conditions, fmt.Sprintf("created_at <= $%d", argIndex))
        args = append(args, *filter.DateTo)
        argIndex++
    }
    
    whereClause := strings.Join(conditions, " AND ")
    
    // Build ORDER BY
    orderBy := "created_at DESC"
    if sortBy != "" {
        allowedSorts := map[string]bool{"created_at": true, "title": true, "priority": true, "status": true}
        if allowedSorts[sortBy] {
            order := "ASC"
            if strings.ToUpper(sortOrder) == "DESC" {
                order = "DESC"
            }
            orderBy = fmt.Sprintf("%s %s", sortBy, order)
        }
    }
    
    // Count total
    countQuery := fmt.Sprintf("SELECT COUNT(*) FROM tasks WHERE %s", whereClause)
    var total int
    if err := r.db.QueryRowContext(ctx, countQuery, args...).Scan(&total); err != nil {
        return nil, 0, err
    }
    
    // Get data with pagination
    offset := (page - 1) * pageSize
    query := fmt.Sprintf(`
        SELECT id, user_id, title, description, status, priority, created_at, updated_at
        FROM tasks
        WHERE %s
        ORDER BY %s
        LIMIT $%d OFFSET $%d
    `, whereClause, orderBy, argIndex, argIndex+1)
    
    args = append(args, pageSize, offset)
    
    rows, err := r.db.QueryContext(ctx, query, args...)
    if err != nil {
        return nil, 0, err
    }
    defer rows.Close()
    
    var tasks []Task
    for rows.Next() {
        var task Task
        if err := rows.Scan(
            &task.ID, &task.UserID, &task.Title, &task.Description,
            &task.Status, &task.Priority, &task.CreatedAt, &task.UpdatedAt,
        ); err != nil {
            return nil, 0, err
        }
        tasks = append(tasks, task)
    }
    
    return tasks, total, nil
}
```

### Fluent Query Builder

```go
// internal/repository/query_builder.go
package repository

type QueryBuilder struct {
    table      string
    conditions []string
    args       []interface{}
    orderBy    string
    limit      int
    offset     int
}

func NewQueryBuilder(table string) *QueryBuilder {
    return &QueryBuilder{
        table:      table,
        conditions: []string{},
        args:       []interface{}{},
    }
}

func (qb *QueryBuilder) Where(condition string, args ...interface{}) *QueryBuilder {
    qb.conditions = append(qb.conditions, condition)
    qb.args = append(qb.args, args...)
    return qb
}

func (qb *QueryBuilder) WhereIf(condition bool, clause string, args ...interface{}) *QueryBuilder {
    if condition {
        return qb.Where(clause, args...)
    }
    return qb
}

func (qb *QueryBuilder) OrderBy(order string) *QueryBuilder {
    qb.orderBy = order
    return qb
}

func (qb *QueryBuilder) Paginate(page, pageSize int) *QueryBuilder {
    qb.limit = pageSize
    qb.offset = (page - 1) * pageSize
    return qb
}

func (qb *QueryBuilder) BuildSelect(columns string) (string, []interface{}) {
    query := fmt.Sprintf("SELECT %s FROM %s", columns, qb.table)
    
    if len(qb.conditions) > 0 {
        // Replace placeholders with PostgreSQL-style $1, $2, etc.
        where := strings.Join(qb.conditions, " AND ")
        query += " WHERE " + qb.replacePlaceholders(where)
    }
    
    if qb.orderBy != "" {
        query += " ORDER BY " + qb.orderBy
    }
    
    if qb.limit > 0 {
        query += fmt.Sprintf(" LIMIT %d OFFSET %d", qb.limit, qb.offset)
    }
    
    return query, qb.args
}

func (qb *QueryBuilder) replacePlaceholders(query string) string {
    result := query
    for i := range qb.args {
        result = strings.Replace(result, "?", fmt.Sprintf("$%d", i+1), 1)
    }
    return result
}

// Usage
func (r *TaskRepository) ListWithBuilder(ctx context.Context, filter TaskFilter, page, pageSize int) ([]Task, error) {
    qb := NewQueryBuilder("tasks").
        WhereIf(filter.Status != "", "status = ?", filter.Status).
        WhereIf(filter.Priority != "", "priority = ?", filter.Priority).
        WhereIf(filter.Search != "", "(title ILIKE ? OR description ILIKE ?)", "%"+filter.Search+"%", "%"+filter.Search+"%").
        OrderBy("created_at DESC").
        Paginate(page, pageSize)
    
    query, args := qb.BuildSelect("*")
    
    rows, err := r.db.QueryContext(ctx, query, args...)
    // ... rest of the code
}
```

---

## 3️⃣ GORM Filtering

### Basic GORM Filtering

```go
// internal/repository/task_gorm.go
package repository

import (
    "gorm.io/gorm"
)

type TaskGORMRepository struct {
    db *gorm.DB
}

func (r *TaskGORMRepository) List(ctx context.Context, filter TaskFilter, page, pageSize int, sortBy, sortOrder string) ([]Task, int64, error) {
    var tasks []Task
    var total int64
    
    query := r.db.WithContext(ctx).Model(&Task{})
    
    // Apply filters
    if filter.Status != "" {
        query = query.Where("status = ?", filter.Status)
    }
    
    if filter.Priority != "" {
        query = query.Where("priority = ?", filter.Priority)
    }
    
    if filter.UserID != nil {
        query = query.Where("user_id = ?", *filter.UserID)
    }
    
    if filter.Search != "" {
        search := "%" + filter.Search + "%"
        query = query.Where("title ILIKE ? OR description ILIKE ?", search, search)
    }
    
    if filter.DateFrom != nil {
        query = query.Where("created_at >= ?", *filter.DateFrom)
    }
    
    if filter.DateTo != nil {
        query = query.Where("created_at <= ?", *filter.DateTo)
    }
    
    if len(filter.Tags) > 0 {
        query = query.Joins("JOIN task_tags ON task_tags.task_id = tasks.id").
            Where("task_tags.tag_id IN ?", filter.Tags)
    }
    
    // Count total
    if err := query.Count(&total).Error; err != nil {
        return nil, 0, err
    }
    
    // Apply sorting
    order := "created_at DESC"
    if sortBy != "" {
        allowedSorts := map[string]bool{"created_at": true, "title": true, "priority": true}
        if allowedSorts[sortBy] {
            order = sortBy
            if strings.ToUpper(sortOrder) == "DESC" {
                order += " DESC"
            } else {
                order += " ASC"
            }
        }
    }
    query = query.Order(order)
    
    // Apply pagination
    offset := (page - 1) * pageSize
    if err := query.Limit(pageSize).Offset(offset).Find(&tasks).Error; err != nil {
        return nil, 0, err
    }
    
    return tasks, total, nil
}
```

### GORM Scopes

```go
// internal/repository/scopes.go
package repository

import "gorm.io/gorm"

// Reusable scopes
func StatusScope(status string) func(*gorm.DB) *gorm.DB {
    return func(db *gorm.DB) *gorm.DB {
        if status != "" {
            return db.Where("status = ?", status)
        }
        return db
    }
}

func PriorityScope(priority string) func(*gorm.DB) *gorm.DB {
    return func(db *gorm.DB) *gorm.DB {
        if priority != "" {
            return db.Where("priority = ?", priority)
        }
        return db
    }
}

func SearchScope(search string) func(*gorm.DB) *gorm.DB {
    return func(db *gorm.DB) *gorm.DB {
        if search != "" {
            pattern := "%" + search + "%"
            return db.Where("title ILIKE ? OR description ILIKE ?", pattern, pattern)
        }
        return db
    }
}

func DateRangeScope(from, to *time.Time) func(*gorm.DB) *gorm.DB {
    return func(db *gorm.DB) *gorm.DB {
        if from != nil {
            db = db.Where("created_at >= ?", *from)
        }
        if to != nil {
            db = db.Where("created_at <= ?", *to)
        }
        return db
    }
}

func PaginationScope(page, pageSize int) func(*gorm.DB) *gorm.DB {
    return func(db *gorm.DB) *gorm.DB {
        offset := (page - 1) * pageSize
        return db.Limit(pageSize).Offset(offset)
    }
}

// Usage with scopes
func (r *TaskGORMRepository) ListWithScopes(ctx context.Context, filter TaskFilter, page, pageSize int) ([]Task, int64, error) {
    var tasks []Task
    var total int64
    
    query := r.db.WithContext(ctx).Model(&Task{}).
        Scopes(
            StatusScope(filter.Status),
            PriorityScope(filter.Priority),
            SearchScope(filter.Search),
            DateRangeScope(filter.DateFrom, filter.DateTo),
        )
    
    // Count before pagination
    query.Count(&total)
    
    // Apply pagination and get data
    err := query.Scopes(PaginationScope(page, pageSize)).
        Order("created_at DESC").
        Find(&tasks).Error
    
    return tasks, total, err
}
```

---

## 4️⃣ Search Implementation

### Basic Search

```go
// internal/service/task_service.go
func (s *TaskService) Search(ctx context.Context, query string, page, pageSize int) ([]Task, int, error) {
    if query == "" {
        return s.List(ctx, TaskFilter{}, page, pageSize, "", "")
    }
    
    // Sanitize query
    query = strings.TrimSpace(query)
    if len(query) < 2 {
        return nil, 0, errors.New("search query too short")
    }
    
    return s.repo.Search(ctx, query, page, pageSize)
}

// Repository
func (r *TaskRepository) Search(ctx context.Context, query string, page, pageSize int) ([]Task, int, error) {
    pattern := "%" + query + "%"
    offset := (page - 1) * pageSize
    
    // Count
    var total int
    countSQL := `
        SELECT COUNT(*) FROM tasks
        WHERE title ILIKE $1 OR description ILIKE $1
    `
    if err := r.db.QueryRowContext(ctx, countSQL, pattern).Scan(&total); err != nil {
        return nil, 0, err
    }
    
    // Search
    searchSQL := `
        SELECT id, title, description, status, priority, created_at
        FROM tasks
        WHERE title ILIKE $1 OR description ILIKE $1
        ORDER BY 
            CASE WHEN title ILIKE $2 THEN 0 ELSE 1 END,
            created_at DESC
        LIMIT $3 OFFSET $4
    `
    
    exactPattern := query + "%"
    rows, err := r.db.QueryContext(ctx, searchSQL, pattern, exactPattern, pageSize, offset)
    if err != nil {
        return nil, 0, err
    }
    defer rows.Close()
    
    var tasks []Task
    for rows.Next() {
        var task Task
        if err := rows.Scan(&task.ID, &task.Title, &task.Description, &task.Status, &task.Priority, &task.CreatedAt); err != nil {
            return nil, 0, err
        }
        tasks = append(tasks, task)
    }
    
    return tasks, total, nil
}
```

### Weighted Search

```go
// Search with relevance scoring
func (r *TaskRepository) WeightedSearch(ctx context.Context, query string, page, pageSize int) ([]Task, int, error) {
    offset := (page - 1) * pageSize
    pattern := "%" + query + "%"
    
    searchSQL := `
        WITH ranked_tasks AS (
            SELECT 
                id, title, description, status, priority, created_at,
                CASE 
                    WHEN title ILIKE $1 THEN 100
                    WHEN title ILIKE $2 THEN 80
                    WHEN description ILIKE $1 THEN 50
                    WHEN description ILIKE $2 THEN 30
                    ELSE 0
                END as relevance
            FROM tasks
            WHERE title ILIKE $2 OR description ILIKE $2
        )
        SELECT id, title, description, status, priority, created_at
        FROM ranked_tasks
        WHERE relevance > 0
        ORDER BY relevance DESC, created_at DESC
        LIMIT $3 OFFSET $4
    `
    
    exactPattern := query + "%"
    rows, err := r.db.QueryContext(ctx, searchSQL, query, pattern, pageSize, offset)
    // ... process rows
}
```

---

## 5️⃣ Full-Text Search

### PostgreSQL Full-Text Search

```sql
-- Migration: Add tsvector column
ALTER TABLE tasks ADD COLUMN search_vector tsvector;

-- Update existing data
UPDATE tasks SET search_vector = 
    setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(description, '')), 'B');

-- Create index
CREATE INDEX idx_tasks_search ON tasks USING GIN(search_vector);

-- Trigger for automatic update
CREATE OR REPLACE FUNCTION tasks_search_trigger() RETURNS trigger AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(NEW.description, '')), 'B');
    RETURN NEW;
END
$$ LANGUAGE plpgsql;

CREATE TRIGGER tasks_search_update
    BEFORE INSERT OR UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION tasks_search_trigger();
```

### Go Implementation

```go
// internal/repository/task_search.go
func (r *TaskRepository) FullTextSearch(ctx context.Context, query string, page, pageSize int) ([]Task, int, error) {
    offset := (page - 1) * pageSize
    
    // Parse query for PostgreSQL tsquery
    tsQuery := strings.Join(strings.Fields(query), " & ")
    
    // Count
    countSQL := `
        SELECT COUNT(*) FROM tasks
        WHERE search_vector @@ plainto_tsquery('english', $1)
    `
    var total int
    if err := r.db.QueryRowContext(ctx, countSQL, query).Scan(&total); err != nil {
        return nil, 0, err
    }
    
    // Search with ranking
    searchSQL := `
        SELECT 
            id, title, description, status, priority, created_at,
            ts_rank(search_vector, plainto_tsquery('english', $1)) as rank
        FROM tasks
        WHERE search_vector @@ plainto_tsquery('english', $1)
        ORDER BY rank DESC, created_at DESC
        LIMIT $2 OFFSET $3
    `
    
    rows, err := r.db.QueryContext(ctx, searchSQL, query, pageSize, offset)
    if err != nil {
        return nil, 0, err
    }
    defer rows.Close()
    
    var tasks []Task
    for rows.Next() {
        var task Task
        var rank float64
        if err := rows.Scan(
            &task.ID, &task.Title, &task.Description,
            &task.Status, &task.Priority, &task.CreatedAt, &rank,
        ); err != nil {
            return nil, 0, err
        }
        tasks = append(tasks, task)
    }
    
    return tasks, total, nil
}

// Search with highlights
func (r *TaskRepository) SearchWithHighlight(ctx context.Context, query string) ([]TaskSearchResult, error) {
    searchSQL := `
        SELECT 
            id,
            ts_headline('english', title, plainto_tsquery('english', $1),
                'StartSel=<mark>, StopSel=</mark>, MaxWords=50') as title_highlight,
            ts_headline('english', description, plainto_tsquery('english', $1),
                'StartSel=<mark>, StopSel=</mark>, MaxWords=100') as description_highlight,
            ts_rank(search_vector, plainto_tsquery('english', $1)) as rank
        FROM tasks
        WHERE search_vector @@ plainto_tsquery('english', $1)
        ORDER BY rank DESC
        LIMIT 20
    `
    
    rows, err := r.db.QueryContext(ctx, searchSQL, query)
    // ... process rows
}
```

---

## 6️⃣ Advanced Filters

### Filter API Design

```go
// GET /api/tasks?filter[status]=TODO&filter[priority]=HIGH&filter[created_at][gte]=2024-01-01

// internal/api/filter_parser.go
package api

type FilterOperator string

const (
    OpEqual        FilterOperator = "eq"
    OpNotEqual     FilterOperator = "ne"
    OpGreaterThan  FilterOperator = "gt"
    OpGreaterEqual FilterOperator = "gte"
    OpLessThan     FilterOperator = "lt"
    OpLessEqual    FilterOperator = "lte"
    OpIn           FilterOperator = "in"
    OpContains     FilterOperator = "contains"
)

type FilterCondition struct {
    Field    string
    Operator FilterOperator
    Value    interface{}
}

func ParseFilters(query url.Values) []FilterCondition {
    var conditions []FilterCondition
    
    for key, values := range query {
        if !strings.HasPrefix(key, "filter[") {
            continue
        }
        
        // Parse filter[field] or filter[field][operator]
        parts := strings.Split(strings.Trim(key, "filter[]"), "][")
        
        field := parts[0]
        operator := OpEqual
        if len(parts) > 1 {
            operator = FilterOperator(parts[1])
        }
        
        conditions = append(conditions, FilterCondition{
            Field:    field,
            Operator: operator,
            Value:    values[0],
        })
    }
    
    return conditions
}

// Build SQL from conditions
func BuildFilterSQL(conditions []FilterCondition, allowedFields map[string]string) (string, []interface{}) {
    var clauses []string
    var args []interface{}
    argIndex := 1
    
    for _, cond := range conditions {
        // Map API field to DB column
        dbColumn, ok := allowedFields[cond.Field]
        if !ok {
            continue
        }
        
        var clause string
        switch cond.Operator {
        case OpEqual:
            clause = fmt.Sprintf("%s = $%d", dbColumn, argIndex)
        case OpNotEqual:
            clause = fmt.Sprintf("%s != $%d", dbColumn, argIndex)
        case OpGreaterThan:
            clause = fmt.Sprintf("%s > $%d", dbColumn, argIndex)
        case OpGreaterEqual:
            clause = fmt.Sprintf("%s >= $%d", dbColumn, argIndex)
        case OpLessThan:
            clause = fmt.Sprintf("%s < $%d", dbColumn, argIndex)
        case OpLessEqual:
            clause = fmt.Sprintf("%s <= $%d", dbColumn, argIndex)
        case OpContains:
            clause = fmt.Sprintf("%s ILIKE $%d", dbColumn, argIndex)
            cond.Value = "%" + cond.Value.(string) + "%"
        case OpIn:
            values := strings.Split(cond.Value.(string), ",")
            placeholders := make([]string, len(values))
            for i := range values {
                placeholders[i] = fmt.Sprintf("$%d", argIndex+i)
                args = append(args, values[i])
            }
            clause = fmt.Sprintf("%s IN (%s)", dbColumn, strings.Join(placeholders, ","))
            argIndex += len(values) - 1
        }
        
        if clause != "" {
            clauses = append(clauses, clause)
            if cond.Operator != OpIn {
                args = append(args, cond.Value)
            }
            argIndex++
        }
    }
    
    return strings.Join(clauses, " AND "), args
}
```

---

## 📋 Filtering Checklist

### Junior ✅
- [ ] Parse query parameters
- [ ] Basic WHERE clauses
- [ ] Simple LIKE search

### Mid ✅
- [ ] Query builder pattern
- [ ] GORM scopes
- [ ] Sorting & pagination
- [ ] Input validation

### Senior ✅
- [ ] Full-text search (PostgreSQL)
- [ ] Weighted search results
- [ ] Search highlighting
- [ ] Complex filter operators

### Expert ✅
- [ ] Filter API design (JSON:API style)
- [ ] Elasticsearch integration
- [ ] Search analytics
- [ ] Query optimization
