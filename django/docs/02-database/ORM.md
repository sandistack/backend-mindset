# 🗄️ Django ORM Advanced Patterns

## Kenapa Penting?

ORM yang salah = performance nightmare:
- ❌ N+1 query problems
- ❌ Full table scans
- ❌ Memory overflow
- ❌ Slow API responses

ORM yang benar:
- ✅ Optimal queries
- ✅ Efficient memory usage
- ✅ Sub-millisecond responses
- ✅ Scalable architecture

---

## 📚 Daftar Isi

1. [QuerySet Basics](#1️⃣-queryset-basics)
2. [Select Related & Prefetch](#2️⃣-select-related--prefetch)
3. [F() dan Q() Objects](#3️⃣-f-dan-q-objects)
4. [Aggregation & Annotation](#4️⃣-aggregation--annotation)
5. [Subqueries](#5️⃣-subqueries)
6. [Raw SQL](#6️⃣-raw-sql)
7. [Database Functions](#7️⃣-database-functions)
8. [Query Optimization](#8️⃣-query-optimization)
9. [Bulk Operations](#9️⃣-bulk-operations)
10. [Transactions](#🔟-transactions)

---

## 1️⃣ QuerySet Basics

### QuerySets are Lazy

```python
# Query TIDAK dijalankan sampai evaluate
tasks = Task.objects.filter(status='TODO')  # No DB hit
tasks = tasks.filter(priority='HIGH')        # No DB hit
tasks = tasks.order_by('-created_at')        # No DB hit

# Query dijalankan saat:
list(tasks)           # Conversion to list
for task in tasks:    # Iteration
    print(task)
len(tasks)            # Count (use .count() instead!)
tasks[0]              # Indexing
bool(tasks)           # Boolean check (use .exists() instead!)
```

### Efficient Evaluation

```python
# ❌ Bad: Multiple queries
if len(tasks) > 0:        # Query 1: SELECT COUNT(*)
    first = tasks[0]      # Query 2: SELECT * LIMIT 1
    
# ✅ Good: Single query
first = tasks.first()
if first:
    # Use first

# ❌ Bad: Fetches all data just to check existence
if tasks:
    do_something()

# ✅ Good: Optimized existence check
if tasks.exists():
    do_something()

# ❌ Bad: Fetches all then counts
total = len(tasks)

# ✅ Good: Database COUNT
total = tasks.count()
```

### Chaining Methods

```python
# All these return new QuerySets
Task.objects.filter(status='TODO')
Task.objects.exclude(is_deleted=True)
Task.objects.order_by('-created_at')
Task.objects.select_related('user')
Task.objects.prefetch_related('tags')
Task.objects.only('id', 'title')
Task.objects.defer('description')
Task.objects.values('id', 'title')
Task.objects.values_list('id', flat=True)
Task.objects.distinct()
Task.objects.all()[:10]  # LIMIT 10
Task.objects.all()[10:20]  # OFFSET 10 LIMIT 10
```

---

## 2️⃣ Select Related & Prefetch

### The N+1 Problem

```python
# ❌ N+1 Problem: 1 + N queries
tasks = Task.objects.filter(user_id=1)
for task in tasks:
    print(task.user.username)  # Each access = new query!
    print(task.category.name)  # Another query per task!

# SQL executed:
# SELECT * FROM tasks WHERE user_id = 1;  (1 query)
# SELECT * FROM users WHERE id = 1;       (N queries)
# SELECT * FROM categories WHERE id = X;  (N queries)
```

### select_related (ForeignKey, OneToOne)

```python
# ✅ Single query with JOIN
tasks = Task.objects.select_related('user', 'category').filter(user_id=1)

for task in tasks:
    print(task.user.username)    # No extra query!
    print(task.category.name)    # No extra query!

# SQL executed:
# SELECT tasks.*, users.*, categories.*
# FROM tasks
# LEFT JOIN users ON tasks.user_id = users.id
# LEFT JOIN categories ON tasks.category_id = categories.id
# WHERE tasks.user_id = 1;
```

### prefetch_related (ManyToMany, Reverse FK)

```python
# ❌ Bad: N+1 for ManyToMany
tasks = Task.objects.all()
for task in tasks:
    print(task.tags.all())  # Query per task!

# ✅ Good: 2 queries total
tasks = Task.objects.prefetch_related('tags').all()

for task in tasks:
    print(task.tags.all())  # No extra query!

# SQL executed:
# SELECT * FROM tasks;
# SELECT * FROM task_tags WHERE task_id IN (1, 2, 3, ...);
```

### Custom Prefetch

```python
from django.db.models import Prefetch

# Prefetch with filtering
tasks = Task.objects.prefetch_related(
    Prefetch(
        'comments',
        queryset=Comment.objects.filter(is_approved=True).order_by('-created_at')[:5],
        to_attr='recent_comments'  # Store in different attribute
    )
)

for task in tasks:
    for comment in task.recent_comments:  # Use custom attribute
        print(comment.text)
```

### Combining Both

```python
# Complex example
tasks = Task.objects.select_related(
    'user',           # FK
    'category',       # FK
    'user__profile',  # Nested FK
).prefetch_related(
    'tags',           # M2M
    'attachments',    # Reverse FK
    Prefetch(
        'comments',
        queryset=Comment.objects.select_related('author').filter(is_approved=True)
    ),
).filter(
    status='IN_PROGRESS'
).order_by('-created_at')
```

---

## 3️⃣ F() dan Q() Objects

### F() - Reference Database Columns

```python
from django.db.models import F

# ❌ Bad: Race condition
task = Task.objects.get(id=1)
task.view_count = task.view_count + 1
task.save()

# ✅ Good: Atomic update
Task.objects.filter(id=1).update(view_count=F('view_count') + 1)

# Compare columns
overdue_tasks = Task.objects.filter(
    due_date__lt=F('created_at') + timedelta(days=7)
)

# Combine with expressions
from django.db.models import ExpressionWrapper, DurationField

tasks = Task.objects.annotate(
    time_to_complete=ExpressionWrapper(
        F('completed_at') - F('created_at'),
        output_field=DurationField()
    )
)

# Arithmetic with F()
products = Product.objects.annotate(
    discounted_price=F('price') * 0.9  # 10% discount
)
```

### Q() - Complex Lookups

```python
from django.db.models import Q

# OR condition
tasks = Task.objects.filter(
    Q(status='TODO') | Q(status='IN_PROGRESS')
)

# AND condition (explicit)
tasks = Task.objects.filter(
    Q(status='TODO') & Q(priority='HIGH')
)

# NOT condition
tasks = Task.objects.filter(
    ~Q(status='DONE')
)

# Complex combinations
tasks = Task.objects.filter(
    Q(status='TODO') | Q(priority='HIGH'),
    user=request.user,  # Regular filter (AND)
    ~Q(is_deleted=True)
)

# Dynamic query building
def search_tasks(filters):
    query = Q()
    
    if filters.get('status'):
        query &= Q(status=filters['status'])
    
    if filters.get('priority'):
        query &= Q(priority=filters['priority'])
    
    if filters.get('search'):
        query &= (
            Q(title__icontains=filters['search']) |
            Q(description__icontains=filters['search'])
        )
    
    if filters.get('exclude_done'):
        query &= ~Q(status='DONE')
    
    return Task.objects.filter(query)
```

---

## 4️⃣ Aggregation & Annotation

### Aggregate - Single Value

```python
from django.db.models import Count, Sum, Avg, Max, Min

# Single aggregate
result = Task.objects.aggregate(
    total=Count('id'),
    avg_priority=Avg('priority_score'),
    max_created=Max('created_at')
)
# Result: {'total': 100, 'avg_priority': 3.5, 'max_created': datetime(...)}

# Filtered aggregate
from django.db.models import Count, Q

result = Task.objects.aggregate(
    total=Count('id'),
    done=Count('id', filter=Q(status='DONE')),
    high_priority=Count('id', filter=Q(priority='HIGH'))
)
```

### Annotate - Per-Object Value

```python
# Add computed field to each object
users = User.objects.annotate(
    task_count=Count('tasks'),
    completed_count=Count('tasks', filter=Q(tasks__status='DONE')),
    pending_count=Count('tasks', filter=Q(tasks__status='TODO'))
)

for user in users:
    print(f"{user.username}: {user.task_count} tasks, {user.completed_count} done")

# Calculate completion rate
from django.db.models import Case, When, FloatField

users = User.objects.annotate(
    task_count=Count('tasks'),
    completed_count=Count('tasks', filter=Q(tasks__status='DONE'))
).annotate(
    completion_rate=Case(
        When(task_count=0, then=0.0),
        default=100.0 * F('completed_count') / F('task_count'),
        output_field=FloatField()
    )
)
```

### Group By

```python
# Group tasks by status
status_counts = Task.objects.values('status').annotate(
    count=Count('id')
).order_by('status')
# Result: [{'status': 'TODO', 'count': 50}, {'status': 'DONE', 'count': 30}, ...]

# Group by date
from django.db.models.functions import TruncDate

daily_tasks = Task.objects.annotate(
    date=TruncDate('created_at')
).values('date').annotate(
    count=Count('id')
).order_by('date')
# Result: [{'date': date(2024, 1, 1), 'count': 10}, ...]

# Multiple grouping
stats = Task.objects.values('status', 'priority').annotate(
    count=Count('id')
).order_by('status', 'priority')
```

---

## 5️⃣ Subqueries

### Basic Subquery

```python
from django.db.models import Subquery, OuterRef

# Get latest comment for each task
latest_comment = Comment.objects.filter(
    task=OuterRef('pk')
).order_by('-created_at')

tasks = Task.objects.annotate(
    latest_comment_text=Subquery(latest_comment.values('text')[:1])
)

# Get tasks where user has more than 5 tasks
active_users = User.objects.annotate(
    task_count=Count('tasks')
).filter(task_count__gt=5).values('id')

tasks_from_active_users = Task.objects.filter(
    user_id__in=Subquery(active_users)
)
```

### Exists Subquery

```python
from django.db.models import Exists, OuterRef

# Tasks that have at least one comment
has_comments = Comment.objects.filter(task=OuterRef('pk'))
tasks_with_comments = Task.objects.annotate(
    has_comments=Exists(has_comments)
).filter(has_comments=True)

# Users with overdue tasks
overdue_task = Task.objects.filter(
    user=OuterRef('pk'),
    due_date__lt=timezone.now(),
    status__in=['TODO', 'IN_PROGRESS']
)

users_with_overdue = User.objects.annotate(
    has_overdue=Exists(overdue_task)
).filter(has_overdue=True)
```

### Correlated Subquery

```python
# Rank within group
from django.db.models import Window, F
from django.db.models.functions import Rank

tasks = Task.objects.annotate(
    priority_rank=Window(
        expression=Rank(),
        partition_by=[F('user')],
        order_by=F('created_at').desc()
    )
).filter(priority_rank__lte=3)  # Top 3 per user
```

---

## 6️⃣ Raw SQL

### raw() - Returns Model Instances

```python
# Simple raw query
tasks = Task.objects.raw('SELECT * FROM tasks WHERE status = %s', ['TODO'])

for task in tasks:
    print(task.title)  # Regular model instance

# Raw with JOIN
tasks = Task.objects.raw('''
    SELECT t.*, u.username as user_name
    FROM tasks t
    JOIN users u ON t.user_id = u.id
    WHERE t.status = %s
''', ['TODO'])
```

### cursor() - Raw SQL Execution

```python
from django.db import connection

def get_task_stats():
    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT 
                status,
                COUNT(*) as count,
                AVG(EXTRACT(EPOCH FROM (completed_at - created_at))) as avg_completion_time
            FROM tasks
            WHERE completed_at IS NOT NULL
            GROUP BY status
        ''')
        
        columns = [col[0] for col in cursor.description]
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

# Named parameters
def search_tasks(query):
    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT * FROM tasks
            WHERE to_tsvector('english', title || ' ' || description)
                  @@ plainto_tsquery('english', %(query)s)
        ''', {'query': query})
        return cursor.fetchall()
```

### When to Use Raw SQL

```python
# ✅ Good use cases for raw SQL:
# 1. Complex analytics queries
# 2. Database-specific features (full-text search, window functions)
# 3. Performance-critical queries that ORM can't optimize
# 4. Bulk operations with complex logic

# ❌ Avoid raw SQL for:
# 1. Simple CRUD operations
# 2. Queries that ORM handles well
# 3. Queries that need to work across databases
```

---

## 7️⃣ Database Functions

### Built-in Functions

```python
from django.db.models.functions import (
    Lower, Upper, Length, Concat, Coalesce,
    Now, TruncDate, TruncMonth, ExtractYear,
    Cast, Greatest, Least
)
from django.db.models import CharField, IntegerField, Value

# String functions
users = User.objects.annotate(
    email_lower=Lower('email'),
    full_name=Concat('first_name', Value(' '), 'last_name'),
    name_length=Length('username')
)

# Date functions
tasks = Task.objects.annotate(
    created_date=TruncDate('created_at'),
    created_month=TruncMonth('created_at'),
    created_year=ExtractYear('created_at')
)

# Coalesce (first non-null value)
tasks = Task.objects.annotate(
    display_name=Coalesce('title', 'description', Value('Untitled'))
)

# Greatest/Least
products = Product.objects.annotate(
    best_price=Least('price', 'sale_price'),
    max_price=Greatest('price', 'suggested_price')
)
```

### Conditional Expressions

```python
from django.db.models import Case, When, Value, CharField, IntegerField

# CASE WHEN equivalent
tasks = Task.objects.annotate(
    priority_label=Case(
        When(priority='HIGH', then=Value('🔴 High')),
        When(priority='MEDIUM', then=Value('🟡 Medium')),
        When(priority='LOW', then=Value('🟢 Low')),
        default=Value('⚪ Unknown'),
        output_field=CharField()
    )
)

# Scoring
tasks = Task.objects.annotate(
    score=Case(
        When(priority='HIGH', status='DONE', then=Value(10)),
        When(priority='HIGH', then=Value(5)),
        When(status='DONE', then=Value(3)),
        default=Value(1),
        output_field=IntegerField()
    )
).order_by('-score')
```

### Custom Database Functions

```python
from django.db.models import Func, CharField

class SHA256(Func):
    """PostgreSQL SHA256 function"""
    function = 'ENCODE'
    template = "%(function)s(DIGEST(%(expressions)s, 'sha256'), 'hex')"
    output_field = CharField()


class ArrayLength(Func):
    """PostgreSQL array_length"""
    function = 'ARRAY_LENGTH'
    template = '%(function)s(%(expressions)s, 1)'
    output_field = IntegerField()


# Usage
users = User.objects.annotate(
    email_hash=SHA256('email')
)
```

---

## 8️⃣ Query Optimization

### .only() and .defer()

```python
# Only load specific fields
tasks = Task.objects.only('id', 'title', 'status')

# Exclude heavy fields
tasks = Task.objects.defer('description', 'content')  # Lazy load these

# For serializers - match exactly what's needed
class TaskListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'status']

class TaskListView(APIView):
    def get(self, request):
        tasks = Task.objects.only('id', 'title', 'status')
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data)
```

### .values() and .values_list()

```python
# Return dicts instead of model instances
task_data = Task.objects.filter(status='TODO').values('id', 'title')
# [{'id': 1, 'title': 'Task 1'}, {'id': 2, 'title': 'Task 2'}]

# Return tuples
task_tuples = Task.objects.filter(status='TODO').values_list('id', 'title')
# [(1, 'Task 1'), (2, 'Task 2')]

# Single column as flat list
task_ids = Task.objects.filter(status='TODO').values_list('id', flat=True)
# [1, 2, 3, 4, 5]
```

### Explain Query

```python
# Django 4.0+
qs = Task.objects.filter(status='TODO').select_related('user')
print(qs.explain())

# With analyze (actually runs query)
print(qs.explain(analyze=True))

# Output example:
# Seq Scan on tasks  (cost=0.00..12.50 rows=250 width=82)
#   Filter: (status = 'TODO')
```

### Query Logging

```python
# config/settings/development.py
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

### Django Debug Toolbar

```bash
pip install django-debug-toolbar
```

```python
# config/settings/development.py
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
INTERNAL_IPS = ['127.0.0.1']
```

---

## 9️⃣ Bulk Operations

### bulk_create()

```python
# ❌ Bad: N queries
for data in task_data_list:
    Task.objects.create(**data)

# ✅ Good: 1 query
tasks = [Task(**data) for data in task_data_list]
Task.objects.bulk_create(tasks)

# With batch size (for large datasets)
Task.objects.bulk_create(tasks, batch_size=1000)

# Ignore conflicts (PostgreSQL, SQLite)
Task.objects.bulk_create(
    tasks,
    ignore_conflicts=True  # Skip duplicates
)

# Update on conflict (PostgreSQL)
Task.objects.bulk_create(
    tasks,
    update_conflicts=True,
    update_fields=['status', 'updated_at'],
    unique_fields=['id']
)
```

### bulk_update()

```python
# ❌ Bad: N queries
for task in tasks:
    task.status = 'DONE'
    task.save()

# ✅ Good: 1 query
for task in tasks:
    task.status = 'DONE'

Task.objects.bulk_update(tasks, ['status'])

# With batch size
Task.objects.bulk_update(tasks, ['status', 'completed_at'], batch_size=1000)
```

### update() - Direct Database Update

```python
# Single query, no model loading
Task.objects.filter(status='TODO').update(
    status='IN_PROGRESS',
    updated_at=timezone.now()
)

# With F() expressions
Task.objects.filter(id__in=task_ids).update(
    view_count=F('view_count') + 1
)

# Conditional update
from django.db.models import Case, When

Task.objects.update(
    priority=Case(
        When(due_date__lt=timezone.now(), then=Value('HIGH')),
        default=F('priority')
    )
)
```

### delete() - Bulk Delete

```python
# Single query
deleted_count, _ = Task.objects.filter(
    status='DONE',
    completed_at__lt=timezone.now() - timedelta(days=30)
).delete()

# Note: This triggers signals for each object!
# For truly bulk delete without signals:
Task.objects.filter(...).delete()  # Calls pre_delete and post_delete

# Raw delete (no signals)
Task.objects.filter(...).delete()
```

---

## 🔟 Transactions

### atomic()

```python
from django.db import transaction

# As decorator
@transaction.atomic
def create_task_with_subtasks(user, data):
    task = Task.objects.create(user=user, **data['task'])
    
    for subtask_data in data['subtasks']:
        Subtask.objects.create(task=task, **subtask_data)
    
    # If any error occurs, everything is rolled back
    return task

# As context manager
def transfer_task(task_id, new_user):
    with transaction.atomic():
        task = Task.objects.select_for_update().get(id=task_id)
        old_user = task.user
        
        task.user = new_user
        task.save()
        
        TaskHistory.objects.create(
            task=task,
            action='transferred',
            from_user=old_user,
            to_user=new_user
        )
```

### select_for_update()

```python
# Lock rows for update (prevent concurrent modifications)
with transaction.atomic():
    task = Task.objects.select_for_update().get(id=task_id)
    
    # Other transactions trying to modify this row will wait
    task.status = 'IN_PROGRESS'
    task.save()

# Skip locked rows
tasks = Task.objects.select_for_update(skip_locked=True).filter(
    status='PENDING'
)[:10]

# nowait - raise error instead of waiting
try:
    task = Task.objects.select_for_update(nowait=True).get(id=task_id)
except DatabaseError:
    # Row is locked by another transaction
    pass
```

### Savepoints

```python
from django.db import transaction

def process_tasks(tasks):
    with transaction.atomic():
        for task in tasks:
            savepoint = transaction.savepoint()
            
            try:
                process_single_task(task)
            except ProcessingError:
                transaction.savepoint_rollback(savepoint)
                # Continue with next task
            else:
                transaction.savepoint_commit(savepoint)
```

### on_commit()

```python
from django.db import transaction

def create_task(user, data):
    with transaction.atomic():
        task = Task.objects.create(user=user, **data)
        
        # This runs AFTER transaction commits successfully
        transaction.on_commit(
            lambda: send_notification.delay(task.id)
        )
        
        return task
```

---

## 📊 Performance Cheat Sheet

| Operation | Instead of | Use |
|-----------|------------|-----|
| Get single | `filter()[0]` | `first()` or `get()` |
| Check existence | `len(qs) > 0` | `qs.exists()` |
| Count | `len(qs)` | `qs.count()` |
| FK access | Loop with FK | `select_related()` |
| M2M access | Loop with M2M | `prefetch_related()` |
| Atomic increment | `obj.count += 1` | `F('count') + 1` |
| Multiple creates | Loop `create()` | `bulk_create()` |
| Multiple updates | Loop `save()` | `bulk_update()` |
| Complex OR | Multiple queries | `Q()` objects |

---

## 📋 ORM Checklist

### Junior ✅
- [ ] Understand QuerySet laziness
- [ ] Use `first()`, `exists()`, `count()` correctly
- [ ] Basic `filter()` and `exclude()`
- [ ] Simple `order_by()`

### Mid ✅
- [ ] `select_related()` for ForeignKey
- [ ] `prefetch_related()` for ManyToMany
- [ ] `F()` for atomic updates
- [ ] `Q()` for complex queries
- [ ] Basic aggregation

### Senior ✅
- [ ] Custom Prefetch objects
- [ ] Subqueries
- [ ] Window functions
- [ ] Complex annotations
- [ ] Query optimization (only, defer)
- [ ] Bulk operations

### Expert ✅
- [ ] Raw SQL when needed
- [ ] Custom database functions
- [ ] Query explain analysis
- [ ] Transaction management
- [ ] select_for_update patterns
- [ ] Database-specific optimizations
