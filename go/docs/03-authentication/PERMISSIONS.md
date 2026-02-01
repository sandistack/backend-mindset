# 🔒 Permissions & RBAC di Go

## Kenapa Penting?

Authorization yang baik:
- ✅ Granular access control
- ✅ Scalable permission system
- ✅ Separation of concerns
- ✅ Audit trail

---

## 📚 Daftar Isi

1. [RBAC Basics](#1️⃣-rbac-basics)
2. [Simple Role-Based Access](#2️⃣-simple-role-based-access)
3. [Casbin Integration](#3️⃣-casbin-integration)
4. [Permission Middleware](#4️⃣-permission-middleware)
5. [Resource-Based Permissions](#5️⃣-resource-based-permissions)
6. [Dynamic Permissions](#6️⃣-dynamic-permissions)

---

## 1️⃣ RBAC Basics

### Role-Based Access Control Concepts

```
User → has → Role → has → Permissions

Example:
- User: john@example.com
  - Role: editor
    - Permissions: tasks.create, tasks.update, tasks.read

- User: admin@example.com
  - Role: admin
    - Permissions: *, users.delete, settings.update
```

### Database Schema

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Roles table
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Permissions table
CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    resource VARCHAR(50),
    action VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- User-Role mapping (many-to-many)
CREATE TABLE user_roles (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- Role-Permission mapping (many-to-many)
CREATE TABLE role_permissions (
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- Seed data
INSERT INTO roles (name, description) VALUES
    ('admin', 'Administrator with full access'),
    ('editor', 'Can create and edit content'),
    ('viewer', 'Read-only access');

INSERT INTO permissions (name, resource, action) VALUES
    ('tasks.create', 'tasks', 'create'),
    ('tasks.read', 'tasks', 'read'),
    ('tasks.update', 'tasks', 'update'),
    ('tasks.delete', 'tasks', 'delete'),
    ('users.manage', 'users', 'manage'),
    ('settings.update', 'settings', 'update');

-- Assign permissions to roles
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'admin'; -- Admin gets all permissions

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'editor' AND p.name IN ('tasks.create', 'tasks.read', 'tasks.update');

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'viewer' AND p.name = 'tasks.read';
```

---

## 2️⃣ Simple Role-Based Access

### Domain Models

```go
// internal/domain/permission.go
package domain

type User struct {
    ID    int
    Email string
    Roles []Role
}

type Role struct {
    ID          int
    Name        string
    Permissions []Permission
}

type Permission struct {
    ID       int
    Name     string
    Resource string
    Action   string
}

func (u *User) HasRole(roleName string) bool {
    for _, role := range u.Roles {
        if role.Name == roleName {
            return true
        }
    }
    return false
}

func (u *User) HasPermission(permissionName string) bool {
    for _, role := range u.Roles {
        for _, perm := range role.Permissions {
            if perm.Name == permissionName {
                return true
            }
        }
    }
    return false
}

func (u *User) HasAnyPermission(permissions ...string) bool {
    for _, p := range permissions {
        if u.HasPermission(p) {
            return true
        }
    }
    return false
}

func (u *User) HasAllPermissions(permissions ...string) bool {
    for _, p := range permissions {
        if !u.HasPermission(p) {
            return false
        }
    }
    return true
}
```

### Repository

```go
// internal/repository/user_repo.go
package repository

func (r *UserRepository) GetUserWithRoles(ctx context.Context, userID int) (*domain.User, error) {
    query := `
        SELECT DISTINCT
            u.id, u.email,
            r.id, r.name,
            p.id, p.name, p.resource, p.action
        FROM users u
        LEFT JOIN user_roles ur ON u.id = ur.user_id
        LEFT JOIN roles r ON ur.role_id = r.id
        LEFT JOIN role_permissions rp ON r.id = rp.role_id
        LEFT JOIN permissions p ON rp.permission_id = p.id
        WHERE u.id = $1
    `
    
    rows, err := r.db.QueryContext(ctx, query, userID)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    
    var user *domain.User
    rolesMap := make(map[int]*domain.Role)
    
    for rows.Next() {
        var (
            userID, roleID, permID         sql.NullInt64
            email, roleName, permName      sql.NullString
            permResource, permAction       sql.NullString
        )
        
        if err := rows.Scan(
            &userID, &email,
            &roleID, &roleName,
            &permID, &permName, &permResource, &permAction,
        ); err != nil {
            return nil, err
        }
        
        // Initialize user
        if user == nil {
            user = &domain.User{
                ID:    int(userID.Int64),
                Email: email.String,
                Roles: []domain.Role{},
            }
        }
        
        // Add role if not exists
        if roleID.Valid {
            role, exists := rolesMap[int(roleID.Int64)]
            if !exists {
                role = &domain.Role{
                    ID:          int(roleID.Int64),
                    Name:        roleName.String,
                    Permissions: []domain.Permission{},
                }
                rolesMap[int(roleID.Int64)] = role
            }
            
            // Add permission to role
            if permID.Valid {
                role.Permissions = append(role.Permissions, domain.Permission{
                    ID:       int(permID.Int64),
                    Name:     permName.String,
                    Resource: permResource.String,
                    Action:   permAction.String,
                })
            }
        }
    }
    
    // Convert map to slice
    if user != nil {
        for _, role := range rolesMap {
            user.Roles = append(user.Roles, *role)
        }
    }
    
    return user, nil
}
```

### Middleware

```go
// internal/middleware/permission.go
package middleware

import (
    "context"
    "net/http"
    
    "myapp/internal/domain"
)

func RequirePermission(permissions ...string) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            user := GetUser(r.Context())
            if user == nil {
                http.Error(w, "Unauthorized", http.StatusUnauthorized)
                return
            }
            
            // Check if user has any of the required permissions
            if !user.HasAnyPermission(permissions...) {
                http.Error(w, "Forbidden", http.StatusForbidden)
                return
            }
            
            next.ServeHTTP(w, r)
        })
    }
}

func RequireRole(roles ...string) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            user := GetUser(r.Context())
            if user == nil {
                http.Error(w, "Unauthorized", http.StatusUnauthorized)
                return
            }
            
            // Check if user has any of the required roles
            hasRole := false
            for _, role := range roles {
                if user.HasRole(role) {
                    hasRole = true
                    break
                }
            }
            
            if !hasRole {
                http.Error(w, "Forbidden", http.StatusForbidden)
                return
            }
            
            next.ServeHTTP(w, r)
        })
    }
}
```

### Usage

```go
// cmd/api/routes.go
func SetupRoutes(r *chi.Mux) {
    // Public routes
    r.Post("/auth/login", loginHandler)
    
    // Protected routes
    r.Group(func(r chi.Router) {
        r.Use(middleware.Auth)
        
        // Tasks - anyone authenticated can read
        r.With(middleware.RequirePermission("tasks.read")).
            Get("/tasks", listTasksHandler)
        
        // Tasks - need create permission
        r.With(middleware.RequirePermission("tasks.create")).
            Post("/tasks", createTaskHandler)
        
        // Tasks - need update permission
        r.With(middleware.RequirePermission("tasks.update")).
            Put("/tasks/{id}", updateTaskHandler)
        
        // Tasks - need delete permission
        r.With(middleware.RequirePermission("tasks.delete")).
            Delete("/tasks/{id}", deleteTaskHandler)
        
        // Admin only routes
        r.With(middleware.RequireRole("admin")).
            Route("/admin", func(r chi.Router) {
                r.Get("/users", listAllUsersHandler)
                r.Delete("/users/{id}", deleteUserHandler)
            })
    })
}
```

---

## 3️⃣ Casbin Integration

### Installation

```bash
go get github.com/casbin/casbin/v2
go get github.com/casbin/gorm-adapter/v3
```

### Model Definition

```ini
# config/casbin_model.conf
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act

[role_definition]
g = _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = g(r.sub, p.sub) && r.obj == p.obj && r.act == p.act
```

### Policy Definition

```csv
# config/casbin_policy.csv
p, admin, tasks, create
p, admin, tasks, read
p, admin, tasks, update
p, admin, tasks, delete
p, admin, users, manage

p, editor, tasks, create
p, editor, tasks, read
p, editor, tasks, update

p, viewer, tasks, read

g, user:1, admin
g, user:2, editor
g, user:3, viewer
```

### Setup Casbin

```go
// internal/auth/casbin.go
package auth

import (
    "fmt"
    
    "github.com/casbin/casbin/v2"
    gormadapter "github.com/casbin/gorm-adapter/v3"
    "gorm.io/gorm"
)

func SetupCasbin(db *gorm.DB) (*casbin.Enforcer, error) {
    // Use GORM adapter
    adapter, err := gormadapter.NewAdapterByDB(db)
    if err != nil {
        return nil, fmt.Errorf("failed to create adapter: %w", err)
    }
    
    // Load model from file
    enforcer, err := casbin.NewEnforcer("config/casbin_model.conf", adapter)
    if err != nil {
        return nil, fmt.Errorf("failed to create enforcer: %w", err)
    }
    
    // Load policies from DB
    if err := enforcer.LoadPolicy(); err != nil {
        return nil, fmt.Errorf("failed to load policy: %w", err)
    }
    
    return enforcer, nil
}

// Alternative: Setup with file adapter
func SetupCasbinWithFile() (*casbin.Enforcer, error) {
    enforcer, err := casbin.NewEnforcer(
        "config/casbin_model.conf",
        "config/casbin_policy.csv",
    )
    if err != nil {
        return nil, err
    }
    
    return enforcer, nil
}
```

### Casbin Middleware

```go
// internal/middleware/casbin.go
package middleware

import (
    "fmt"
    "net/http"
    
    "github.com/casbin/casbin/v2"
)

func CasbinAuthorizer(enforcer *casbin.Enforcer) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            user := GetUser(r.Context())
            if user == nil {
                http.Error(w, "Unauthorized", http.StatusUnauthorized)
                return
            }
            
            // Get resource and action from route
            resource := getResourceFromPath(r.URL.Path) // e.g., "tasks"
            action := getActionFromMethod(r.Method)      // e.g., "read", "create"
            
            // Check permission with Casbin
            sub := fmt.Sprintf("user:%d", user.ID)
            allowed, err := enforcer.Enforce(sub, resource, action)
            if err != nil {
                http.Error(w, "Permission check failed", http.StatusInternalServerError)
                return
            }
            
            if !allowed {
                http.Error(w, "Forbidden", http.StatusForbidden)
                return
            }
            
            next.ServeHTTP(w, r)
        })
    }
}

func getResourceFromPath(path string) string {
    // Extract resource from path
    // /api/tasks -> "tasks"
    // /api/users/{id} -> "users"
    parts := strings.Split(strings.Trim(path, "/"), "/")
    if len(parts) >= 2 {
        return parts[1]
    }
    return ""
}

func getActionFromMethod(method string) string {
    switch method {
    case http.MethodGet:
        return "read"
    case http.MethodPost:
        return "create"
    case http.MethodPut, http.MethodPatch:
        return "update"
    case http.MethodDelete:
        return "delete"
    default:
        return ""
    }
}
```

### Managing Policies

```go
// internal/service/permission_service.go
package service

import (
    "github.com/casbin/casbin/v2"
)

type PermissionService struct {
    enforcer *casbin.Enforcer
}

func NewPermissionService(enforcer *casbin.Enforcer) *PermissionService {
    return &PermissionService{enforcer: enforcer}
}

// Add role to user
func (s *PermissionService) AssignRole(userID int, role string) error {
    sub := fmt.Sprintf("user:%d", userID)
    _, err := s.enforcer.AddRoleForUser(sub, role)
    if err != nil {
        return err
    }
    return s.enforcer.SavePolicy()
}

// Remove role from user
func (s *PermissionService) RemoveRole(userID int, role string) error {
    sub := fmt.Sprintf("user:%d", userID)
    _, err := s.enforcer.DeleteRoleForUser(sub, role)
    if err != nil {
        return err
    }
    return s.enforcer.SavePolicy()
}

// Get user roles
func (s *PermissionService) GetUserRoles(userID int) ([]string, error) {
    sub := fmt.Sprintf("user:%d", userID)
    return s.enforcer.GetRolesForUser(sub)
}

// Add permission to role
func (s *PermissionService) AddPermission(role, resource, action string) error {
    _, err := s.enforcer.AddPolicy(role, resource, action)
    if err != nil {
        return err
    }
    return s.enforcer.SavePolicy()
}

// Remove permission from role
func (s *PermissionService) RemovePermission(role, resource, action string) error {
    _, err := s.enforcer.RemovePolicy(role, resource, action)
    if err != nil {
        return err
    }
    return s.enforcer.SavePolicy()
}

// Check if user has permission
func (s *PermissionService) CheckPermission(userID int, resource, action string) (bool, error) {
    sub := fmt.Sprintf("user:%d", userID)
    return s.enforcer.Enforce(sub, resource, action)
}

// Get all permissions for role
func (s *PermissionService) GetRolePermissions(role string) [][]string {
    return s.enforcer.GetFilteredPolicy(0, role)
}
```

---

## 4️⃣ Permission Middleware

### Fine-Grained Permission Check

```go
// internal/middleware/resource_permission.go
package middleware

import (
    "context"
    "net/http"
    "strconv"
    
    "github.com/go-chi/chi/v5"
)

type ResourceChecker interface {
    CanAccess(ctx context.Context, userID, resourceID int, action string) (bool, error)
}

// Check if user can access specific resource
func RequireResourcePermission(checker ResourceChecker, action string) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            user := GetUser(r.Context())
            if user == nil {
                http.Error(w, "Unauthorized", http.StatusUnauthorized)
                return
            }
            
            // Get resource ID from URL
            resourceIDStr := chi.URLParam(r, "id")
            resourceID, err := strconv.Atoi(resourceIDStr)
            if err != nil {
                http.Error(w, "Invalid resource ID", http.StatusBadRequest)
                return
            }
            
            // Check if user can access this specific resource
            canAccess, err := checker.CanAccess(r.Context(), user.ID, resourceID, action)
            if err != nil {
                http.Error(w, "Permission check failed", http.StatusInternalServerError)
                return
            }
            
            if !canAccess {
                http.Error(w, "Forbidden", http.StatusForbidden)
                return
            }
            
            next.ServeHTTP(w, r)
        })
    }
}

// Task-specific checker
type TaskResourceChecker struct {
    taskRepo TaskRepository
}

func (c *TaskResourceChecker) CanAccess(ctx context.Context, userID, taskID int, action string) (bool, error) {
    task, err := c.taskRepo.GetByID(ctx, taskID)
    if err != nil {
        return false, err
    }
    
    user := GetUser(ctx)
    
    // Owners can do anything
    if task.UserID == userID {
        return true, nil
    }
    
    // Admins can do anything
    if user.HasRole("admin") {
        return true, nil
    }
    
    // Editors can read and update
    if action == "read" || action == "update" {
        return user.HasRole("editor"), nil
    }
    
    return false, nil
}
```

---

## 5️⃣ Resource-Based Permissions

### Ownership Check

```go
// internal/middleware/ownership.go
package middleware

func RequireOwnership(resourceGetter func(context.Context, int) (interface{ GetUserID() int }, error)) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            user := GetUser(r.Context())
            if user == nil {
                http.Error(w, "Unauthorized", http.StatusUnauthorized)
                return
            }
            
            // Skip ownership check for admins
            if user.HasRole("admin") {
                next.ServeHTTP(w, r)
                return
            }
            
            // Get resource ID
            resourceID, err := strconv.Atoi(chi.URLParam(r, "id"))
            if err != nil {
                http.Error(w, "Invalid ID", http.StatusBadRequest)
                return
            }
            
            // Get resource
            resource, err := resourceGetter(r.Context(), resourceID)
            if err != nil {
                http.Error(w, "Resource not found", http.StatusNotFound)
                return
            }
            
            // Check ownership
            if resource.GetUserID() != user.ID {
                http.Error(w, "Forbidden", http.StatusForbidden)
                return
            }
            
            next.ServeHTTP(w, r)
        })
    }
}

// Usage
r.With(
    RequireOwnership(taskService.GetByID),
).Put("/tasks/{id}", updateTaskHandler)
```

### ABAC (Attribute-Based Access Control)

```go
// internal/auth/abac.go
package auth

type Rule struct {
    Resource   string
    Action     string
    Conditions map[string]interface{}
}

type ABACEnforcer struct {
    rules []Rule
}

func (e *ABACEnforcer) Evaluate(user *User, resource string, action string, attributes map[string]interface{}) bool {
    for _, rule := range e.rules {
        if rule.Resource != resource || rule.Action != action {
            continue
        }
        
        // Check all conditions
        conditionsMet := true
        for key, expectedValue := range rule.Conditions {
            actualValue, ok := attributes[key]
            if !ok || actualValue != expectedValue {
                conditionsMet = false
                break
            }
        }
        
        if conditionsMet {
            return true
        }
    }
    
    return false
}

// Example: Can update task if user is owner OR admin
func (s *TaskService) CanUpdateTask(user *User, task *Task) bool {
    // Owner can always update
    if task.UserID == user.ID {
        return true
    }
    
    // Admin can update any task
    if user.HasRole("admin") {
        return true
    }
    
    // Editor can update if task is not completed
    if user.HasRole("editor") && task.Status != "DONE" {
        return true
    }
    
    return false
}
```

---

## 6️⃣ Dynamic Permissions

### Feature Flags & Permissions

```go
// internal/auth/feature_flags.go
package auth

type FeatureFlag struct {
    Name      string
    Enabled   bool
    Roles     []string
    UserIDs   []int
}

type FeatureFlagService struct {
    flags map[string]*FeatureFlag
}

func (s *FeatureFlagService) IsEnabled(flagName string, user *User) bool {
    flag, exists := s.flags[flagName]
    if !exists || !flag.Enabled {
        return false
    }
    
    // Check if flag is enabled for specific users
    for _, userID := range flag.UserIDs {
        if userID == user.ID {
            return true
        }
    }
    
    // Check if flag is enabled for user's roles
    for _, role := range user.Roles {
        for _, flagRole := range flag.Roles {
            if role.Name == flagRole {
                return true
            }
        }
    }
    
    return false
}

// Middleware
func RequireFeature(featureService *FeatureFlagService, feature string) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            user := GetUser(r.Context())
            
            if !featureService.IsEnabled(feature, user) {
                http.Error(w, "Feature not available", http.StatusForbidden)
                return
            }
            
            next.ServeHTTP(w, r)
        })
    }
}
```

### Temporary Permissions

```go
// internal/auth/temporary_permissions.go
package auth

type TemporaryPermission struct {
    UserID     int
    Permission string
    ExpiresAt  time.Time
}

type TempPermissionService struct {
    repo TempPermissionRepository
}

func (s *TempPermissionService) Grant(userID int, permission string, duration time.Duration) error {
    temp := &TemporaryPermission{
        UserID:     userID,
        Permission: permission,
        ExpiresAt:  time.Now().Add(duration),
    }
    return s.repo.Create(temp)
}

func (s *TempPermissionService) HasTempPermission(userID int, permission string) (bool, error) {
    temp, err := s.repo.GetActivePermission(userID, permission)
    if err != nil {
        return false, err
    }
    
    if temp == nil {
        return false, nil
    }
    
    // Check if expired
    if time.Now().After(temp.ExpiresAt) {
        s.repo.Delete(temp.ID)
        return false, nil
    }
    
    return true, nil
}
```

---

## 📋 Permission Checklist

### Junior ✅
- [ ] Simple role checking
- [ ] Basic permission middleware
- [ ] Hardcoded roles

### Mid ✅
- [ ] Database-backed RBAC
- [ ] Role-Permission mapping
- [ ] Ownership checks
- [ ] Resource-based permissions

### Senior ✅
- [ ] Casbin integration
- [ ] Dynamic policy management
- [ ] ABAC patterns
- [ ] Feature flags

### Expert ✅
- [ ] Multi-tenancy permissions
- [ ] Temporary permissions
- [ ] Audit logging
- [ ] Performance optimization (caching)
