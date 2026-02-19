"""
Chat channel models.
"""

from django.db import models
from django.conf import settings
from apps.core.models import BaseModel
from apps.workspaces.models import Workspace


class Channel(BaseModel):
    """
    Chat channel (like Slack channels).
    """
    TYPE_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
    ]
    
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='chat_channels'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='public')
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='joined_channels',
        blank=True
    )
    
    class Meta:
        db_table = 'chat_channels'
        ordering = ['name']
    
    def __str__(self):
        return f"#{self.name}"


class Message(BaseModel):
    """
    Chat message.
    """
    channel = models.ForeignKey(
        Channel,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    content = models.TextField()
    attachments = models.JSONField(default=list, blank=True)
    
    class Meta:
        db_table = 'chat_messages'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.user.email}: {self.content[:50]}"
