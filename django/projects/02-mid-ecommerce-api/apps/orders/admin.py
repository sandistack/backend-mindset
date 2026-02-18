"""
Admin configuration for Orders app.
"""

from django.contrib import admin
from .models import Discount, Order, OrderItem


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


class OrderItemInline(admin.TabularInline):
    """Inline for order items."""
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'variant_name', 'price', 'quantity', 'subtotal']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin for Order model."""
    list_display = [
        'order_number', 'user', 'status', 'total', 
        'created_at', 'paid_at', 'shipped_at'
    ]
    list_filter = ['status', 'created_at', 'paid_at', 'shipped_at']
    search_fields = ['order_number', 'user__email', 'shipping_name', 'shipping_phone']
    readonly_fields = [
        'order_number', 'subtotal', 'discount_amount', 'total',
        'created_at', 'updated_at', 'paid_at', 'shipped_at', 
        'completed_at', 'cancelled_at'
    ]
    inlines = [OrderItemInline]
    list_per_page = 50
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Order Info', {
            'fields': ('order_number', 'user', 'status')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'discount', 'discount_amount', 'shipping_cost', 'total')
        }),
        ('Shipping Info', {
            'fields': (
                'shipping_name', 'shipping_phone', 'shipping_address',
                'shipping_city', 'shipping_postal_code', 'tracking_number'
            )
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 'updated_at', 'paid_at', 
                'shipped_at', 'completed_at', 'cancelled_at'
            )
        }),
    )
    
    def has_add_permission(self, request):
        """Disable manual order creation."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable order deletion."""
        return False
