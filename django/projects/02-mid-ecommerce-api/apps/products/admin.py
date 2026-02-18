"""
Admin configuration for Products app.
"""

from django.contrib import admin
from .models import Category, Product, ProductVariant, ProductImage


# ============================================
# INLINE ADMINS
# ============================================

class ProductVariantInline(admin.TabularInline):
    """Inline admin for ProductVariant."""
    model = ProductVariant
    extra = 1
    fields = ['sku', 'name', 'size', 'color', 'price', 'stock', 'is_active']


class ProductImageInline(admin.TabularInline):
    """Inline admin for ProductImage."""
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'is_primary', 'order']


# ============================================
# MODEL ADMINS
# ============================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin for Category model."""
    list_display = ['name', 'slug', 'parent', 'is_active', 'order', 'created_at']
    list_filter = ['is_active', 'parent', 'created_at']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']
    list_editable = ['is_active', 'order']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin for Product model with inline variants and images."""
    list_display = ['name', 'slug', 'category', 'base_price', 'is_active', 'is_featured', 'created_at']
    list_filter = ['is_active', 'is_featured', 'category', 'created_at']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['-created_at']
    list_editable = ['is_active', 'is_featured']
    inlines = [ProductVariantInline, ProductImageInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'category', 'description')
        }),
        ('Pricing', {
            'fields': ('base_price',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured')
        }),
    )


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    """Admin for ProductVariant model."""
    list_display = ['product', 'name', 'sku', 'price', 'stock', 'is_active', 'created_at']
    list_filter = ['is_active', 'product__category', 'created_at']
    search_fields = ['sku', 'name', 'product__name']
    ordering = ['-created_at']
    list_editable = ['stock', 'is_active']
    
    fieldsets = (
        ('Product', {
            'fields': ('product',)
        }),
        ('Variant Details', {
            'fields': ('sku', 'name', 'size', 'color')
        }),
        ('Pricing & Inventory', {
            'fields': ('price', 'stock', 'weight')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    """Admin for ProductImage model."""
    list_display = ['product', 'alt_text', 'is_primary', 'order', 'created_at']
    list_filter = ['is_primary', 'created_at']
    search_fields = ['product__name', 'alt_text']
    ordering = ['product', 'order']
    list_editable = ['is_primary', 'order']
