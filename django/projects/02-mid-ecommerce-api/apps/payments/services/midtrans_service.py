import midtransclient
import hashlib
from django.conf import settings
from datetime import datetime, timedelta


class MidtransService:
    """Service for Midtrans payment gateway integration"""
    
    def __init__(self):
        self.snap = midtransclient.Snap(
            is_production=settings.MIDTRANS_IS_PRODUCTION,
            server_key=settings.MIDTRANS_SERVER_KEY,
            client_key=settings.MIDTRANS_CLIENT_KEY
        )
        self.core_api = midtransclient.CoreApi(
            is_production=settings.MIDTRANS_IS_PRODUCTION,
            server_key=settings.MIDTRANS_SERVER_KEY,
            client_key=settings.MIDTRANS_CLIENT_KEY
        )
    
    def create_transaction(self, order):
        """
        Create Snap transaction for Midtrans
        
        Args:
            order: Order instance
            
        Returns:
            dict: Contains 'token' and 'redirect_url'
        """
        # Prepare item details
        items = []
        for item in order.items.all():
            items.append({
                'id': str(item.variant.id),
                'name': f"{item.product_name} - {item.variant_name}"[:50],
                'price': int(item.price),
                'quantity': item.quantity
            })
        
        # Add discount as negative item
        if order.discount_amount > 0:
            items.append({
                'id': 'DISCOUNT',
                'name': 'Discount',
                'price': -int(order.discount_amount),
                'quantity': 1
            })
        
        # Add shipping
        if order.shipping_cost > 0:
            items.append({
                'id': 'SHIPPING',
                'name': 'Shipping Cost',
                'price': int(order.shipping_cost),
                'quantity': 1
            })
        
        # Transaction details
        transaction_data = {
            'transaction_details': {
                'order_id': order.order_number,
                'gross_amount': int(order.total)
            },
            'item_details': items,
            'customer_details': {
                'first_name': order.user.name,
                'email': order.user.email,
                'phone': order.shipping_phone or '',
                'billing_address': {
                    'address': order.shipping_address,
                    'city': order.shipping_city,
                    'postal_code': order.shipping_postal_code or ''
                },
                'shipping_address': {
                    'first_name': order.shipping_name,
                    'address': order.shipping_address,
                    'city': order.shipping_city,
                    'postal_code': order.shipping_postal_code or '',
                    'phone': order.shipping_phone or ''
                }
            },
            'expiry': {
                'unit': 'hours',
                'duration': 24
            },
            'callbacks': {
                'finish': f"{settings.FRONTEND_URL}/orders/{order.id}/finish"
            }
        }
        
        # Create transaction
        response = self.snap.create_transaction(transaction_data)
        
        return {
            'token': response['token'],
            'redirect_url': response['redirect_url']
        }
    
    def get_transaction_status(self, order_id):
        """
        Get transaction status from Midtrans
        
        Args:
            order_id: Order number/ID
            
        Returns:
            dict: Transaction status data
        """
        return self.core_api.transactions.status(order_id)
    
    def verify_notification(self, notification_data):
        """
        Verify webhook notification signature
        
        Args:
            notification_data: Notification payload from webhook
            
        Returns:
            bool: True if signature is valid
        """
        order_id = notification_data.get('order_id', '')
        status_code = notification_data.get('status_code', '')
        gross_amount = notification_data.get('gross_amount', '')
        server_key = settings.MIDTRANS_SERVER_KEY
        
        # Calculate signature
        signature = hashlib.sha512(
            f"{order_id}{status_code}{gross_amount}{server_key}".encode()
        ).hexdigest()
        
        return signature == notification_data.get('signature_key')
    
    def cancel_transaction(self, order_id):
        """
        Cancel transaction
        
        Args:
            order_id: Order number/ID
            
        Returns:
            dict: Response from Midtrans
        """
        return self.core_api.transactions.cancel(order_id)
    
    def refund_transaction(self, order_id, amount=None, reason=''):
        """
        Refund transaction
        
        Args:
            order_id: Order number/ID
            amount: Amount to refund (optional, full refund if not provided)
            reason: Refund reason
            
        Returns:
            dict: Response from Midtrans
        """
        refund_data = {'reason': reason}
        if amount:
            refund_data['amount'] = int(amount)
            
        return self.core_api.transactions.refund(order_id, refund_data)
