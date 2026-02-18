import stripe
from django.conf import settings
from decimal import Decimal


class StripeService:
    """Service for Stripe payment gateway integration"""
    
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    
    def create_checkout_session(self, order):
        """
        Create Stripe Checkout Session
        
        Args:
            order: Order instance
            
        Returns:
            dict: Contains 'session_id' and 'url'
        """
        # Prepare line items
        line_items = []
        
        for item in order.items.all():
            line_items.append({
                'price_data': {
                    'currency': 'usd',  # Change to your currency
                    'unit_amount': int(item.price * 100),  # Amount in cents
                    'product_data': {
                        'name': f"{item.product_name} - {item.variant_name}",
                        'description': f"SKU: {item.variant.sku if item.variant else 'N/A'}",
                    },
                },
                'quantity': item.quantity,
            })
        
        # Add discount if any
        if order.discount_amount > 0:
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': -int(order.discount_amount * 100),
                    'product_data': {
                        'name': 'Discount',
                    },
                },
                'quantity': 1,
            })
        
        # Add shipping
        if order.shipping_cost > 0:
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': int(order.shipping_cost * 100),
                    'product_data': {
                        'name': 'Shipping',
                    },
                },
                'quantity': 1,
            })
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            customer_email=order.user.email,
            client_reference_id=str(order.id),
            metadata={
                'order_id': str(order.id),
                'order_number': order.order_number,
            },
            success_url=f"{settings.FRONTEND_URL}/orders/{order.id}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_URL}/orders/{order.id}/cancel",
            expires_at=int((order.created_at.timestamp() + 86400)),  # 24 hours
        )
        
        return {
            'session_id': session.id,
            'url': session.url
        }
    
    def create_payment_intent(self, order):
        """
        Create Stripe Payment Intent (for custom checkout flow)
        
        Args:
            order: Order instance
            
        Returns:
            dict: Contains 'client_secret' and 'payment_intent_id'
        """
        intent = stripe.PaymentIntent.create(
            amount=int(order.total * 100),  # Amount in cents
            currency='usd',
            customer_email=order.user.email,
            metadata={
                'order_id': str(order.id),
                'order_number': order.order_number,
            },
            description=f"Order {order.order_number}",
        )
        
        return {
            'client_secret': intent.client_secret,
            'payment_intent_id': intent.id
        }
    
    def retrieve_session(self, session_id):
        """
        Retrieve checkout session details
        
        Args:
            session_id: Stripe session ID
            
        Returns:
            Session object
        """
        return stripe.checkout.Session.retrieve(session_id)
    
    def retrieve_payment_intent(self, payment_intent_id):
        """
        Retrieve payment intent details
        
        Args:
            payment_intent_id: Stripe payment intent ID
            
        Returns:
            PaymentIntent object
        """
        return stripe.PaymentIntent.retrieve(payment_intent_id)
    
    def verify_webhook_signature(self, payload, sig_header):
        """
        Verify webhook signature
        
        Args:
            payload: Raw request body
            sig_header: Stripe-Signature header value
            
        Returns:
            Event object if valid
            
        Raises:
            ValueError: If signature is invalid
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            return event
        except ValueError as e:
            # Invalid payload
            raise ValueError(f"Invalid payload: {str(e)}")
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            raise ValueError(f"Invalid signature: {str(e)}")
    
    def refund_payment(self, payment_intent_id, amount=None, reason=''):
        """
        Refund a payment
        
        Args:
            payment_intent_id: Stripe payment intent ID
            amount: Amount to refund in cents (optional, full refund if not provided)
            reason: Refund reason
            
        Returns:
            Refund object
        """
        refund_data = {'payment_intent': payment_intent_id}
        
        if amount:
            refund_data['amount'] = int(amount * 100)
        
        if reason:
            refund_data['reason'] = reason
            
        return stripe.Refund.create(**refund_data)
    
    def cancel_payment_intent(self, payment_intent_id):
        """
        Cancel a payment intent
        
        Args:
            payment_intent_id: Stripe payment intent ID
            
        Returns:
            PaymentIntent object
        """
        return stripe.PaymentIntent.cancel(payment_intent_id)
