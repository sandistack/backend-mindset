"""
Serializers for Product catalog.
"""

from rest_framework import serializers
from .models import Category, Product, ProductVariant, ProductImage


# ============================================
# CATEGORY SERIALIZERS
# ============================================

class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category with nested children."""
    
    children = serializers.SerializerMethodField()
    full_path = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'parent', 'description', 
            'image', 'full_path', 'children', 'product_count'
        ]
        read_only_fields = ['full_path', 'children', 'product_count']
    
    def get_children(self, obj):
        """Get active child categories."""
        children = obj.children.filter(is_active=True)
        return CategorySerializer(children, many=True, context=self.context).data
    
    def get_full_path(self, obj):
        """Get full category path."""
        return obj.get_full_path()
    
    def get_product_count(self, obj):
        """Count products in this category."""
        return obj.products.filter(is_active=True).count()


# ============================================
# PRODUCT IMAGE SERIALIZERS
# ============================================

class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer for Product Image."""
    
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_primary', 'order']


# ============================================
# PRODUCT VARIANT SERIALIZERS
# ============================================

class ProductVariantSerializer(serializers.ModelSerializer):
    """Serializer for Product Variant."""
    
    is_in_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'sku', 'name', 'size', 'color', 
            'price', 'stock', 'weight', 'is_active', 'is_in_stock'
        ]
    
    def get_is_in_stock(self, obj):
        """Check if variant is in stock."""
        return obj.is_in_stock()


# ============================================
# PRODUCT SERIALIZERS
# ============================================

class ProductListSerializer(serializers.ModelSerializer):
    """Serializer for Product list view (lighter data)."""
    
    category = CategorySerializer(read_only=True)
    primary_image = serializers.SerializerMethodField()
    price_range = serializers.SerializerMethodField()
    total_stock = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'category', 'base_price', 
            'price_range', 'primary_image', 'is_featured', 
            'is_in_stock', 'total_stock', 'created_at'
        ]
    
    def get_primary_image(self, obj):
        """Get primary image URL."""
        primary = obj.primary_image
        if primary and primary.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(primary.image.url)
            return primary.image.url
        return None
    
    def get_price_range(self, obj):
        """Get price range from variants."""
        return obj.price_range


class ProductDetailSerializer(serializers.ModelSerializer):
    """Serializer for Product detail view (full data)."""
    
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    price_range = serializers.SerializerMethodField()
    total_stock = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'category', 'category_id',
            'base_price', 'price_range', 'is_active', 'is_featured', 
            'is_in_stock', 'total_stock', 'variants', 'images', 
            'created_at', 'updated_at'
        ]
    
    def get_price_range(self, obj):
        """Get price range from variants."""
        return obj.price_range


# ============================================
# ADMIN SERIALIZERS (for creating products)
# ============================================

class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating products (Admin)."""
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'category',
            'base_price', 'is_active', 'is_featured'
        ]
    
    def validate_slug(self, value):
        """Validate slug uniqueness on update."""
        instance = self.instance
        if instance and Product.objects.exclude(pk=instance.pk).filter(slug=value).exists():
            raise serializers.ValidationError("Product with this slug already exists.")
        elif not instance and Product.objects.filter(slug=value).exists():
            raise serializers.ValidationError("Product with this slug already exists.")
        return value


class ProductVariantCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating variants (Admin)."""
    
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'product', 'sku', 'name', 'size', 'color',
            'price', 'stock', 'weight', 'is_active'
        ]
    
    def validate_sku(self, value):
        """Validate SKU uniqueness on update."""
        instance = self.instance
        if instance and ProductVariant.objects.exclude(pk=instance.pk).filter(sku=value).exists():
            raise serializers.ValidationError("Variant with this SKU already exists.")
        elif not instance and ProductVariant.objects.filter(sku=value).exists():
            raise serializers.ValidationError("Variant with this SKU already exists.")
        return value
