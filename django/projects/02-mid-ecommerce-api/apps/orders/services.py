"""
Order business logic service.
"""

from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Order, OrderItem
from .tasks import (
    send_order_confirmation_email,
    send_payment_confirmation_email,
    send_shipping_notification_email,
)


class OrderService:
    """Service class for order operations."""
    
    @staticmethod
    @transaction.atomic
    def create_from_cart(user, cart, shipping_data):
        """Create order from cart and reserve stock."""
        
        # Validate cart not empty
        if not cart.items.exists():
            raise ValidationError("Cart is empty")
        
        # Validate all items available
        for item in cart.items.select_related('variant').all():
            if not item.is_available:
                raise ValidationError(f"{item.variant.name} is not available")
        
        # Calculate totals
        shipping_cost = shipping_data.get('shipping_cost', 0)
        total = cart.subtotal - cart.discount_amount + shipping_cost
        
        # Create order
        order = Order.objects.create(
            user=user,
            order_number=Order.generate_order_number(),
            subtotal=cart.subtotal,
            discount=cart.discount,
            discount_amount=cart.discount_amount,
            shipping_cost=shipping_cost,
            total=total,
            shipping_name=shipping_data['name'],
            shipping_phone=shipping_data['phone'],
            shipping_address=shipping_data['address'],
            shipping_city=shipping_data['city'],
            shipping_postal_code=shipping_data['postal_code'],
            notes=shipping_data.get('notes', '')
        )
        
        # Create order items & reserve stock
        for item in cart.items.select_related('variant__product').all():
            OrderItem.objects.create(
                order=order,
                variant=item.variant,
                product_name=item.variant.product.name,
                variant_name=item.variant.name,
                price=item.variant.price,
                quantity=item.quantity,
                subtotal=item.subtotal
            )
            
            # Reserve stock
            item.variant.reserve_stock(item.quantity)
        
        # Increment discount usage
        if cart.discount:
            cart.discount.increment_usage()
        
        # Clear cart
        cart.items.all().delete()
        cart.discount = None
        cart.save()
        
        # Send order confirmation email (async)
        send_order_confirmation_email.delay(order.id)
        
        return order
    
    @staticmethod
    @transaction.atomic
    def cancel_order(order, reason=""):
        """Cancel order and release stock."""
        if not order.can_cancel():
            raise ValidationError(f"Order with status '{order.status}' cannot be cancelled")
        
        # Release stock
        for item in order.items.select_related('variant').all():
            item.variant.release_stock(item.quantity)
        
        order.cancel(reason)
        
        return order
    
    @staticmethod
    def update_status(order, new_status, **kwargs):
        """Update order status with validation."""
        
        # Define valid status transitions
        valid_transitions = {
            'pending': ['paid', 'cancelled'],
            'paid': ['processing', 'cancelled'],
            'processing': ['shipped', 'cancelled'],
            'shipped': ['delivered'],
            'delivered': ['completed'],
        }
        
        if new_status not in valid_transitions.get(order.status, []):
            raise ValidationError(
                f"Cannot transition from '{order.status}' to '{new_status}'"
            )
        
        # Update status with appropriate timestamps
        if new_status == 'paid':
            order.mark_paid()
            # Send payment confirmation email
            send_payment_confirmation_email.delay(order.id)
        elif new_status == 'shipped':
            tracking_number = kwargs.get('tracking_number', '')
            order.mark_shipped(tracking_number)
            # Send shipping notification email
            send_shipping_notification_email.delay(order.id, tracking_number)
        elif new_status == 'completed':
            order.mark_completed()
        elif new_status == 'cancelled':
            reason = kwargs.get('reason', '')
            OrderService.cancel_order(order, reason)
        else:
            order.status = new_status
            order.save(update_fields=['status', 'updated_at'])
        
        return order
