# 🔄 MIGRATIONS - Django (Junior → Senior)

Dokumentasi lengkap tentang Django Migrations dari basic hingga advanced strategies.

---

## 🎯 Apa itu Migrations?

**Migrations** = Version control untuk database schema.

```
Code Changes              Database Changes
────────────              ────────────────
models.py         →       migrations/       →       Database
(Python)                  (Migration Files)         (Tables)

# Workflow:
1. Edit models.py
2. makemigrations (generate migration file)
3. migrate (apply to database)
```

**Benefits:**
- ✅ Track schema changes over time
- ✅ Reproducible database setup
- ✅ Team collaboration
- ✅ Rollback capability
- ✅ Database agnostic

---

## 1️⃣ JUNIOR LEVEL - Basic Migrations

### Create & Apply Migrations

```bash
# Create migrations from model changes
python manage.py makemigrations

# Create migration for specific app
python manage.py makemigrations tasks

# Show what will be migrated (dry run)
python manage.py makemigrations --dry-run

# Apply all pending migrations
python manage.py migrate

# Apply migrations for specific app
python manage.py migrate tasks

# Show migration status
python manage.py showmigrations
```

### Migration File Structure

```python
# apps/tasks/migrations/0001_initial.py
from django.db import migrations, models


class Migration(migrations.Migration):
    
    initial = True  # First migration for this app
    
    dependencies = [
        # Other migrations this depends on
        ('auth', '0012_alter_user_first_name_max_length'),
    ]
    
    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(primary_key=True)),
                ('title', models.CharField(max_length=200)),
                ('status', models.CharField(max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
```

### Migration Naming

```bash
# Auto-generated name
python manage.py makemigrations
# → 0002_auto_20240115_1430.py (not descriptive)

# Custom name (recommended)
python manage.py makemigrations --name add_priority_to_task
# → 0002_add_priority_to_task.py (descriptive!)
```

---

## 2️⃣ MID LEVEL - Common Operations

### Add Field

```python
# models.py - Add new field
class Task(models.Model):
    title = models.CharField(max_length=200)
    priority = models.IntegerField(default=0)  # NEW FIELD
```

```bash
python manage.py makemigrations --name add_priority_to_task
```

```python
# Generated migration
operations = [
    migrations.AddField(
        model_name='task',
        name='priority',
        field=models.IntegerField(default=0),
    ),
]
```

### Add Field (Nullable vs Default)

```python
# Option 1: With default value
priority = models.IntegerField(default=0)  # ✅ Safe

# Option 2: Nullable field
priority = models.IntegerField(null=True, blank=True)  # ✅ Safe

# Option 3: Required field without default
priority = models.IntegerField()  # ⚠️ Requires manual handling
# Django will ask: Provide default or quit?
```

### Remove Field

```python
# models.py - Remove field
class Task(models.Model):
    title = models.CharField(max_length=200)
    # priority = models.IntegerField()  ← REMOVED
```

```bash
python manage.py makemigrations --name remove_priority_from_task
```

### Rename Field

```python
# models.py - Rename field
class Task(models.Model):
    name = models.CharField(max_length=200)  # was: title
```

```bash
python manage.py makemigrations --name rename_title_to_name
# Django will ask: Did you rename task.title to task.name? [y/N]
# Answer: y
```

### Change Field Type

```python
# models.py - Change field type
class Task(models.Model):
    # Before: priority = models.IntegerField()
    priority = models.CharField(max_length=20)  # Changed to CharField
```

**⚠️ Warning:** Changing field types can cause data loss!

---

## 3️⃣ MID-SENIOR LEVEL - Data Migrations

### What is Data Migration?

```
Schema Migration: Change table structure (columns)
Data Migration:   Change data in tables (rows)
```

### Create Empty Migration

```bash
python manage.py makemigrations --empty tasks --name populate_slug
```

### Data Migration Example

```python
# apps/tasks/migrations/0003_populate_slug.py
from django.db import migrations
from django.utils.text import slugify


def populate_slugs(apps, schema_editor):
    """
    Forward migration: Populate slug field
    """
    Task = apps.get_model('tasks', 'Task')
    
    for task in Task.objects.all():
        if not task.slug:
            task.slug = slugify(task.title)
            task.save(update_fields=['slug'])


def reverse_slugs(apps, schema_editor):
    """
    Reverse migration: Clear slug field
    """
    Task = apps.get_model('tasks', 'Task')
    Task.objects.all().update(slug='')


class Migration(migrations.Migration):
    
    dependencies = [
        ('tasks', '0002_task_slug'),
    ]
    
    operations = [
        migrations.RunPython(
            populate_slugs,
            reverse_slugs,  # For rollback
        ),
    ]
```

### Data Migration Best Practices

```python
def populate_data(apps, schema_editor):
    """
    ✅ Best practices for data migrations
    """
    # ✅ Use apps.get_model() - not direct import!
    Task = apps.get_model('tasks', 'Task')
    
    # ❌ DON'T DO THIS
    # from apps.tasks.models import Task  # May have different schema!
    
    # ✅ Batch processing for large datasets
    batch_size = 1000
    tasks = Task.objects.filter(slug__isnull=True)
    
    for i in range(0, tasks.count(), batch_size):
        batch = tasks[i:i + batch_size]
        for task in batch:
            task.slug = slugify(task.title)
        Task.objects.bulk_update(batch, ['slug'])
```

### Complex Data Migration

```python
# Migrate data between apps
def migrate_user_profiles(apps, schema_editor):
    OldProfile = apps.get_model('users', 'Profile')
    NewProfile = apps.get_model('profiles', 'UserProfile')
    
    profiles_to_create = []
    
    for old in OldProfile.objects.all():
        profiles_to_create.append(
            NewProfile(
                user_id=old.user_id,
                bio=old.bio,
                avatar=old.avatar,
            )
        )
    
    NewProfile.objects.bulk_create(profiles_to_create)
```

---

## 4️⃣ SENIOR LEVEL - Advanced Strategies

### Squash Migrations

```bash
# Combine multiple migrations into one
python manage.py squashmigrations tasks 0001 0010
# Creates: 0001_squashed_0010.py

# After all servers have applied the squashed migration:
# 1. Delete old migration files (0001-0010)
# 2. Remove 'replaces' from squashed migration
```

### Migration Dependencies

```python
class Migration(migrations.Migration):
    
    dependencies = [
        # Depend on other app's migration
        ('auth', '0012_alter_user_first_name_max_length'),
        
        # Depend on same app's migration
        ('tasks', '0005_add_category'),
        
        # Depend on swappable model (User)
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
```

### Run Migrations in Transaction

```python
class Migration(migrations.Migration):
    
    # Wrap all operations in a transaction
    atomic = True  # Default is True
    
    # Disable for large data migrations
    # atomic = False
    
    operations = [...]
```

### Fake Migrations

```bash
# Mark migration as applied WITHOUT running it
python manage.py migrate tasks 0005 --fake

# Useful when:
# - Database already has the changes
# - Fixing migration history
# - Syncing with existing database
```

### Zero Migration (Reset)

```bash
# Unapply all migrations for an app
python manage.py migrate tasks zero

# ⚠️ WARNING: This will DROP all tables for the app!
```

---

## 5️⃣ SENIOR LEVEL - Production Strategies

### Safe Schema Changes (Zero Downtime)

```python
# ❌ UNSAFE: Adding required field
title = models.CharField(max_length=200)  # No default!

# ✅ SAFE: 3-step migration
# Step 1: Add nullable field
title = models.CharField(max_length=200, null=True)

# Step 2: Data migration - populate field
# (Deploy and run)

# Step 3: Make field required
title = models.CharField(max_length=200, null=False, default='')
```

### Large Table Migrations

```python
# For tables with millions of rows

# apps/tasks/migrations/0010_add_index.py
from django.db import migrations


class Migration(migrations.Migration):
    
    atomic = False  # Don't use transaction (for large tables)
    
    operations = [
        # Create index CONCURRENTLY (PostgreSQL)
        migrations.RunSQL(
            sql='CREATE INDEX CONCURRENTLY idx_task_status ON tasks_task(status)',
            reverse_sql='DROP INDEX CONCURRENTLY idx_task_status',
        ),
    ]
```

### Backward Compatible Migrations

```python
# Safe deployment strategy:
#
# 1. New code must work with OLD schema
# 2. Deploy new code
# 3. Run migrations
# 4. New code uses NEW schema

# Example: Renaming a column
# 
# Migration 1: Add new column, keep old
# Migration 2: Copy data from old to new
# Migration 3: Deploy code that uses new column
# Migration 4: Remove old column (after all servers updated)
```

### Migration Locking

```python
# Prevent concurrent migrations
# config/settings/production.py

DATABASES = {
    'default': {
        # ...
        'OPTIONS': {
            'lock_timeout': 10000,  # 10 seconds
        }
    }
}
```

---

## 6️⃣ EXPERT LEVEL - Custom Operations

### Custom Migration Operation

```python
# apps/core/operations.py
from django.db.migrations.operations.base import Operation


class CreateMaterializedView(Operation):
    """
    Custom operation to create materialized view
    """
    
    reversible = True
    
    def __init__(self, name, sql):
        self.name = name
        self.sql = sql
    
    def state_forwards(self, app_label, state):
        pass  # No model state changes
    
    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        schema_editor.execute(
            f"CREATE MATERIALIZED VIEW {self.name} AS {self.sql}"
        )
    
    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        schema_editor.execute(f"DROP MATERIALIZED VIEW {self.name}")
    
    def describe(self):
        return f"Create materialized view {self.name}"


# Usage in migration
from apps.core.operations import CreateMaterializedView

operations = [
    CreateMaterializedView(
        name='task_summary',
        sql='SELECT status, COUNT(*) FROM tasks_task GROUP BY status'
    ),
]
```

### Conditional Migrations

```python
from django.db import migrations


def check_condition(apps, schema_editor):
    """
    Only run if condition is met
    """
    connection = schema_editor.connection
    
    # Check if column exists
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'tasks_task' AND column_name = 'legacy_id'
        """)
        if cursor.fetchone():
            # Column exists, migrate data
            cursor.execute("""
                UPDATE tasks_task SET new_field = legacy_id
            """)


class Migration(migrations.Migration):
    operations = [
        migrations.RunPython(check_condition, migrations.RunPython.noop),
    ]
```

### Database-Specific Migrations

```python
from django.db import migrations


def forwards_postgresql(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute(
            "CREATE EXTENSION IF NOT EXISTS pg_trgm"
        )


def forwards_mysql(apps, schema_editor):
    if schema_editor.connection.vendor == 'mysql':
        schema_editor.execute(
            "ALTER TABLE tasks_task ENGINE=InnoDB"
        )


class Migration(migrations.Migration):
    operations = [
        migrations.RunPython(forwards_postgresql),
        migrations.RunPython(forwards_mysql),
    ]
```

---

## 7️⃣ Troubleshooting

### Common Issues

```bash
# Issue: Migrations out of sync
python manage.py migrate --fake-initial

# Issue: Conflicting migrations
python manage.py makemigrations --merge

# Issue: Migration file missing
python manage.py makemigrations --empty app_name

# Issue: Check migrations without applying
python manage.py migrate --plan

# Issue: See SQL without applying
python manage.py sqlmigrate tasks 0001
```

### Reset Migrations (Development Only!)

```bash
# ⚠️ DANGER: Only in development!

# 1. Delete all migration files (except __init__.py)
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete

# 2. Drop database
dropdb mydb && createdb mydb

# 3. Recreate migrations
python manage.py makemigrations
python manage.py migrate
```

### Debug Migration

```python
# Print SQL statements
python manage.py sqlmigrate tasks 0001

# Verbose migration
python manage.py migrate --verbosity 3

# Run with Python debugger
# Add this in migration file:
import pdb; pdb.set_trace()
```

---

## 📊 Quick Reference

### Commands

| Command | Description |
|---------|-------------|
| `makemigrations` | Create migration files |
| `migrate` | Apply migrations |
| `showmigrations` | List migration status |
| `sqlmigrate app 0001` | Show SQL for migration |
| `migrate app zero` | Unapply all migrations |
| `migrate --fake` | Mark as applied |
| `squashmigrations` | Combine migrations |

### Migration Operations

| Operation | Description |
|-----------|-------------|
| `CreateModel` | Create new table |
| `DeleteModel` | Delete table |
| `AddField` | Add column |
| `RemoveField` | Remove column |
| `AlterField` | Change column definition |
| `RenameField` | Rename column |
| `AddIndex` | Create index |
| `RemoveIndex` | Remove index |
| `RunPython` | Run Python code |
| `RunSQL` | Run raw SQL |

---

## 💡 Summary

| Level | Focus |
|-------|-------|
| **Junior** | makemigrations, migrate basics |
| **Mid** | Add/remove fields, naming |
| **Mid-Senior** | Data migrations, RunPython |
| **Senior** | Squash, production strategies |
| **Expert** | Custom operations, zero-downtime |

**Best Practices:**
- ✅ Always name migrations descriptively
- ✅ Test migrations on staging first
- ✅ Always provide reverse migration
- ✅ Use atomic=False for large data migrations
- ✅ Backup database before production migrations
- ❌ Never edit applied migrations
- ❌ Never delete applied migrations in production
- ❌ Don't mix schema and data changes
