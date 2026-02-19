"""
Notification models.
"""

from django.db import models
from django.conf import settings
from apps.core.models import BaseModel


class Notification(BaseModel):
    """
    User notification.
    """
    TYPE_CHOICES = [
        ('mention', 'Mention'),
        ('comment', 'Comment'),
        ('invite', 'Invite'),
        ('task', 'Task'),
        ('system', 'System'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.user.email}: {self.title}"
