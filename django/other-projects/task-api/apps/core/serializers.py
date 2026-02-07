from rest_framework import serializers
from .models import AuditLog
from apps.authentication.serializers import UserSerializer

class AuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer untuk Audit Log (read-only)
    
    Secure: Read-only, can't be manipulated
    Readable: Display-friendly format
    """
    
    user = UserSerializer(read_only=True)
    action_display = serializers.CharField(
        source='get_action_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    
    class Meta:
        model = AuditLog
        fields = (
            'id',
            'timestamp',
            'user',
            'action',
            'action_display',
            'feature',
            'description',
            'ip_address',
            'status',
            'status_display'
        )
        read_only_fields = '__all__'