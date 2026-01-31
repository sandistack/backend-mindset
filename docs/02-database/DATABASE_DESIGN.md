# 🗄️ DATABASE DESIGN - Fundamentals (Junior → Senior)

Dokumentasi lengkap tentang database design dari konsep dasar hingga advanced optimization.

---

## 🎯 Kenapa Database Design Penting?

**Bad Design:**
```
❌ Slow queries (10+ seconds)
❌ Data inconsistency
❌ Hard to maintain
❌ Doesn't scale
❌ Data loss risk
```

**Good Design:**
```
✅ Fast queries (< 100ms)
✅ Data integrity
✅ Easy to maintain
✅ Scales well
✅ Data safe
```

---

## 1️⃣ JUNIOR LEVEL - Database Basics

### Relational Database (SQL)

Data disimpan dalam **tables** dengan **rows** dan **columns**.

```sql
-- Table: users
| id | name       | email            | created_at |
|----|------------|------------------|------------|
| 1  | John Doe   | john@email.com   | 2024-01-01 |
| 2  | Jane Smith | jane@email.com   | 2024-01-02 |

-- Table: tasks
| id | title        | user_id | status  |
|----|--------------|---------|---------|
| 1  | Buy groceries| 1       | done    |
| 2  | Learn SQL    | 1       | pending |
| 3  | Write docs   | 2       | pending |
```

### Primary Key

Unique identifier untuk setiap row.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,  -- Auto-increment
    name VARCHAR(100),
    email VARCHAR(255) UNIQUE
);

-- Or using UUID
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100),
    email VARCHAR(255) UNIQUE
);
```

### Foreign Key

Relasi antara tables.

```sql
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200),
    user_id INTEGER REFERENCES users(id),  -- Foreign key
    status VARCHAR(20)
);
```

### Basic Data Types

| Type | Description | Example |
|------|-------------|---------|
| `INTEGER` | Whole numbers | 1, 42, -100 |
| `BIGINT` | Large integers | User IDs |
| `VARCHAR(n)` | Variable text | Names, emails |
| `TEXT` | Long text | Descriptions |
| `BOOLEAN` | True/False | is_active |
| `TIMESTAMP` | Date + time | created_at |
| `DATE` | Date only | birth_date |
| `DECIMAL(p,s)` | Precise numbers | Prices |
| `JSON/JSONB` | JSON data | Metadata |
| `UUID` | Unique ID | Primary keys |

---

## 2️⃣ MID LEVEL - Relationships

### One-to-One (1:1)

Satu record di table A = satu record di table B.

```sql
-- User has one profile
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE
);

CREATE TABLE profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id),  -- UNIQUE = 1:1
    bio TEXT,
    avatar_url TEXT
);
```

```
users           profiles
┌────┐          ┌────┐
│ 1  │─────────→│ 1  │
├────┤          ├────┤
│ 2  │─────────→│ 2  │
└────┘          └────┘
```

### One-to-Many (1:N)

Satu record di table A = banyak record di table B.

```sql
-- User has many tasks
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100)
);

CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200),
    user_id INTEGER REFERENCES users(id)  -- No UNIQUE = 1:N
);
```

```
users           tasks
┌────┐          ┌────┐
│ 1  │─────────→│ 1  │
│    │─────────→│ 2  │
│    │─────────→│ 3  │
├────┤          ├────┤
│ 2  │─────────→│ 4  │
│    │─────────→│ 5  │
└────┘          └────┘
```

### Many-to-Many (N:M)

Banyak record di table A = banyak record di table B.

```sql
-- Users can have many roles, roles can have many users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100)
);

CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50)
);

-- Junction/pivot table
CREATE TABLE user_roles (
    user_id INTEGER REFERENCES users(id),
    role_id INTEGER REFERENCES roles(id),
    PRIMARY KEY (user_id, role_id)  -- Composite primary key
);
```

```
users           user_roles       roles
┌────┐          ┌────┬────┐     ┌────┐
│ 1  │─────────→│ 1  │ 1  │←────│ 1  │ (admin)
│    │─────────→│ 1  │ 2  │←┐   ├────┤
├────┤          ├────┼────┤ └───│ 2  │ (editor)
│ 2  │─────────→│ 2  │ 2  │     └────┘
└────┘          └────┴────┘
```

---

## 3️⃣ MID-SENIOR LEVEL - Normalization

### Why Normalize?

**Denormalized (Bad):**
```
| order_id | customer_name | customer_email   | product_name | price |
|----------|---------------|------------------|--------------|-------|
| 1        | John Doe      | john@email.com   | Laptop       | 1000  |
| 2        | John Doe      | john@email.com   | Mouse        | 50    |
| 3        | Jane Smith    | jane@email.com   | Laptop       | 1000  |
```

**Problems:**
- ❌ Data duplication (John's info repeated)
- ❌ Update anomaly (change email = update many rows)
- ❌ Insert anomaly (can't add customer without order)
- ❌ Delete anomaly (delete order = lose customer info)

### 1NF (First Normal Form)

**Rules:**
- Each cell contains single value (atomic)
- Each row is unique
- No repeating groups

```sql
-- ❌ Bad: Multiple values in one cell
| id | name | phone_numbers           |
|----|------|-------------------------|
| 1  | John | 123-456, 789-012        |

-- ✅ Good: Separate table
| user_id | phone_number |
|---------|--------------|
| 1       | 123-456      |
| 1       | 789-012      |
```

### 2NF (Second Normal Form)

**Rules:**
- Must be 1NF
- No partial dependency (all non-key columns depend on FULL primary key)

```sql
-- ❌ Bad: product_name depends only on product_id, not order_id
| order_id | product_id | product_name | quantity |
|----------|------------|--------------|----------|
| 1        | 101        | Laptop       | 2        |

-- ✅ Good: Separate tables
-- orders
| order_id | product_id | quantity |

-- products
| product_id | product_name |
```

### 3NF (Third Normal Form)

**Rules:**
- Must be 2NF
- No transitive dependency (non-key depends on non-key)

```sql
-- ❌ Bad: city depends on zip_code, not on id
| id | name | zip_code | city     |
|----|------|----------|----------|
| 1  | John | 12345    | New York |

-- ✅ Good: Separate tables
-- users
| id | name | zip_code |

-- zip_codes
| zip_code | city     |
```

### Normalized Design

```sql
-- Fully normalized e-commerce
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(255) UNIQUE
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200),
    price DECIMAL(10,2)
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER,
    price_at_order DECIMAL(10,2)  -- Store price at time of order
);
```

---

## 4️⃣ SENIOR LEVEL - Indexing

### Why Index?

```sql
-- Without index: Full table scan (slow)
SELECT * FROM users WHERE email = 'john@email.com';
-- Scans 1,000,000 rows 😱

-- With index: Direct lookup (fast)
CREATE INDEX idx_users_email ON users(email);
-- Finds in 3-4 lookups 🚀
```

### Types of Indexes

**B-Tree (Default):**
```sql
-- Best for: equality, range queries
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_tasks_created ON tasks(created_at);

-- Usage
WHERE email = 'john@email.com'
WHERE created_at > '2024-01-01'
WHERE created_at BETWEEN '2024-01-01' AND '2024-12-31'
```

**Hash:**
```sql
-- Best for: equality only (faster than B-Tree for =)
CREATE INDEX idx_users_email ON users USING HASH(email);

-- Usage
WHERE email = 'john@email.com'
```

**GIN (Generalized Inverted):**
```sql
-- Best for: arrays, full-text search, JSONB
CREATE INDEX idx_posts_tags ON posts USING GIN(tags);
CREATE INDEX idx_users_meta ON users USING GIN(metadata);

-- Usage
WHERE tags @> ARRAY['python']
WHERE metadata @> '{"role": "admin"}'
```

**GiST (Generalized Search Tree):**
```sql
-- Best for: geometric data, full-text search
CREATE INDEX idx_locations_point ON locations USING GIST(coordinates);
```

### Composite Index

```sql
-- Index on multiple columns
CREATE INDEX idx_tasks_user_status ON tasks(user_id, status);

-- Works for:
WHERE user_id = 1
WHERE user_id = 1 AND status = 'done'

-- Doesn't work for:
WHERE status = 'done'  -- First column not used
```

### Index Best Practices

```sql
-- ✅ Good: Index frequently queried columns
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_tasks_user_id ON tasks(user_id);

-- ✅ Good: Index foreign keys
CREATE INDEX idx_tasks_user_id ON tasks(user_id);

-- ✅ Good: Covering index (includes all needed columns)
CREATE INDEX idx_tasks_covering ON tasks(user_id) INCLUDE (title, status);

-- ❌ Bad: Too many indexes (slows writes)
-- ❌ Bad: Index on low-cardinality columns (e.g., boolean)
-- ❌ Bad: Index on rarely queried columns
```

### Check Query Performance

```sql
-- EXPLAIN ANALYZE
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'john@email.com';

-- Result shows:
-- Index Scan vs Seq Scan
-- Actual time
-- Rows examined
```

---

## 5️⃣ SENIOR LEVEL - SQL vs NoSQL

### SQL (Relational)

**Examples:** PostgreSQL, MySQL, SQLite

**Best for:**
- ✅ Complex queries (JOINs)
- ✅ ACID transactions
- ✅ Data integrity
- ✅ Structured data

```sql
SELECT u.name, COUNT(t.id) as task_count
FROM users u
LEFT JOIN tasks t ON u.id = t.user_id
WHERE t.status = 'done'
GROUP BY u.id
HAVING COUNT(t.id) > 5
ORDER BY task_count DESC;
```

### NoSQL (Document)

**Examples:** MongoDB, CouchDB

**Best for:**
- ✅ Flexible schema
- ✅ Rapid development
- ✅ Horizontal scaling
- ✅ Unstructured data

```javascript
// MongoDB
db.users.insertOne({
    name: "John Doe",
    email: "john@email.com",
    tasks: [
        { title: "Task 1", status: "done" },
        { title: "Task 2", status: "pending" }
    ],
    metadata: {
        lastLogin: new Date(),
        preferences: { theme: "dark" }
    }
});
```

### NoSQL (Key-Value)

**Examples:** Redis, Memcached

**Best for:**
- ✅ Caching
- ✅ Session storage
- ✅ Real-time data
- ✅ Simple lookups

```bash
# Redis
SET user:123 '{"name": "John", "email": "john@email.com"}'
GET user:123
```

### NoSQL (Column-Family)

**Examples:** Cassandra, HBase

**Best for:**
- ✅ Time-series data
- ✅ Write-heavy workloads
- ✅ Massive scale

### NoSQL (Graph)

**Examples:** Neo4j, Amazon Neptune

**Best for:**
- ✅ Social networks
- ✅ Recommendation engines
- ✅ Complex relationships

```cypher
// Neo4j - Find friends of friends
MATCH (user:Person {name: "John"})-[:FRIEND]->()-[:FRIEND]->(fof)
RETURN fof.name
```

### Comparison

| Aspect | SQL | NoSQL |
|--------|-----|-------|
| **Schema** | Rigid | Flexible |
| **Scaling** | Vertical | Horizontal |
| **Transactions** | ACID | BASE (eventual) |
| **Queries** | Complex JOINs | Simple lookups |
| **Data** | Structured | Unstructured |
| **Best For** | Banking, ERP | Social, IoT |

---

## 6️⃣ EXPERT LEVEL - ACID vs BASE

### ACID (SQL)

```
A - Atomicity     : All or nothing
C - Consistency   : Valid state always
I - Isolation     : Transactions independent
D - Durability    : Committed = permanent
```

```sql
-- Transaction example
BEGIN;

UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;

-- If any fails, rollback all
COMMIT;  -- or ROLLBACK;
```

### BASE (NoSQL)

```
BA - Basically Available  : System always responds
S  - Soft state          : State may change over time
E  - Eventually Consistent: Will be consistent eventually
```

```javascript
// Eventually consistent
// Write to primary
db.users.insertOne({ name: "John" });

// Replicas may not have data immediately
// But will eventually sync
```

---

## 7️⃣ EXPERT LEVEL - Scaling Strategies

### Vertical Scaling (Scale Up)

```
Add more power to single server:
- More CPU
- More RAM
- Faster SSD

Pros: Simple
Cons: Has limits, expensive
```

### Horizontal Scaling (Scale Out)

**Read Replicas:**
```
                ┌─────────────┐
   Writes ─────→│   Primary   │
                └──────┬──────┘
                       │ Replication
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
  ┌──────────┐   ┌──────────┐   ┌──────────┐
  │ Replica 1│   │ Replica 2│   │ Replica 3│
  └──────────┘   └──────────┘   └──────────┘
        ▲              ▲              ▲
        └──────────────┴──────────────┘
                  Reads
```

**Sharding:**
```
Data split across multiple servers:

Users A-H  → Shard 1
Users I-P  → Shard 2
Users Q-Z  → Shard 3

Or by ID range:
ID 1-1M    → Shard 1
ID 1M-2M   → Shard 2
ID 2M-3M   → Shard 3
```

### Partitioning

```sql
-- Range partitioning
CREATE TABLE logs (
    id SERIAL,
    message TEXT,
    created_at TIMESTAMP
) PARTITION BY RANGE (created_at);

CREATE TABLE logs_2024_01 PARTITION OF logs
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE logs_2024_02 PARTITION OF logs
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
```

---

## 8️⃣ EXPERT LEVEL - CAP Theorem

```
You can only have 2 of 3:

C - Consistency   : All nodes see same data
A - Availability  : System always responds
P - Partition Tolerance: System works despite network issues

            Consistency
               /\
              /  \
             /    \
            /  CA  \
           /________\
          /\        /\
         /  \  CP  /  \
        / AP \    /    \
       /______\  /______\
    Availability ──── Partition
```

**CP Systems:** MongoDB, Redis, HBase
- Consistent, handles partitions
- May be unavailable during partition

**AP Systems:** Cassandra, DynamoDB, CouchDB
- Available, handles partitions
- May be inconsistent temporarily

**CA Systems:** Traditional RDBMS (single node)
- Consistent, available
- Cannot handle partitions

---

## 📊 Quick Reference

### Design Checklist

- [ ] Identify entities (tables)
- [ ] Define relationships (1:1, 1:N, N:M)
- [ ] Normalize to 3NF
- [ ] Add primary keys
- [ ] Add foreign keys
- [ ] Add indexes on:
  - [ ] Foreign keys
  - [ ] Frequently queried columns
  - [ ] Columns used in WHERE, ORDER BY
- [ ] Consider denormalization for read performance
- [ ] Plan for scaling

### Common Patterns

**Soft Delete:**
```sql
ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP;

-- "Delete"
UPDATE users SET deleted_at = NOW() WHERE id = 1;

-- Query active users
SELECT * FROM users WHERE deleted_at IS NULL;
```

**Timestamps:**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Audit Log:**
```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100),
    record_id INTEGER,
    action VARCHAR(20),  -- INSERT, UPDATE, DELETE
    old_data JSONB,
    new_data JSONB,
    user_id INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 💡 Summary

| Level | Focus |
|-------|-------|
| **Junior** | Tables, relationships, basic SQL |
| **Mid** | 1:1, 1:N, N:M relationships |
| **Mid-Senior** | Normalization (1NF, 2NF, 3NF) |
| **Senior** | Indexing, SQL vs NoSQL |
| **Expert** | ACID/BASE, CAP, sharding |

**Golden Rules:**
- ✅ Design for your use case
- ✅ Normalize first, denormalize for performance
- ✅ Index foreign keys and frequently queried columns
- ✅ Use appropriate data types
- ✅ Plan for growth
- ✅ Backup regularly
- ✅ Monitor query performance

**Decision Guide:**
```
Need complex queries? → SQL
Need flexible schema? → NoSQL (Document)
Need speed + caching? → NoSQL (Key-Value)
Need massive writes?  → NoSQL (Column)
Need relationships?   → SQL or Graph
```
