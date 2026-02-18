"""
Reports models for background export jobs.
"""

from django.db import models
from django.conf import settings


class ExportJob(models.Model):
    """Background export job for large datasets."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    FORMAT_CHOICES = [
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ]
    
    TYPE_CHOICES = [
        ('sales', 'Sales Report'),
        ('products', 'Products Report'),
        ('orders', 'Orders Report'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='export_jobs'
    )
    export_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='excel')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Export file
    file = models.FileField(upload_to='exports/%Y/%m/', null=True, blank=True)
    
    # Error tracking
    error_message = models.TextField(blank=True)
    
    # Filters applied
    filters = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'export_jobs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.get_export_type_display()} - {self.status} ({self.created_at})"
