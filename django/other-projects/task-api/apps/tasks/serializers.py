from rest_framework import serializers
from .models import Task
from apps.authentication.serializers import UserSerializer

class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer untuk Task CRUD
    
    Readable: Clear field definitions
    Secure: Input validation
    Maintainable: Easy to extend
    """
    
    # Nested user info (read-only)
    user = UserSerializer(read_only=True)
    
    # Display choices (read-only)
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    priority_display = serializers.CharField(
        source='get_priority_display',
        read_only=True
    )
    
    class Meta:
        model = Task
        fields = (
            'id',
            'user',
            'title',
            'description',
            'status',
            'status_display',
            'priority',
            'priority_display',
            'due_date',
            'created_at',
            'updated_at'
        )
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')
    
    def validate_title(self, value):
        """
        Secure: Validate title format
        """
        if not value or len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Title must be at least 3 characters long."
            )
        
        # Sanitize: Remove leading/trailing whitespace
        return value.strip()
    
    def validate_description(self, value):
        """
        Secure: Sanitize description
        """
        if value:
            return value.strip()
        return value
    
    def validate_status(self, value):
        """
        Predictable: Validate status choices
        """
        valid_statuses = ['TODO', 'IN_PROGRESS', 'DONE']
        if value not in valid_statuses:
            raise serializers.ValidationError(
                f"Status must be one of: {', '.join(valid_statuses)}"
            )
        return value
    
    def validate_priority(self, value):
        """
        Predictable: Validate priority choices
        """
        valid_priorities = ['LOW', 'MEDIUM', 'HIGH']
        if value not in valid_priorities:
            raise serializers.ValidationError(
                f"Priority must be one of: {', '.join(valid_priorities)}"
            )
        return value


class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer untuk Create/Update (simple, tanpa nested user)
    
    Maintainable: Separate create/update dari display
    """
    
    class Meta:
        model = Task
        fields = (
            'title',
            'description',
            'status',
            'priority',
            'due_date'
        )
    
    def validate_title(self, value):
        if not value or len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Title must be at least 3 characters long."
            )
        return value.strip()