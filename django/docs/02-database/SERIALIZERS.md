# 🔄 SERIALIZERS - Django REST Framework (Junior → Senior)

Dokumentasi lengkap tentang DRF Serializers.

---

## 🎯 Apa itu Serializer?

**Serializer** = Jembatan antara Database (Model) dan API (JSON).

```
Database (Model)    ←→    Serializer    ←→    JSON (API)
   ↓                         ↓                      ↓
Python Object          Validation            dict/JSON
```

**Fungsi:**
1. **Serialization:** Model → JSON (output)
2. **Deserialization:** JSON → Model (input)
3. **Validation:** Check input validity

---

## 1️⃣ JUNIOR LEVEL - ModelSerializer

### Basic ModelSerializer

```python
# apps/tasks/serializers.py
from rest_framework import serializers
from .models import Task

class TaskSerializer(serializers.ModelSerializer):
    """
    Auto-generate fields from model
    """
    
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'status', 'priority', 'created_at']
        # Or: fields = '__all__'  # All fields
        # Or: exclude = ['user']  # All except user
```

### Usage in Views

```python
# Serialize (Model → JSON)
task = Task.objects.get(pk=1)
serializer = TaskSerializer(task)
print(serializer.data)  # OrderedDict (like dict)

# Serialize multiple
tasks = Task.objects.all()
serializer = TaskSerializer(tasks, many=True)
print(serializer.data)  # List of dicts

# Deserialize (JSON → Model)
data = {'title': 'New Task', 'status': 'TODO'}
serializer = TaskSerializer(data=data)

if serializer.is_valid():
    task = serializer.save()  # Create Task instance
else:
    print(serializer.errors)  # Validation errors
```

---

## 2️⃣ MID LEVEL - Field-Level Validation

### Custom Validation Methods

```python
class TaskSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'status', 'priority', 'due_date']
    
    def validate_title(self, value):
        """
        Field-level validation: validate_<field_name>
        """
        # Title min length
        if len(value) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters")
        
        # Title max length
        if len(value) > 255:
            raise serializers.ValidationError("Title too long (max 255 characters)")
        
        # No profanity (example)
        bad_words = ['spam', 'test123']
        if any(word in value.lower() for word in bad_words):
            raise serializers.ValidationError("Title contains inappropriate words")
        
        return value.strip()  # Sanitize: remove whitespace
    
    def validate_status(self, value):
        """Validate status"""
        allowed_statuses = ['TODO', 'IN_PROGRESS', 'DONE']
        
        if value not in allowed_statuses:
            raise serializers.ValidationError(
                f"Invalid status. Choose from: {', '.join(allowed_statuses)}"
            )
        
        return value
    
    def validate_due_date(self, value):
        """Validate due date not in past"""
        from django.utils import timezone
        
        if value and value < timezone.now():
            raise serializers.ValidationError("Due date cannot be in the past")
        
        return value
```

---

## 3️⃣ MID-SENIOR LEVEL - Object-Level Validation

### Cross-Field Validation

```python
class TaskSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Task
        fields = '__all__'
    
    def validate(self, attrs):
        """
        Object-level validation: validate entire object
        """
        
        # Example 1: Status + description logic
        if attrs.get('status') == 'DONE' and not attrs.get('description'):
            raise serializers.ValidationError(
                "Completed tasks must have a description"
            )
        
        # Example 2: Priority + due_date logic
        if attrs.get('priority') == 'HIGH' and not attrs.get('due_date'):
            raise serializers.ValidationError({
                "due_date": "High priority tasks must have a due date"
            })
        
        # Example 3: Check duplicate title for user
        user = self.context.get('request').user
        title = attrs.get('title')
        
        # Skip check on update (self.instance exists)
        if not self.instance:
            if Task.objects.filter(user=user, title__iexact=title).exists():
                raise serializers.ValidationError({
                    "title": "You already have a task with this title"
                })
        
        return attrs
```

---

## 4️⃣ SENIOR LEVEL - Read-Only & Write-Only Fields

### Separate Read/Write Fields

```python
class TaskSerializer(serializers.ModelSerializer):
    # Write-only fields (input only)
    password = serializers.CharField(write_only=True)
    
    # Read-only fields (output only)
    id = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    
    # Computed fields (read-only)
    days_until_due = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 
            'created_at', 'days_until_due'
        ]
        read_only_fields = ['id', 'created_at']  # Alternative way
    
    def get_days_until_due(self, obj):
        """SerializerMethodField: get_<field_name>"""
        if obj.due_date:
            from django.utils import timezone
            delta = obj.due_date - timezone.now()
            return delta.days
        return None
```

---

## 5️⃣ SENIOR LEVEL - Nested Serializers

### One-to-Many Relationship

```python
# apps/tasks/models.py
class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


# Serializers
class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'text', 'created_at']


class TaskDetailSerializer(serializers.ModelSerializer):
    """
    Task with nested comments
    """
    comments = CommentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'comments']


# Output
{
    "id": 1,
    "title": "Task 1",
    "description": "Description",
    "comments": [
        {"id": 1, "text": "Comment 1", "created_at": "2026-01-31T10:00:00Z"},
        {"id": 2, "text": "Comment 2", "created_at": "2026-01-31T11:00:00Z"}
    ]
}
```

### Foreign Key Representation

```python
class TaskSerializer(serializers.ModelSerializer):
    # Option 1: Show only ID (default)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    
    # Option 2: Show string representation
    user = serializers.StringRelatedField()
    
    # Option 3: Nested serializer (full object)
    user = UserSerializer(read_only=True)
    
    # Option 4: Custom field
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = Task
        fields = ['id', 'title', 'user', 'user_email']
```

---

## 6️⃣ EXPERT LEVEL - Dynamic Serializers

### Dynamic Fields

```python
class DynamicFieldsSerializer(serializers.ModelSerializer):
    """
    Allow client to specify fields
    
    Usage:
        GET /api/tasks/?fields=id,title,status
    """
    
    def __init__(self, *args, **kwargs):
        # Get fields from context
        fields = kwargs.pop('fields', None)
        
        # Instantiate serializer
        super().__init__(*args, **kwargs)
        
        if fields:
            # Drop fields not specified
            allowed = set(fields.split(','))
            existing = set(self.fields.keys())
            
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class TaskSerializer(DynamicFieldsSerializer):
    class Meta:
        model = Task
        fields = '__all__'


# View
def get(self, request):
    tasks = Task.objects.all()
    fields = request.query_params.get('fields')
    
    serializer = TaskSerializer(
        tasks,
        many=True,
        fields=fields  # Pass to context
    )
    
    return Response(serializer.data)
```

### Conditional Fields Based on Context

```python
class TaskSerializer(serializers.ModelSerializer):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get user from context
        request = self.context.get('request')
        
        if request and request.user:
            # Show extra fields for admin
            if not request.user.groups.filter(name='Admin').exists():
                # Remove sensitive fields for non-admin
                self.fields.pop('internal_notes', None)


class TaskDetailSerializer(serializers.ModelSerializer):
    # Conditional include
    internal_notes = serializers.CharField(required=False)
    
    class Meta:
        model = Task
        fields = '__all__'
```

---

## 7️⃣ EXPERT LEVEL - Writable Nested Serializers

### Create with Nested Objects

```python
class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['text']


class TaskCreateSerializer(serializers.ModelSerializer):
    """
    Create task with comments in one request
    """
    comments = CommentSerializer(many=True, required=False)
    
    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'comments']
    
    def create(self, validated_data):
        """Override create to handle nested"""
        # Pop nested data
        comments_data = validated_data.pop('comments', [])
        
        # Create task
        task = Task.objects.create(**validated_data)
        
        # Create comments
        for comment_data in comments_data:
            Comment.objects.create(task=task, **comment_data)
        
        return task
    
    def update(self, instance, validated_data):
        """Override update to handle nested"""
        # Pop nested data
        comments_data = validated_data.pop('comments', None)
        
        # Update task fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update comments if provided
        if comments_data is not None:
            # Delete old comments
            instance.comments.all().delete()
            
            # Create new comments
            for comment_data in comments_data:
                Comment.objects.create(task=instance, **comment_data)
        
        return instance


# Request body
{
    "title": "Task with comments",
    "description": "Description",
    "status": "TODO",
    "comments": [
        {"text": "First comment"},
        {"text": "Second comment"}
    ]
}
```

---

## 8️⃣ EXPERT LEVEL - Custom Serializer Fields

### Custom Field

```python
class Base64ImageField(serializers.ImageField):
    """
    Custom field for base64 image upload
    """
    
    def to_internal_value(self, data):
        import base64
        from django.core.files.base import ContentFile
        
        # Check if base64 string
        if isinstance(data, str) and data.startswith('data:image'):
            # Extract format and base64 data
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            
            # Decode base64
            data = ContentFile(base64.b64decode(imgstr), name=f'temp.{ext}')
        
        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'avatar']
```

---

## 📊 Serializer vs Form

| Feature | Serializer (DRF) | Form (Django) |
|---------|-----------------|---------------|
| **Use Case** | REST API (JSON) | HTML forms |
| **Output** | JSON | HTML |
| **Validation** | Yes | Yes |
| **Nested** | Easy | Hard |
| **Many-to-many** | Easy | Manual |

---

## 🎯 Best Practices

### 1. Separate Read/Write Serializers

```python
# For listing (minimal fields)
class TaskListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'status']


# For detail (all fields + nested)
class TaskDetailSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Task
        fields = '__all__'


# For create/update (write operations)
class TaskWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'priority']
```

### 2. Use SerializerMethodField for Computed Values

```python
class TaskSerializer(serializers.ModelSerializer):
    is_overdue = serializers.SerializerMethodField()
    
    def get_is_overdue(self, obj):
        from django.utils import timezone
        if obj.due_date:
            return obj.due_date < timezone.now() and obj.status != 'DONE'
        return False
```

### 3. Validate in Serializer, Not View

```python
# ❌ Bad: Validation in view
def post(self, request):
    if len(request.data['title']) < 3:
        return Response({'error': 'Title too short'}, status=400)

# ✅ Good: Validation in serializer
class TaskSerializer(serializers.ModelSerializer):
    def validate_title(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Title too short")
        return value
```

### 4. Use Context

```python
# Pass request to serializer
serializer = TaskSerializer(
    data=request.data,
    context={'request': request}  # ← Important!
)

# Access in serializer
def validate(self, attrs):
    user = self.context['request'].user
    # Use user for validation
    ...
```

---

## 💡 Summary

| Level | Technique |
|-------|-----------|
| **Junior** | Basic ModelSerializer |
| **Mid** | Field-level validation |
| **Mid-Senior** | Object-level validation, read_only fields |
| **Senior** | Nested serializers, SerializerMethodField |
| **Expert** | Dynamic fields, writable nested, custom fields |

**Key Points:**
- ✅ Serializers = validation + transformation
- ✅ Use separate serializers for read/write
- ✅ Validate in serializer, not view
- ✅ Pass context (request) to serializer
- ✅ Use SerializerMethodField for computed values
