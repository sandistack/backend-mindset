"""
Serializers for Cart.
"""

from rest_framework import serializers
from .models import Cart, CartItem
from apps.products.serializers import ProductVariantSerializer
from apps.orders.models import Discount


class CartItemSerializer(serializers.ModelSerializer):
    """Serializer for CartItem."""
    
    variant = ProductVariantSerializer(read_only=True)
    subtotal = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        read_only=True
    )
    is_available = serializers.BooleanField(read_only=True)
    product_name = serializers.CharField(
        source='variant.product.name', 
        read_only=True
    )
    
    class Meta:
        model = CartItem
        fields = [
            'id', 'variant', 'product_name', 'quantity', 
            'subtotal', 'is_available', 'added_at'
        ]


class DiscountSerializer(serializers.ModelSerializer):
    """Serializer for Discount code."""
    
    class Meta:
        model = Discount
        fields = ['id', 'code', 'type', 'value']


class CartSerializer(serializers.ModelSerializer):
    """Serializer for Cart with all items."""
    
    items = CartItemSerializer(many=True, read_only=True)
    items_count = serializers.IntegerField(read_only=True)
    subtotal = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        read_only=True
    )
    discount_amount = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        read_only=True
    )
    total = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        read_only=True
    )
    discount_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = [
            'id', 'items', 'items_count', 'subtotal', 
            'discount_info', 'discount_amount', 'total', 
            'created_at', 'updated_at'
        ]
    
    def get_discount_info(self, obj):
        """Get discount information if applied."""
        if obj.discount:
            return DiscountSerializer(obj.discount).data
        return None


# ============================================
# INPUT SERIALIZERS
# ============================================

class AddToCartSerializer(serializers.Serializer):
    """Serializer for adding item to cart."""
    
    variant_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, default=1)


class UpdateCartItemSerializer(serializers.Serializer):
    """Serializer for updating cart item quantity."""
    
    quantity = serializers.IntegerField(min_value=0)


class ApplyDiscountSerializer(serializers.Serializer):
    """Serializer for applying discount code."""
    
    code = serializers.CharField(max_length=50)
