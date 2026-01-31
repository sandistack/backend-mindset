from django.contrib import admin
from django.utils.html import format_html
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin untuk audit logs dengan UI yang bagus"""
    
    list_display = [
        'timestamp',
        'user',
        'action_badge',
        'feature',
        'description_short',
        'ip_address',
        'status_badge'
    ]
    
    list_filter = ['action', 'feature', 'status', 'timestamp']
    search_fields = ['user__email', 'user__username', 'description', 'feature']
    readonly_fields = [
        'timestamp', 'user', 'action', 'feature', 
        'description', 'ip_address', 'status'
    ]
    date_hierarchy = 'timestamp'
    
    def action_badge(self, obj):
        """Colored badge untuk action"""
        colors = {
            'CREATE': 'green',
            'UPDATE': 'orange',
            'DELETE': 'red',
            'ERROR': 'darkred',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            colors.get(obj.action, 'gray'),
            obj.get_action_display()
        )
    action_badge.short_description = 'Action'
    
    def status_badge(self, obj):
        """Colored badge untuk status"""
        if obj.status == 'SUCCESS':
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Success</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">✗ Failed</span>'
        )
    status_badge.short_description = 'Status'
    
    def description_short(self, obj):
        """Truncate description"""
        if len(obj.description) > 50:
            return obj.description[:50] + '...'
        return obj.description
    description_short.short_description = 'Description'
    
    def has_add_permission(self, request):
        """Disable manual add"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Only superuser can delete"""
        return request.user.is_superuser