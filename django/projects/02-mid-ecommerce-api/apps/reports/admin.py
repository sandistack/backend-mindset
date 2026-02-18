"""
Admin configuration for Reports app.
"""

from django.contrib import admin
from .models import ExportJob


@admin.register(ExportJob)
class ExportJobAdmin(admin.ModelAdmin):
    """Admin for ExportJob model."""
    list_display = [
        'id', 'user', 'export_type', 'format', 'status',
        'created_at', 'completed_at'
    ]
    list_filter = ['status', 'export_type', 'format', 'created_at']
    search_fields = ['user__email', 'id']
    readonly_fields = [
        'created_at', 'started_at', 'completed_at',
        'error_message', 'file'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Job Info', {
            'fields': ('user', 'export_type', 'format', 'status')
        }),
        ('Filters', {
            'fields': ('filters',)
        }),
        ('Result', {
            'fields': ('file', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'started_at', 'completed_at')
        }),
    )
    
    def has_add_permission(self, request):
        """Disable manual creation."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Only allow deletion of completed/failed jobs."""
        if obj and obj.status in ['pending', 'processing']:
            return False
        return True
