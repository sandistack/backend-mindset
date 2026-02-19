"""
Document models for collaboration.
"""

from django.db import models
from django.conf import settings
from apps.core.models import SoftDeleteModel
from apps.workspaces.models import Workspace


class Document(SoftDeleteModel):
    """
    Collaborative document.
    """
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    version = models.IntegerField(default=1)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_documents'
    )
    
    class Meta:
        db_table = 'documents'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
