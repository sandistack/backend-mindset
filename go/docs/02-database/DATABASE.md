# 🗄️ DATABASE - SQL & GORM di Go (Junior → Senior)

Dokumentasi lengkap tentang database operations di Go menggunakan database/sql dan GORM.

---

## 🎯 Database Libraries di Go

```
1. database/sql (Standard Library)
   - Low-level, full control
   - Butuh SQL driver (pq, mysql, sqlite3)

2. GORM (Object-Relational Mapping)
   - High-level, abstraction
   - Auto migrations, associations
   - Paling populer

3. sqlx
   - Extension dari database/sql
   - Struct scanning, named parameters

4. sqlc
   - Generate type-safe Go from SQL
   - Compile-time checks

Rekomendasi: GORM untuk rapid development
```

---

## 1️⃣ JUNIOR LEVEL - database/sql Basics

### Installation

```bash
# PostgreSQL driver
go get github.com/lib/pq

# MySQL driver
go get github.com/go-sql-driver/mysql

# SQLite driver
go get github.com/mattn/go-sqlite3
```

### Basic Connection

```go
package main

import (
    "database/sql"
    "fmt"
    "log"
    
    _ "github.com/lib/pq" // PostgreSQL driver
)

func main() {
    // Connection string
    connStr := "host=localhost port=5432 user=postgres password=secret dbname=mydb sslmode=disable"
    
    // Open connection
    db, err := sql.Open("postgres", connStr)
    if err != nil {
        log.Fatal(err)
    }
    defer db.Close()
    
    // Verify connection
    if err := db.Ping(); err != nil {
        log.Fatal(err)
    }
    
    fmt.Println("Connected to database!")
}
```

### Basic CRUD Operations

```go
package main

import (
    "database/sql"
    "fmt"
    "log"
    "time"
    
    _ "github.com/lib/pq"
)

type User struct {
    ID        int
    Name      string
    Email     string
    CreatedAt time.Time
}

func main() {
    db, err := sql.Open("postgres", "...")
    if err != nil {
        log.Fatal(err)
    }
    defer db.Close()
    
    // CREATE
    createUser(db, "John", "john@example.com")
    
    // READ
    user, _ := getUserByID(db, 1)
    fmt.Printf("User: %+v\n", user)
    
    // READ ALL
    users, _ := getAllUsers(db)
    fmt.Printf("All users: %+v\n", users)
    
    // UPDATE
    updateUser(db, 1, "John Doe", "johndoe@example.com")
    
    // DELETE
    deleteUser(db, 1)
}

// CREATE
func createUser(db *sql.DB, name, email string) (int, error) {
    var id int
    query := `
        INSERT INTO users (name, email, created_at)
        VALUES ($1, $2, $3)
        RETURNING id
    `
    err := db.QueryRow(query, name, email, time.Now()).Scan(&id)
    return id, err
}

// READ ONE
func getUserByID(db *sql.DB, id int) (*User, error) {
    user := &User{}
    query := `SELECT id, name, email, created_at FROM users WHERE id = $1`
    
    err := db.QueryRow(query, id).Scan(
        &user.ID,
        &user.Name,
        &user.Email,
        &user.CreatedAt,
    )
    
    if err == sql.ErrNoRows {
        return nil, fmt.Errorf("user not found")
    }
    
    return user, err
}

// READ ALL
func getAllUsers(db *sql.DB) ([]User, error) {
    query := `SELECT id, name, email, created_at FROM users ORDER BY id`
    
    rows, err := db.Query(query)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    
    var users []User
    for rows.Next() {
        var user User
        err := rows.Scan(
            &user.ID,
            &user.Name,
            &user.Email,
            &user.CreatedAt,
        )
        if err != nil {
            return nil, err
        }
        users = append(users, user)
    }
    
    return users, rows.Err()
}

// UPDATE
func updateUser(db *sql.DB, id int, name, email string) error {
    query := `UPDATE users SET name = $1, email = $2 WHERE id = $3`
    result, err := db.Exec(query, name, email, id)
    if err != nil {
        return err
    }
    
    rowsAffected, _ := result.RowsAffected()
    if rowsAffected == 0 {
        return fmt.Errorf("user not found")
    }
    
    return nil
}

// DELETE
func deleteUser(db *sql.DB, id int) error {
    query := `DELETE FROM users WHERE id = $1`
    result, err := db.Exec(query, id)
    if err != nil {
        return err
    }
    
    rowsAffected, _ := result.RowsAffected()
    if rowsAffected == 0 {
        return fmt.Errorf("user not found")
    }
    
    return nil
}
```

---

## 2️⃣ MID LEVEL - GORM Basics

### Installation

```bash
go get -u gorm.io/gorm
go get -u gorm.io/driver/postgres
go get -u gorm.io/driver/mysql
go get -u gorm.io/driver/sqlite
```

### Connection Setup

```go
package main

import (
    "log"
    
    "gorm.io/driver/postgres"
    "gorm.io/gorm"
    "gorm.io/gorm/logger"
)

func main() {
    dsn := "host=localhost user=postgres password=secret dbname=mydb port=5432 sslmode=disable"
    
    db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{
        Logger: logger.Default.LogMode(logger.Info), // Show SQL queries
    })
    if err != nil {
        log.Fatal(err)
    }
    
    // Get underlying sql.DB for connection pool settings
    sqlDB, _ := db.DB()
    sqlDB.SetMaxIdleConns(10)
    sqlDB.SetMaxOpenConns(100)
    
    log.Println("Connected to database!")
}
```

### Model Definition

```go
package models

import (
    "time"
    
    "gorm.io/gorm"
)

type User struct {
    ID        uint           `gorm:"primaryKey" json:"id"`
    Name      string         `gorm:"size:100;not null" json:"name"`
    Email     string         `gorm:"uniqueIndex;not null" json:"email"`
    Password  string         `gorm:"not null" json:"-"` // Hide from JSON
    Age       int            `gorm:"default:0" json:"age"`
    IsActive  bool           `gorm:"default:true" json:"is_active"`
    CreatedAt time.Time      `json:"created_at"`
    UpdatedAt time.Time      `json:"updated_at"`
    DeletedAt gorm.DeletedAt `gorm:"index" json:"-"` // Soft delete
}

// Custom table name
func (User) TableName() string {
    return "users"
}
```

### Auto Migration

```go
package main

import (
    "log"
    
    "gorm.io/driver/postgres"
    "gorm.io/gorm"
)

type User struct {
    gorm.Model // Includes ID, CreatedAt, UpdatedAt, DeletedAt
    Name  string `gorm:"size:100"`
    Email string `gorm:"uniqueIndex"`
}

type Task struct {
    gorm.Model
    Title   string
    UserID  uint
    User    User `gorm:"foreignKey:UserID"`
}

func main() {
    db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
    if err != nil {
        log.Fatal(err)
    }
    
    // Auto migrate models
    db.AutoMigrate(&User{}, &Task{})
    
    log.Println("Migration completed!")
}
```

### GORM CRUD Operations

```go
package main

import (
    "fmt"
    "log"
    
    "gorm.io/gorm"
)

type User struct {
    gorm.Model
    Name  string
    Email string
}

// ===== CREATE =====
func createUser(db *gorm.DB) {
    // Single record
    user := User{Name: "John", Email: "john@example.com"}
    result := db.Create(&user)
    
    fmt.Printf("ID: %d\n", user.ID)               // Auto-filled
    fmt.Printf("Rows: %d\n", result.RowsAffected) // 1
    
    // Multiple records
    users := []User{
        {Name: "Jane", Email: "jane@example.com"},
        {Name: "Bob", Email: "bob@example.com"},
    }
    db.Create(&users)
}

// ===== READ =====
func readUsers(db *gorm.DB) {
    // Find by ID
    var user User
    db.First(&user, 1) // Find by primary key
    db.First(&user, "id = ?", 1) // Same as above
    
    // Find by condition
    db.Where("name = ?", "John").First(&user)
    db.Where("email LIKE ?", "%@example.com").First(&user)
    
    // Find all
    var users []User
    db.Find(&users)
    
    // Find with conditions
    db.Where("age > ?", 18).Find(&users)
    db.Where("name IN ?", []string{"John", "Jane"}).Find(&users)
    
    // Find with struct (non-zero fields only)
    db.Where(&User{Name: "John"}).Find(&users)
    
    // Select specific fields
    db.Select("name", "email").Find(&users)
    
    // Order, Limit, Offset
    db.Order("created_at desc").Limit(10).Offset(0).Find(&users)
    
    // Count
    var count int64
    db.Model(&User{}).Count(&count)
    
    // First or Not Found
    result := db.First(&user, 999)
    if result.Error == gorm.ErrRecordNotFound {
        fmt.Println("User not found")
    }
}

// ===== UPDATE =====
func updateUsers(db *gorm.DB) {
    var user User
    db.First(&user, 1)
    
    // Update single field
    db.Model(&user).Update("name", "John Doe")
    
    // Update multiple fields
    db.Model(&user).Updates(User{Name: "John Doe", Email: "johndoe@example.com"})
    
    // Update with map (zero values included)
    db.Model(&user).Updates(map[string]interface{}{
        "name":      "John Doe",
        "is_active": false, // Zero value will be updated
    })
    
    // Update with conditions
    db.Model(&User{}).Where("is_active = ?", false).Update("is_active", true)
    
    // Update all without conditions
    db.Model(&User{}).Where("1 = 1").Update("is_active", true)
}

// ===== DELETE =====
func deleteUsers(db *gorm.DB) {
    var user User
    db.First(&user, 1)
    
    // Soft delete (if DeletedAt exists)
    db.Delete(&user)
    
    // Delete by ID
    db.Delete(&User{}, 1)
    db.Delete(&User{}, []int{1, 2, 3})
    
    // Delete with conditions
    db.Where("email LIKE ?", "%@test.com").Delete(&User{})
    
    // Permanent delete
    db.Unscoped().Delete(&user)
    
    // Find soft deleted records
    var deletedUsers []User
    db.Unscoped().Where("deleted_at IS NOT NULL").Find(&deletedUsers)
}
```

---

## 3️⃣ MID LEVEL - Relationships

### One-to-Many

```go
package main

import "gorm.io/gorm"

// User has many Tasks
type User struct {
    gorm.Model
    Name  string
    Email string
    Tasks []Task // Has Many
}

type Task struct {
    gorm.Model
    Title  string
    UserID uint // Foreign key
    User   User // Belongs To
}

func main() {
    db, _ := gorm.Open(...)
    
    // Create with association
    user := User{
        Name:  "John",
        Email: "john@example.com",
        Tasks: []Task{
            {Title: "Task 1"},
            {Title: "Task 2"},
        },
    }
    db.Create(&user)
    
    // Preload (eager loading)
    var userWithTasks User
    db.Preload("Tasks").First(&userWithTasks, 1)
    
    // Lazy loading
    var tasks []Task
    db.Model(&user).Association("Tasks").Find(&tasks)
    
    // Add task to user
    db.Model(&user).Association("Tasks").Append(&Task{Title: "Task 3"})
    
    // Replace all tasks
    db.Model(&user).Association("Tasks").Replace(&Task{Title: "Only Task"})
    
    // Count associations
    count := db.Model(&user).Association("Tasks").Count()
    
    // Delete association
    db.Model(&user).Association("Tasks").Delete(&Task{})
}
```

### Many-to-Many

```go
package main

import "gorm.io/gorm"

// User has many Roles, Role has many Users
type User struct {
    gorm.Model
    Name  string
    Roles []Role `gorm:"many2many:user_roles;"`
}

type Role struct {
    gorm.Model
    Name  string
    Users []User `gorm:"many2many:user_roles;"`
}

func main() {
    db, _ := gorm.Open(...)
    
    // Auto migrate (creates junction table)
    db.AutoMigrate(&User{}, &Role{})
    
    // Create with associations
    user := User{
        Name: "John",
        Roles: []Role{
            {Name: "Admin"},
            {Name: "Editor"},
        },
    }
    db.Create(&user)
    
    // Preload
    var userWithRoles User
    db.Preload("Roles").First(&userWithRoles, 1)
    
    // Add role to user
    role := Role{Name: "Viewer"}
    db.Create(&role)
    db.Model(&user).Association("Roles").Append(&role)
    
    // Remove role from user
    db.Model(&user).Association("Roles").Delete(&role)
}
```

### One-to-One

```go
package main

import "gorm.io/gorm"

type User struct {
    gorm.Model
    Name    string
    Profile Profile // Has One
}

type Profile struct {
    gorm.Model
    UserID  uint   // Foreign key
    Bio     string
    Avatar  string
}

func main() {
    db, _ := gorm.Open(...)
    
    // Create with profile
    user := User{
        Name: "John",
        Profile: Profile{
            Bio:    "Developer",
            Avatar: "avatar.png",
        },
    }
    db.Create(&user)
    
    // Preload
    var userWithProfile User
    db.Preload("Profile").First(&userWithProfile, 1)
}
```

---

## 4️⃣ MID-SENIOR LEVEL - Advanced Queries

### Raw SQL

```go
package main

import "gorm.io/gorm"

func rawQueries(db *gorm.DB) {
    // Raw query
    var users []User
    db.Raw("SELECT * FROM users WHERE age > ?", 18).Scan(&users)
    
    // Exec for INSERT/UPDATE/DELETE
    db.Exec("UPDATE users SET is_active = ? WHERE created_at < ?", false, time.Now().AddDate(-1, 0, 0))
    
    // Named arguments
    db.Raw("SELECT * FROM users WHERE name = @name", sql.Named("name", "John")).Scan(&users)
}
```

### Scopes (Reusable Queries)

```go
package main

import "gorm.io/gorm"

// Scope functions
func Active(db *gorm.DB) *gorm.DB {
    return db.Where("is_active = ?", true)
}

func CreatedAfter(date time.Time) func(db *gorm.DB) *gorm.DB {
    return func(db *gorm.DB) *gorm.DB {
        return db.Where("created_at > ?", date)
    }
}

func OrderByNewest(db *gorm.DB) *gorm.DB {
    return db.Order("created_at DESC")
}

func Paginate(page, limit int) func(db *gorm.DB) *gorm.DB {
    return func(db *gorm.DB) *gorm.DB {
        offset := (page - 1) * limit
        return db.Offset(offset).Limit(limit)
    }
}

func main() {
    db, _ := gorm.Open(...)
    
    var users []User
    
    // Use scopes
    db.Scopes(Active, OrderByNewest).Find(&users)
    
    db.Scopes(
        Active,
        CreatedAfter(time.Now().AddDate(0, -1, 0)),
        Paginate(1, 10),
    ).Find(&users)
}
```

### Transactions

```go
package main

import (
    "errors"
    
    "gorm.io/gorm"
)

func transferMoney(db *gorm.DB, fromID, toID uint, amount float64) error {
    // Transaction with automatic rollback on error
    return db.Transaction(func(tx *gorm.DB) error {
        var fromAccount, toAccount Account
        
        // Lock rows for update
        if err := tx.Set("gorm:query_option", "FOR UPDATE").
            First(&fromAccount, fromID).Error; err != nil {
            return err
        }
        
        if err := tx.Set("gorm:query_option", "FOR UPDATE").
            First(&toAccount, toID).Error; err != nil {
            return err
        }
        
        // Check balance
        if fromAccount.Balance < amount {
            return errors.New("insufficient balance")
        }
        
        // Update balances
        if err := tx.Model(&fromAccount).
            Update("balance", fromAccount.Balance-amount).Error; err != nil {
            return err
        }
        
        if err := tx.Model(&toAccount).
            Update("balance", toAccount.Balance+amount).Error; err != nil {
            return err
        }
        
        // Return nil to commit
        return nil
    })
}

// Manual transaction control
func manualTransaction(db *gorm.DB) error {
    tx := db.Begin()
    defer func() {
        if r := recover(); r != nil {
            tx.Rollback()
        }
    }()
    
    if err := tx.Create(&User{Name: "John"}).Error; err != nil {
        tx.Rollback()
        return err
    }
    
    if err := tx.Create(&Task{Title: "Task 1"}).Error; err != nil {
        tx.Rollback()
        return err
    }
    
    return tx.Commit().Error
}
```

### Hooks (Callbacks)

```go
package main

import (
    "errors"
    
    "golang.org/x/crypto/bcrypt"
    "gorm.io/gorm"
)

type User struct {
    gorm.Model
    Name     string
    Email    string
    Password string
}

// BeforeCreate hook
func (u *User) BeforeCreate(tx *gorm.DB) error {
    // Hash password
    hashedPassword, err := bcrypt.GenerateFromPassword(
        []byte(u.Password),
        bcrypt.DefaultCost,
    )
    if err != nil {
        return err
    }
    u.Password = string(hashedPassword)
    return nil
}

// BeforeUpdate hook
func (u *User) BeforeUpdate(tx *gorm.DB) error {
    // Validate email
    if u.Email == "" {
        return errors.New("email cannot be empty")
    }
    return nil
}

// AfterCreate hook
func (u *User) AfterCreate(tx *gorm.DB) error {
    // Send welcome email, create default settings, etc.
    log.Printf("User %s created with ID %d", u.Name, u.ID)
    return nil
}

// AfterFind hook
func (u *User) AfterFind(tx *gorm.DB) error {
    // Mask password after reading from DB
    u.Password = "***"
    return nil
}
```

---

## 5️⃣ SENIOR LEVEL - Repository Pattern

### Repository Interface

```go
// repository/user_repository.go
package repository

import (
    "context"
    
    "github.com/username/myapp/internal/models"
)

type UserRepository interface {
    FindAll(ctx context.Context) ([]models.User, error)
    FindByID(ctx context.Context, id uint) (*models.User, error)
    FindByEmail(ctx context.Context, email string) (*models.User, error)
    Create(ctx context.Context, user *models.User) error
    Update(ctx context.Context, user *models.User) error
    Delete(ctx context.Context, id uint) error
    FindWithPagination(ctx context.Context, page, limit int) ([]models.User, int64, error)
}
```

### GORM Implementation

```go
// repository/gorm/user_repository.go
package gorm

import (
    "context"
    
    "github.com/username/myapp/internal/models"
    "github.com/username/myapp/internal/repository"
    "gorm.io/gorm"
)

type userRepository struct {
    db *gorm.DB
}

func NewUserRepository(db *gorm.DB) repository.UserRepository {
    return &userRepository{db: db}
}

func (r *userRepository) FindAll(ctx context.Context) ([]models.User, error) {
    var users []models.User
    if err := r.db.WithContext(ctx).Find(&users).Error; err != nil {
        return nil, err
    }
    return users, nil
}

func (r *userRepository) FindByID(ctx context.Context, id uint) (*models.User, error) {
    var user models.User
    if err := r.db.WithContext(ctx).First(&user, id).Error; err != nil {
        if err == gorm.ErrRecordNotFound {
            return nil, nil
        }
        return nil, err
    }
    return &user, nil
}

func (r *userRepository) FindByEmail(ctx context.Context, email string) (*models.User, error) {
    var user models.User
    if err := r.db.WithContext(ctx).Where("email = ?", email).First(&user).Error; err != nil {
        if err == gorm.ErrRecordNotFound {
            return nil, nil
        }
        return nil, err
    }
    return &user, nil
}

func (r *userRepository) Create(ctx context.Context, user *models.User) error {
    return r.db.WithContext(ctx).Create(user).Error
}

func (r *userRepository) Update(ctx context.Context, user *models.User) error {
    return r.db.WithContext(ctx).Save(user).Error
}

func (r *userRepository) Delete(ctx context.Context, id uint) error {
    return r.db.WithContext(ctx).Delete(&models.User{}, id).Error
}

func (r *userRepository) FindWithPagination(ctx context.Context, page, limit int) ([]models.User, int64, error) {
    var users []models.User
    var total int64
    
    offset := (page - 1) * limit
    
    if err := r.db.WithContext(ctx).Model(&models.User{}).Count(&total).Error; err != nil {
        return nil, 0, err
    }
    
    if err := r.db.WithContext(ctx).Offset(offset).Limit(limit).Find(&users).Error; err != nil {
        return nil, 0, err
    }
    
    return users, total, nil
}
```

### Generic Repository

```go
// repository/generic_repository.go
package repository

import (
    "context"
    
    "gorm.io/gorm"
)

type GenericRepository[T any] interface {
    FindAll(ctx context.Context) ([]T, error)
    FindByID(ctx context.Context, id uint) (*T, error)
    Create(ctx context.Context, entity *T) error
    Update(ctx context.Context, entity *T) error
    Delete(ctx context.Context, id uint) error
}

type genericRepository[T any] struct {
    db *gorm.DB
}

func NewGenericRepository[T any](db *gorm.DB) GenericRepository[T] {
    return &genericRepository[T]{db: db}
}

func (r *genericRepository[T]) FindAll(ctx context.Context) ([]T, error) {
    var entities []T
    if err := r.db.WithContext(ctx).Find(&entities).Error; err != nil {
        return nil, err
    }
    return entities, nil
}

func (r *genericRepository[T]) FindByID(ctx context.Context, id uint) (*T, error) {
    var entity T
    if err := r.db.WithContext(ctx).First(&entity, id).Error; err != nil {
        if err == gorm.ErrRecordNotFound {
            return nil, nil
        }
        return nil, err
    }
    return &entity, nil
}

func (r *genericRepository[T]) Create(ctx context.Context, entity *T) error {
    return r.db.WithContext(ctx).Create(entity).Error
}

func (r *genericRepository[T]) Update(ctx context.Context, entity *T) error {
    return r.db.WithContext(ctx).Save(entity).Error
}

func (r *genericRepository[T]) Delete(ctx context.Context, id uint) error {
    var entity T
    return r.db.WithContext(ctx).Delete(&entity, id).Error
}

// Usage
func main() {
    userRepo := NewGenericRepository[User](db)
    taskRepo := NewGenericRepository[Task](db)
    
    users, _ := userRepo.FindAll(context.Background())
    tasks, _ := taskRepo.FindAll(context.Background())
}
```

---

## 6️⃣ SENIOR LEVEL - Connection Pool & Performance

### Connection Pool Configuration

```go
package config

import (
    "time"
    
    "gorm.io/driver/postgres"
    "gorm.io/gorm"
    "gorm.io/gorm/logger"
)

func NewDatabase(cfg *Config) *gorm.DB {
    db, err := gorm.Open(postgres.Open(cfg.DatabaseURL), &gorm.Config{
        Logger: logger.Default.LogMode(logger.Info),
        
        // Performance settings
        PrepareStmt:                              true,  // Cache prepared statements
        SkipDefaultTransaction:                   true,  // Skip default transaction for single operations
        DisableForeignKeyConstraintWhenMigrating: true,  // Faster migrations
    })
    
    if err != nil {
        log.Fatal(err)
    }
    
    sqlDB, _ := db.DB()
    
    // Connection pool settings
    sqlDB.SetMaxIdleConns(10)                  // Max idle connections
    sqlDB.SetMaxOpenConns(100)                 // Max open connections
    sqlDB.SetConnMaxLifetime(time.Hour)        // Max connection lifetime
    sqlDB.SetConnMaxIdleTime(10 * time.Minute) // Max idle time
    
    return db
}
```

### Query Optimization

```go
package main

import "gorm.io/gorm"

func optimizedQueries(db *gorm.DB) {
    // ===== SELECT SPECIFIC COLUMNS =====
    var users []User
    db.Select("id", "name").Find(&users) // Don't select all columns
    
    // ===== PRELOAD vs JOINS =====
    
    // Preload: 2 queries (users + tasks)
    db.Preload("Tasks").Find(&users)
    
    // Joins: 1 query (better for filtering)
    db.Joins("Tasks").Where("tasks.status = ?", "pending").Find(&users)
    
    // ===== BATCH INSERT =====
    users := make([]User, 1000)
    db.CreateInBatches(users, 100) // Insert 100 at a time
    
    // ===== FIND IN BATCHES =====
    db.FindInBatches(&users, 100, func(tx *gorm.DB, batch int) error {
        for _, user := range users {
            // Process each user
        }
        return nil
    })
    
    // ===== ITERATOR (for large datasets) =====
    rows, _ := db.Model(&User{}).Rows()
    defer rows.Close()
    for rows.Next() {
        var user User
        db.ScanRows(rows, &user)
        // Process user
    }
    
    // ===== INDEX HINTS =====
    db.Clauses(hints.UseIndex("idx_users_email")).Find(&users)
    
    // ===== PLUCK (single column) =====
    var emails []string
    db.Model(&User{}).Pluck("email", &emails)
}
```

---

## 7️⃣ EXPERT LEVEL - Database Migrations

### golang-migrate

```bash
# Install
go install -tags 'postgres' github.com/golang-migrate/migrate/v4/cmd/migrate@latest

# Create migration
migrate create -ext sql -dir migrations -seq create_users_table

# Run migrations
migrate -path migrations -database "postgres://localhost:5432/mydb?sslmode=disable" up

# Rollback
migrate -path migrations -database "postgres://localhost:5432/mydb?sslmode=disable" down 1
```

```sql
-- migrations/000001_create_users_table.up.sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_deleted_at ON users(deleted_at);

-- migrations/000001_create_users_table.down.sql
DROP TABLE IF EXISTS users;
```

### Migration in Code

```go
package main

import (
    "github.com/golang-migrate/migrate/v4"
    "github.com/golang-migrate/migrate/v4/database/postgres"
    _ "github.com/golang-migrate/migrate/v4/source/file"
)

func runMigrations(db *sql.DB) error {
    driver, err := postgres.WithInstance(db, &postgres.Config{})
    if err != nil {
        return err
    }
    
    m, err := migrate.NewWithDatabaseInstance(
        "file://migrations",
        "postgres",
        driver,
    )
    if err != nil {
        return err
    }
    
    if err := m.Up(); err != nil && err != migrate.ErrNoChange {
        return err
    }
    
    return nil
}
```

---

## 📊 Database Methods Comparison

| Operation | database/sql | GORM |
|-----------|-------------|------|
| Query One | `db.QueryRow()` | `db.First()` |
| Query All | `db.Query()` | `db.Find()` |
| Insert | `db.Exec()` | `db.Create()` |
| Update | `db.Exec()` | `db.Save()` / `db.Update()` |
| Delete | `db.Exec()` | `db.Delete()` |
| Transaction | `db.Begin()` | `db.Transaction()` |

### GORM vs database/sql

| Aspect | database/sql | GORM |
|--------|-------------|------|
| Control | Full | Abstracted |
| Learning | Harder | Easier |
| Performance | Best | Good |
| Migrations | Manual | Auto |
| Associations | Manual | Automatic |
| Use Case | Performance-critical | Rapid development |

---

## 💡 Summary

| Level | Focus |
|-------|-------|
| **Junior** | database/sql basics, CRUD |
| **Mid** | GORM, relationships, migrations |
| **Mid-Senior** | Raw SQL, scopes, transactions |
| **Senior** | Repository pattern, hooks |
| **Expert** | Connection pool, optimization |

**Best Practices:**
- ✅ Use connection pooling
- ✅ Use prepared statements
- ✅ Use transactions for multiple operations
- ✅ Use indexes on frequently queried columns
- ✅ Select only needed columns
- ✅ Use pagination for large datasets
- ❌ Don't use SELECT * in production
- ❌ Don't forget to close rows/connections
- ❌ Don't ignore errors
