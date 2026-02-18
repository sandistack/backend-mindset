from rest_framework import serializers
from django.utils import timezone
from .models import Category, Task


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for Category model
    """
    class Meta:
        model = Category
        fields = ['id', 'name', 'color', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def validate_name(self, value):
        """
        Check that category name is unique for this user
        """
        user = self.context['request'].user
        
        # Check if we're updating an existing category
        if self.instance:
            # Exclude current instance from uniqueness check
            if Category.objects.filter(name=value, user=user).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(
                    f"You already have a category named '{value}'."
                )
        else:
            # Creating new category
            if Category.objects.filter(name=value, user=user).exists():
                raise serializers.ValidationError(
                    f"You already have a category named '{value}'."
                )
        
        return value
    
    def validate_color(self, value):
        """
        Validate hex color format
        """
        if not value.startswith('#') or len(value) != 7:
            raise serializers.ValidationError(
                "Color must be in hex format (e.g., #FF0000)"
            )
        return value


class CategorySimpleSerializer(serializers.ModelSerializer):
    """
    Simple Category serializer for nested representation
    """
    class Meta:
        model = Category
        fields = ['id', 'name', 'color']


class TaskSerializer(serializers.ModelSerializer):
    """
    Task serializer for reading/listing tasks
    Includes nested category information
    """
    category = CategorySimpleSerializer(read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'priority',
            'status',
            'due_date',
            'completed_at',
            'category',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'completed_at', 'created_at', 'updated_at']


class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Task serializer for creating and updating tasks
    """
    
    class Meta:
        model = Task
        fields = [
            'title',
            'description',
            'priority',
            'status',
            'due_date',
            'category'
        ]
    
    def validate_due_date(self, value):
        """
        Validate that due_date is not in the past (only for creation)
        """
        if value and not self.instance:  # Only check on creation
            if value < timezone.now():
                raise serializers.ValidationError(
                    "Due date cannot be in the past."
                )
        return value
    
    def validate_category(self, value):
        """
        Validate that category belongs to the same user
        """
        if value:
            user = self.context['request'].user
            if value.user != user:
                raise serializers.ValidationError(
                    "You can only assign tasks to your own categories."
                )
        return value
    
    def validate(self, attrs):
        """
        Additional validation
        """
        # Auto-set completed_at when status changes to 'done'
        if attrs.get('status') == 'done' and (not self.instance or self.instance.status != 'done'):
            # Status is being changed to done
            pass  # We'll handle this in the view
        
        return attrs


class TaskDetailSerializer(serializers.ModelSerializer):
    """
    Detailed task serializer with all information
    """
    category = CategorySimpleSerializer(read_only=True)
    user = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id',
            'user',
            'title',
            'description',
            'priority',
            'status',
            'due_date',
            'completed_at',
            'category',
            'is_deleted',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'user', 'completed_at', 'created_at', 'updated_at', 'is_deleted']
    
    def get_user(self, obj):
        return {
            'id': obj.user.id,
            'email': obj.user.email,
            'name': obj.user.name
        }
