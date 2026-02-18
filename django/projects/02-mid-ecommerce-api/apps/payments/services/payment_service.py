from django.utils import timezone
from datetime import timedelta
from .midtrans_service import MidtransService
from .stripe_service import StripeService
from ..models import Payment
from apps.orders.models import Order
from apps.orders.services import OrderService


class PaymentService:
    """
    Payment service abstraction layer
    Handles payment creation and webhook notifications for multiple providers
    """
    
    def __init__(self, provider='midtrans'):
        """
        Initialize payment service with specified provider
        
        Args:
            provider: 'midtrans' or 'stripe'
        """
        self.provider = provider
        
        if provider == 'midtrans':
            self.gateway = MidtransService()
        elif provider == 'stripe':
            self.gateway = StripeService()
        else:
            raise ValueError(f"Unsupported payment provider: {provider}")
    
    def create_payment(self, order):
        """
        Initialize payment for an order
        
        Args:
            order: Order instance
            
        Returns:
            Payment instance
            
        Raises:
            ValueError: If order is not in pending status
            Exception: If payment creation fails
        """
        # Check if payment already exists
        if hasattr(order, 'payment'):
            if order.payment.status in ['pending', 'processing']:
                return order.payment
        
        # Validate order status
        if order.status != 'pending':
            raise ValueError("Order must be in pending status to create payment")
        
        # Create payment record
        payment = Payment.objects.create(
            order=order,
            provider=self.provider,
            amount=order.total,
            expired_at=timezone.now() + timedelta(hours=24)
        )
        
        # Create transaction with payment gateway
        try:
            if self.provider == 'midtrans':
                result = self.gateway.create_transaction(order)
                payment.payment_url = result['redirect_url']
                payment.raw_response = result
                
            elif self.provider == 'stripe':
                result = self.gateway.create_checkout_session(order)
                payment.payment_url = result['url']
                payment.provider_transaction_id = result['session_id']
                payment.raw_response = result
            
            payment.save()
            return payment
            
        except Exception as e:
            payment.status = 'failed'
            payment.raw_response = {'error': str(e)}
            payment.save()
            raise Exception(f"Failed to create payment: {str(e)}")
    
    def handle_notification(self, notification_data):
        """
        Handle payment notification from gateway
        
        Args:
            notification_data: Notification payload
            
        Returns:
            Payment instance
            
        Raises:
            ValueError: If notification is invalid
        """
        if self.provider == 'midtrans':
            return self._handle_midtrans_notification(notification_data)
        elif self.provider == 'stripe':
            return self._handle_stripe_notification(notification_data)
    
    def _handle_midtrans_notification(self, data):
        """
        Handle Midtrans notification
        
        Args:
            data: Midtrans notification data
            
        Returns:
            Payment instance
        """
        # Verify signature
        if not self.gateway.verify_notification(data):
            raise ValueError("Invalid Midtrans signature")
        
        order_id = data['order_id']
        transaction_status = data['transaction_status']
        fraud_status = data.get('fraud_status', 'accept')
        
        # Get order and payment
        try:
            order = Order.objects.get(order_number=order_id)
            payment = order.payment
        except Order.DoesNotExist:
            raise ValueError(f"Order {order_id} not found")
        
        # Update payment
        payment.provider_transaction_id = data.get('transaction_id', '')
        payment.method = data.get('payment_type', '')
        payment.raw_response = data
        
        # Status mapping
        if transaction_status == 'capture':
            if fraud_status == 'accept':
                payment.status = 'success'
                payment.paid_at = timezone.now()
                OrderService.update_status(order, 'paid')
        
        elif transaction_status == 'settlement':
            payment.status = 'success'
            payment.paid_at = timezone.now()
            OrderService.update_status(order, 'paid')
        
        elif transaction_status == 'pending':
            payment.status = 'processing'
        
        elif transaction_status in ['deny', 'cancel', 'expire']:
            payment.status = 'failed' if transaction_status != 'expire' else 'expired'
            # Cancel order and release stock
            OrderService.cancel_order(order, f"Payment {transaction_status}")
        
        elif transaction_status == 'refund':
            payment.status = 'refunded'
        
        payment.save()
        return payment
    
    def _handle_stripe_notification(self, event):
        """
        Handle Stripe notification
        
        Args:
            event: Stripe event object (already verified)
            
        Returns:
            Payment instance
        """
        event_type = event['type']
        
        # Handle checkout session completed
        if event_type == 'checkout.session.completed':
            session = event['data']['object']
            order_id = session['metadata'].get('order_id')
            
            try:
                order = Order.objects.get(id=order_id)
                payment = order.payment
            except Order.DoesNotExist:
                raise ValueError(f"Order {order_id} not found")
            
            # Update payment
            payment.provider_transaction_id = session['payment_intent']
            payment.status = 'success'
            payment.paid_at = timezone.now()
            payment.method = 'card'
            payment.raw_response = session
            payment.save()
            
            # Update order status
            OrderService.update_status(order, 'paid')
            
            return payment
        
        # Handle payment intent succeeded
        elif event_type == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            order_id = payment_intent['metadata'].get('order_id')
            
            try:
                order = Order.objects.get(id=order_id)
                payment = order.payment
            except Order.DoesNotExist:
                raise ValueError(f"Order {order_id} not found")
            
            payment.provider_transaction_id = payment_intent['id']
            payment.status = 'success'
            payment.paid_at = timezone.now()
            payment.method = 'card'
            payment.raw_response = payment_intent
            payment.save()
            
            OrderService.update_status(order, 'paid')
            
            return payment
        
        # Handle payment intent failed
        elif event_type == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            order_id = payment_intent['metadata'].get('order_id')
            
            try:
                order = Order.objects.get(id=order_id)
                payment = order.payment
            except Order.DoesNotExist:
                raise ValueError(f"Order {order_id} not found")
            
            payment.status = 'failed'
            payment.raw_response = payment_intent
            payment.save()
            
            OrderService.cancel_order(order, "Payment failed")
            
            return payment
        
        # Handle refund
        elif event_type == 'charge.refunded':
            charge = event['data']['object']
            payment_intent_id = charge['payment_intent']
            
            # Find payment by transaction ID
            try:
                payment = Payment.objects.get(provider_transaction_id=payment_intent_id)
                payment.status = 'refunded'
                payment.raw_response = charge
                payment.save()
                return payment
            except Payment.DoesNotExist:
                raise ValueError(f"Payment with intent {payment_intent_id} not found")
        
        return None
    
    def get_payment_status(self, order):
        """
        Get current payment status for an order
        
        Args:
            order: Order instance
            
        Returns:
            dict: Payment status information
        """
        if not hasattr(order, 'payment'):
            return {'status': 'no_payment', 'message': 'No payment found for this order'}
        
        payment = order.payment
        
        return {
            'status': payment.status,
            'provider': payment.provider,
            'method': payment.method,
            'amount': str(payment.amount),
            'paid_at': payment.paid_at,
            'expired_at': payment.expired_at,
            'payment_url': payment.payment_url if payment.status in ['pending', 'processing'] else None,
            'is_expired': payment.is_expired
        }
    
    def refund_payment(self, order, amount=None, reason=''):
        """
        Refund a payment
        
        Args:
            order: Order instance
            amount: Amount to refund (optional, full refund if not provided)
            reason: Refund reason
            
        Returns:
            Payment instance
            
        Raises:
            ValueError: If payment cannot be refunded
        """
        if not hasattr(order, 'payment'):
            raise ValueError("No payment found for this order")
        
        payment = order.payment
        
        if payment.status != 'success':
            raise ValueError("Only successful payments can be refunded")
        
        try:
            if self.provider == 'midtrans':
                self.gateway.refund_transaction(
                    order.order_number,
                    amount=amount,
                    reason=reason
                )
            elif self.provider == 'stripe':
                self.gateway.refund_payment(
                    payment.provider_transaction_id,
                    amount=amount,
                    reason=reason
                )
            
            payment.status = 'refunded'
            payment.save()
            
            return payment
            
        except Exception as e:
            raise Exception(f"Failed to refund payment: {str(e)}")
