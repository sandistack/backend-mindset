# 🔄 Database Migrations di Go

## Kenapa Penting?

Migrations membantu:
- ✅ Version control untuk database schema
- ✅ Reproducible database changes
- ✅ Team collaboration
- ✅ Safe production deployments

---

## 📚 Daftar Isi

1. [Migration Tools](#1️⃣-migration-tools)
2. [golang-migrate](#2️⃣-golang-migrate)
3. [Goose](#3️⃣-goose)
4. [GORM AutoMigrate](#4️⃣-gorm-automigrate)
5. [Atlas](#5️⃣-atlas)
6. [Best Practices](#6️⃣-best-practices)
7. [CI/CD Integration](#7️⃣-cicd-integration)

---

## 1️⃣ Migration Tools

| Tool | Type | Pros | Cons |
|------|------|------|------|
| **golang-migrate** | SQL files | Popular, flexible | Manual SQL |
| **Goose** | SQL/Go | Embedded Go code | Less popular |
| **GORM AutoMigrate** | Struct-based | Easy, automatic | Less control |
| **Atlas** | Declarative | Modern, safe | Learning curve |

---

## 2️⃣ golang-migrate

### Installation

```bash
# CLI
go install -tags 'postgres' github.com/golang-migrate/migrate/v4/cmd/migrate@latest

# As library
go get github.com/golang-migrate/migrate/v4
```

### Project Structure

```
migrations/
├── 000001_create_users_table.up.sql
├── 000001_create_users_table.down.sql
├── 000002_create_tasks_table.up.sql
├── 000002_create_tasks_table.down.sql
├── 000003_add_priority_to_tasks.up.sql
└── 000003_add_priority_to_tasks.down.sql
```

### Creating Migrations

```bash
# Create new migration
migrate create -ext sql -dir migrations -seq create_users_table
```

```sql
-- migrations/000001_create_users_table.up.sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    username VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);

-- migrations/000001_create_users_table.down.sql
DROP TABLE IF EXISTS users;
```

```sql
-- migrations/000002_create_tasks_table.up.sql
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'TODO',
    priority VARCHAR(10) DEFAULT 'MEDIUM',
    due_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_status ON tasks(status);

-- migrations/000002_create_tasks_table.down.sql
DROP TABLE IF EXISTS tasks;
```

### CLI Commands

```bash
# Run migrations
migrate -database "postgres://user:pass@localhost:5432/dbname?sslmode=disable" -path migrations up

# Rollback last migration
migrate -database "..." -path migrations down 1

# Rollback all
migrate -database "..." -path migrations down

# Go to specific version
migrate -database "..." -path migrations goto 3

# Check current version
migrate -database "..." -path migrations version

# Force version (fix dirty state)
migrate -database "..." -path migrations force 2
```

### Programmatic Usage

```go
// internal/database/migrate.go
package database

import (
    "database/sql"
    "fmt"
    
    "github.com/golang-migrate/migrate/v4"
    "github.com/golang-migrate/migrate/v4/database/postgres"
    _ "github.com/golang-migrate/migrate/v4/source/file"
)

func RunMigrations(db *sql.DB, migrationsPath string) error {
    driver, err := postgres.WithInstance(db, &postgres.Config{})
    if err != nil {
        return fmt.Errorf("failed to create driver: %w", err)
    }
    
    m, err := migrate.NewWithDatabaseInstance(
        fmt.Sprintf("file://%s", migrationsPath),
        "postgres",
        driver,
    )
    if err != nil {
        return fmt.Errorf("failed to create migrate instance: %w", err)
    }
    
    if err := m.Up(); err != nil && err != migrate.ErrNoChange {
        return fmt.Errorf("failed to run migrations: %w", err)
    }
    
    version, dirty, err := m.Version()
    if err != nil && err != migrate.ErrNilVersion {
        return fmt.Errorf("failed to get version: %w", err)
    }
    
    fmt.Printf("Migration version: %d, dirty: %v\n", version, dirty)
    return nil
}

// Usage in main.go
func main() {
    db, _ := sql.Open("postgres", os.Getenv("DATABASE_URL"))
    
    if err := database.RunMigrations(db, "migrations"); err != nil {
        log.Fatal(err)
    }
    
    // Start server...
}
```

### Embedded Migrations

```go
// internal/database/migrations.go
package database

import (
    "embed"
    
    "github.com/golang-migrate/migrate/v4"
    "github.com/golang-migrate/migrate/v4/source/iofs"
)

//go:embed migrations/*.sql
var migrationsFS embed.FS

func RunEmbeddedMigrations(db *sql.DB) error {
    source, err := iofs.New(migrationsFS, "migrations")
    if err != nil {
        return err
    }
    
    driver, err := postgres.WithInstance(db, &postgres.Config{})
    if err != nil {
        return err
    }
    
    m, err := migrate.NewWithInstance("iofs", source, "postgres", driver)
    if err != nil {
        return err
    }
    
    return m.Up()
}
```

---

## 3️⃣ Goose

### Installation

```bash
go install github.com/pressly/goose/v3/cmd/goose@latest
```

### Creating Migrations

```bash
# SQL migration
goose -dir migrations create add_users_table sql

# Go migration
goose -dir migrations create add_users_table go
```

### SQL Migration

```sql
-- migrations/00001_add_users_table.sql
-- +goose Up
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- +goose Down
DROP TABLE users;
```

### Go Migration

```go
// migrations/00002_seed_data.go
package migrations

import (
    "context"
    "database/sql"
    
    "github.com/pressly/goose/v3"
)

func init() {
    goose.AddMigrationContext(upSeedData, downSeedData)
}

func upSeedData(ctx context.Context, tx *sql.Tx) error {
    _, err := tx.ExecContext(ctx, `
        INSERT INTO users (email) VALUES 
        ('admin@example.com'),
        ('user@example.com');
    `)
    return err
}

func downSeedData(ctx context.Context, tx *sql.Tx) error {
    _, err := tx.ExecContext(ctx, `
        DELETE FROM users WHERE email IN ('admin@example.com', 'user@example.com');
    `)
    return err
}
```

### CLI Commands

```bash
# Run migrations
goose -dir migrations postgres "postgres://user:pass@localhost:5432/db" up

# Rollback
goose -dir migrations postgres "..." down

# Status
goose -dir migrations postgres "..." status

# Create
goose -dir migrations create add_column sql
```

### Programmatic Usage

```go
// internal/database/goose.go
package database

import (
    "database/sql"
    
    "github.com/pressly/goose/v3"
)

func RunGooseMigrations(db *sql.DB, migrationsDir string) error {
    goose.SetDialect("postgres")
    
    if err := goose.Up(db, migrationsDir); err != nil {
        return err
    }
    
    return nil
}
```

---

## 4️⃣ GORM AutoMigrate

### Basic Usage

```go
// internal/models/models.go
package models

import (
    "time"
    
    "gorm.io/gorm"
)

type User struct {
    ID        uint           `gorm:"primaryKey"`
    Email     string         `gorm:"uniqueIndex;size:255;not null"`
    Password  string         `gorm:"size:255;not null"`
    Username  string         `gorm:"size:100;not null"`
    IsActive  bool           `gorm:"default:true"`
    CreatedAt time.Time
    UpdatedAt time.Time
    DeletedAt gorm.DeletedAt `gorm:"index"`
}

type Task struct {
    ID          uint           `gorm:"primaryKey"`
    UserID      uint           `gorm:"not null;index"`
    User        User           `gorm:"foreignKey:UserID"`
    Title       string         `gorm:"size:255;not null"`
    Description string         `gorm:"type:text"`
    Status      string         `gorm:"size:20;default:'TODO';index"`
    Priority    string         `gorm:"size:10;default:'MEDIUM'"`
    DueDate     *time.Time
    CreatedAt   time.Time
    UpdatedAt   time.Time
    DeletedAt   gorm.DeletedAt `gorm:"index"`
}
```

### AutoMigrate

```go
// internal/database/gorm.go
package database

import (
    "myapp/internal/models"
    
    "gorm.io/driver/postgres"
    "gorm.io/gorm"
)

func SetupDatabase(dsn string) (*gorm.DB, error) {
    db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
    if err != nil {
        return nil, err
    }
    
    // Auto migrate
    if err := db.AutoMigrate(
        &models.User{},
        &models.Task{},
    ); err != nil {
        return nil, err
    }
    
    return db, nil
}
```

### Manual Migration with GORM

```go
// For more control, use Migrator
func ManualMigration(db *gorm.DB) error {
    migrator := db.Migrator()
    
    // Create table
    if !migrator.HasTable(&models.Task{}) {
        if err := migrator.CreateTable(&models.Task{}); err != nil {
            return err
        }
    }
    
    // Add column
    if !migrator.HasColumn(&models.Task{}, "priority") {
        if err := migrator.AddColumn(&models.Task{}, "priority"); err != nil {
            return err
        }
    }
    
    // Add index
    if !migrator.HasIndex(&models.Task{}, "idx_tasks_status") {
        if err := migrator.CreateIndex(&models.Task{}, "idx_tasks_status"); err != nil {
            return err
        }
    }
    
    return nil
}
```

---

## 5️⃣ Atlas

### Installation

```bash
# macOS
brew install ariga/tap/atlas

# Linux
curl -sSf https://atlasgo.sh | sh
```

### Declarative Schema

```hcl
// schema.hcl
schema "public" {}

table "users" {
  schema = schema.public
  column "id" {
    type = serial
  }
  column "email" {
    type = varchar(255)
  }
  column "password_hash" {
    type = varchar(255)
  }
  column "created_at" {
    type    = timestamptz
    default = sql("NOW()")
  }
  primary_key {
    columns = [column.id]
  }
  index "idx_users_email" {
    unique  = true
    columns = [column.email]
  }
}

table "tasks" {
  schema = schema.public
  column "id" {
    type = serial
  }
  column "user_id" {
    type = int
  }
  column "title" {
    type = varchar(255)
  }
  column "status" {
    type    = varchar(20)
    default = "TODO"
  }
  column "created_at" {
    type    = timestamptz
    default = sql("NOW()")
  }
  primary_key {
    columns = [column.id]
  }
  foreign_key "fk_tasks_user" {
    columns     = [column.user_id]
    ref_columns = [table.users.column.id]
    on_delete   = CASCADE
  }
  index "idx_tasks_user" {
    columns = [column.user_id]
  }
}
```

### CLI Commands

```bash
# Inspect current database
atlas schema inspect -u "postgres://user:pass@localhost:5432/db"

# Generate migration from diff
atlas migrate diff create_tables \
  --dir "file://migrations" \
  --to "file://schema.hcl" \
  --dev-url "docker://postgres/15"

# Apply migrations
atlas migrate apply \
  --dir "file://migrations" \
  --url "postgres://user:pass@localhost:5432/db"

# Lint migrations
atlas migrate lint \
  --dir "file://migrations" \
  --dev-url "docker://postgres/15"
```

---

## 6️⃣ Best Practices

### Safe Migration Patterns

```sql
-- ✅ Add column with default (safe)
ALTER TABLE tasks ADD COLUMN priority VARCHAR(10) DEFAULT 'MEDIUM';

-- ✅ Create index concurrently (PostgreSQL)
CREATE INDEX CONCURRENTLY idx_tasks_priority ON tasks(priority);

-- ❌ Don't rename column directly in production
-- Instead: Add new column -> Copy data -> Drop old column

-- ✅ Safe column rename
-- Step 1: Add new column
ALTER TABLE tasks ADD COLUMN task_title VARCHAR(255);

-- Step 2: Copy data (in separate migration)
UPDATE tasks SET task_title = title WHERE task_title IS NULL;

-- Step 3: Add NOT NULL constraint
ALTER TABLE tasks ALTER COLUMN task_title SET NOT NULL;

-- Step 4: Drop old column (later migration)
ALTER TABLE tasks DROP COLUMN title;
```

### Transaction per Migration

```sql
-- migrations/000003_add_priority.up.sql
BEGIN;

ALTER TABLE tasks ADD COLUMN priority VARCHAR(10) DEFAULT 'MEDIUM';
CREATE INDEX idx_tasks_priority ON tasks(priority);

COMMIT;

-- migrations/000003_add_priority.down.sql
BEGIN;

DROP INDEX IF EXISTS idx_tasks_priority;
ALTER TABLE tasks DROP COLUMN IF EXISTS priority;

COMMIT;
```

### Data Migration

```sql
-- migrations/000004_backfill_priority.up.sql
-- Backfill in batches to avoid locking
DO $$
DECLARE
    batch_size INT := 1000;
    affected INT;
BEGIN
    LOOP
        UPDATE tasks
        SET priority = CASE
            WHEN due_date < NOW() THEN 'HIGH'
            ELSE 'MEDIUM'
        END
        WHERE id IN (
            SELECT id FROM tasks
            WHERE priority IS NULL
            LIMIT batch_size
            FOR UPDATE SKIP LOCKED
        );
        
        GET DIAGNOSTICS affected = ROW_COUNT;
        
        EXIT WHEN affected = 0;
        
        COMMIT;
    END LOOP;
END $$;
```

---

## 7️⃣ CI/CD Integration

### Makefile

```makefile
# Makefile
MIGRATIONS_DIR=migrations
DB_URL=postgres://user:pass@localhost:5432/myapp?sslmode=disable

.PHONY: migrate-up migrate-down migrate-create migrate-status

migrate-up:
	migrate -database "$(DB_URL)" -path $(MIGRATIONS_DIR) up

migrate-down:
	migrate -database "$(DB_URL)" -path $(MIGRATIONS_DIR) down 1

migrate-create:
	@read -p "Migration name: " name; \
	migrate create -ext sql -dir $(MIGRATIONS_DIR) -seq $$name

migrate-status:
	migrate -database "$(DB_URL)" -path $(MIGRATIONS_DIR) version

migrate-force:
	@read -p "Force version: " version; \
	migrate -database "$(DB_URL)" -path $(MIGRATIONS_DIR) force $$version
```

### GitHub Actions

```yaml
# .github/workflows/migrate.yml
name: Database Migration

on:
  push:
    branches: [main]
    paths:
      - 'migrations/**'

jobs:
  migrate:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Install migrate
        run: |
          curl -L https://github.com/golang-migrate/migrate/releases/download/v4.16.2/migrate.linux-amd64.tar.gz | tar xvz
          sudo mv migrate /usr/local/bin/
      
      - name: Run migrations
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: |
          migrate -database "$DATABASE_URL" -path migrations up
```

### Docker Entrypoint

```dockerfile
# Dockerfile
FROM golang:1.21-alpine AS builder

# Install migrate
RUN go install -tags 'postgres' github.com/golang-migrate/migrate/v4/cmd/migrate@latest

# Build app
WORKDIR /app
COPY . .
RUN go build -o main ./cmd/api

# Final image
FROM alpine:3.18

COPY --from=builder /go/bin/migrate /usr/local/bin/
COPY --from=builder /app/main /app/
COPY --from=builder /app/migrations /app/migrations/
COPY docker-entrypoint.sh /

ENTRYPOINT ["/docker-entrypoint.sh"]
```

```bash
#!/bin/sh
# docker-entrypoint.sh

# Run migrations
echo "Running migrations..."
migrate -database "$DATABASE_URL" -path /app/migrations up

# Start app
exec /app/main
```

---

## 📋 Migration Checklist

### Junior ✅
- [ ] Understand up/down migrations
- [ ] Create basic table migrations
- [ ] Run migrations via CLI

### Mid ✅
- [ ] Programmatic migrations
- [ ] Index management
- [ ] Foreign key constraints
- [ ] Rollback strategy

### Senior ✅
- [ ] Safe production migrations
- [ ] Zero-downtime migrations
- [ ] Data backfill patterns
- [ ] CI/CD integration

### Expert ✅
- [ ] Embedded migrations
- [ ] Blue-green deployments
- [ ] Schema validation
- [ ] Automated rollback
