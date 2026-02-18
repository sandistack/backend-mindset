"""
Admin configuration for Orders app.
"""

from django.contrib import admin
from .models import Discount


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    """Admin for Discount model."""
    list_display = [
        'code', 'type', 'value', 'min_order_amount', 
        'valid_from', 'valid_until', 'used_count', 'usage_limit', 'is_active'
    ]
    list_filter = ['type', 'is_active', 'valid_from', 'valid_until']
    search_fields = ['code']
    readonly_fields = ['used_count', 'created_at', 'updated_at']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Discount Info', {
            'fields': ('code', 'type', 'value')
        }),
        ('Constraints', {
            'fields': ('min_order_amount', 'max_discount_amount')
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_until', 'is_active')
        }),
        ('Usage', {
            'fields': ('usage_limit', 'used_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
