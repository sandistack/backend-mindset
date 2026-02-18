"""
Admin configuration for Cart app.
"""

from django.contrib import admin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    """Inline admin for CartItem."""
    model = CartItem
    extra = 0
    readonly_fields = ['subtotal', 'added_at']
    fields = ['variant', 'quantity', 'subtotal', 'added_at']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Admin for Cart model."""
    list_display = ['id', 'user', 'session_key', 'items_count', 'subtotal', 'total', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'session_key']
    readonly_fields = ['items_count', 'subtotal', 'discount_amount', 'total', 'created_at', 'updated_at']
    inlines = [CartItemInline]
    
    fieldsets = (
        ('Cart Owner', {
            'fields': ('user', 'session_key')
        }),
        ('Discount', {
            'fields': ('discount',)
        }),
        ('Totals', {
            'fields': ('items_count', 'subtotal', 'discount_amount', 'total')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """Admin for CartItem model."""
    list_display = ['id', 'cart', 'variant', 'quantity', 'subtotal', 'is_available', 'added_at']
    list_filter = ['added_at']
    search_fields = ['cart__user__email', 'variant__product__name', 'variant__sku']
    readonly_fields = ['subtotal', 'is_available', 'added_at']
