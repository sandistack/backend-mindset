from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model"""
    
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id',
            'order',
            'order_number',
            'provider',
            'provider_transaction_id',
            'amount',
            'status',
            'method',
            'payment_url',
            'created_at',
            'updated_at',
            'paid_at',
            'expired_at',
            'is_expired'
        ]
        read_only_fields = [
            'id',
            'provider_transaction_id',
            'status',
            'method',
            'payment_url',
            'created_at',
            'updated_at',
            'paid_at',
            'expired_at'
        ]


class CreatePaymentSerializer(serializers.Serializer):
    """Serializer for creating payment"""
    
    provider = serializers.ChoiceField(
        choices=['midtrans', 'stripe'],
        default='midtrans',
        help_text="Payment provider to use"
    )


class PaymentStatusSerializer(serializers.Serializer):
    """Serializer for payment status response"""
    
    status = serializers.CharField()
    provider = serializers.CharField(required=False)
    method = serializers.CharField(required=False)
    amount = serializers.CharField(required=False)
    paid_at = serializers.DateTimeField(required=False, allow_null=True)
    expired_at = serializers.DateTimeField(required=False, allow_null=True)
    payment_url = serializers.URLField(required=False, allow_null=True)
    is_expired = serializers.BooleanField(required=False)
    message = serializers.CharField(required=False)
