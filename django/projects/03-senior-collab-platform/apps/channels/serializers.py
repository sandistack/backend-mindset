"""
Serializers for chat channels and messages.
"""

from rest_framework import serializers
from .models import Channel, Message


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for Message model."""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'channel', 'user', 'user_name', 'content', 'attachments', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']
