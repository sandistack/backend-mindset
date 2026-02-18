"""
Order serializers.
"""

from rest_framework import serializers
from .models import Order, OrderItem


class ShippingDataSerializer(serializers.Serializer):
    """Shipping information for checkout."""
    name = serializers.CharField(max_length=100)
    phone = serializers.CharField(max_length=20)
    address = serializers.CharField()
    city = serializers.CharField(max_length=100)
    postal_code = serializers.CharField(max_length=10)
    shipping_cost = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0
    )
    notes = serializers.CharField(required=False, allow_blank=True)


class CheckoutSerializer(serializers.Serializer):
    """Checkout request serializer."""
    shipping = ShippingDataSerializer()


class OrderItemSerializer(serializers.ModelSerializer):
    """Order item serializer."""
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 
            'product_name', 
            'variant_name', 
            'price', 
            'quantity', 
            'subtotal'
        ]


class OrderListSerializer(serializers.ModelSerializer):
    """Order list serializer (simplified)."""
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 
            'order_number', 
            'status', 
            'total', 
            'items_count', 
            'created_at'
        ]
    
    def get_items_count(self, obj):
        return obj.items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    """Order detail serializer (full data)."""
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 
            'order_number', 
            'status',
            'status_display',
            'items',
            'subtotal', 
            'discount_amount', 
            'shipping_cost', 
            'total',
            'shipping_name', 
            'shipping_phone', 
            'shipping_address',
            'shipping_city', 
            'shipping_postal_code',
            'tracking_number',
            'notes', 
            'created_at', 
            'paid_at', 
            'shipped_at',
            'completed_at',
            'cancelled_at'
        ]
