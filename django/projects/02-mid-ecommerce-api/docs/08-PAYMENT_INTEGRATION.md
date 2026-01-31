# 💳 Step 8: Payment Integration

**Waktu:** 6-8 jam  
**Prerequisite:** Step 7 selesai

---

## 🎯 Tujuan

- Integrasi payment gateway (Midtrans/Stripe)
- Payment flow (snap/checkout)
- Webhook handling
- Payment status management

---

## 📋 Tasks

### 8.1 Payment Model

**Di `apps/payments/models.py`:**

```python
class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
        ('refunded', 'Refunded'),
    ]
    
    PROVIDER_CHOICES = [
        ('midtrans', 'Midtrans'),
        ('stripe', 'Stripe'),
    ]
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    provider_transaction_id = models.CharField(max_length=100, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    method = models.CharField(max_length=50, blank=True)  # credit_card, bank_transfer, gopay, etc.
    
    # URLs
    payment_url = models.URLField(blank=True)
    
    # Metadata
    raw_response = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now)
    paid_at = models.DateTimeField(null=True, blank=True)
    expired_at = models.DateTimeField(null=True, blank=True)
```

### 8.2 Midtrans Integration

**Install:**
```bash
pip install midtransclient
```

**Di `settings/base.py`:**

```python
MIDTRANS_SERVER_KEY = env('MIDTRANS_SERVER_KEY', default='')
MIDTRANS_CLIENT_KEY = env('MIDTRANS_CLIENT_KEY', default='')
MIDTRANS_IS_PRODUCTION = env.bool('MIDTRANS_IS_PRODUCTION', default=False)
```

**Buat `apps/payments/services/midtrans_service.py`:**

```python
import midtransclient
from django.conf import settings
from datetime import datetime, timedelta

class MidtransService:
    
    def __init__(self):
        self.snap = midtransclient.Snap(
            is_production=settings.MIDTRANS_IS_PRODUCTION,
            server_key=settings.MIDTRANS_SERVER_KEY,
            client_key=settings.MIDTRANS_CLIENT_KEY
        )
    
    def create_transaction(self, order):
        """Create Snap transaction"""
        
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
                'phone': order.shipping_phone,
                'billing_address': {
                    'address': order.shipping_address,
                    'city': order.shipping_city,
                    'postal_code': order.shipping_postal_code
                },
                'shipping_address': {
                    'first_name': order.shipping_name,
                    'address': order.shipping_address,
                    'city': order.shipping_city,
                    'postal_code': order.shipping_postal_code,
                    'phone': order.shipping_phone
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
        """Get transaction status"""
        core = midtransclient.CoreApi(
            is_production=settings.MIDTRANS_IS_PRODUCTION,
            server_key=settings.MIDTRANS_SERVER_KEY
        )
        return core.transactions.status(order_id)
    
    def verify_notification(self, notification_data):
        """Verify webhook notification"""
        # Midtrans signature verification
        import hashlib
        
        order_id = notification_data['order_id']
        status_code = notification_data['status_code']
        gross_amount = notification_data['gross_amount']
        server_key = settings.MIDTRANS_SERVER_KEY
        
        signature = hashlib.sha512(
            f"{order_id}{status_code}{gross_amount}{server_key}".encode()
        ).hexdigest()
        
        return signature == notification_data.get('signature_key')
```

### 8.3 Payment Service

**Buat `apps/payments/services/payment_service.py`:**

```python
from .midtrans_service import MidtransService
from ..models import Payment
from apps.orders.models import Order
from apps.orders.services import OrderService

class PaymentService:
    
    def __init__(self, provider='midtrans'):
        self.provider = provider
        if provider == 'midtrans':
            self.gateway = MidtransService()
    
    def create_payment(self, order):
        """Initialize payment for order"""
        
        # Check if payment already exists
        if hasattr(order, 'payment'):
            if order.payment.status in ['pending', 'processing']:
                return order.payment
        
        # Create payment record
        payment = Payment.objects.create(
            order=order,
            provider=self.provider,
            amount=order.total,
            expired_at=timezone.now() + timedelta(hours=24)
        )
        
        # Create transaction with payment gateway
        try:
            result = self.gateway.create_transaction(order)
            
            payment.payment_url = result['redirect_url']
            payment.raw_response = result
            payment.save()
            
            return payment
            
        except Exception as e:
            payment.status = 'failed'
            payment.raw_response = {'error': str(e)}
            payment.save()
            raise
    
    def handle_notification(self, notification_data):
        """Handle payment notification from gateway"""
        
        if self.provider == 'midtrans':
            return self._handle_midtrans_notification(notification_data)
    
    def _handle_midtrans_notification(self, data):
        """Handle Midtrans notification"""
        
        # Verify signature
        if not self.gateway.verify_notification(data):
            raise ValueError("Invalid signature")
        
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
            # Release stock
            OrderService.cancel_order(order, f"Payment {transaction_status}")
        
        elif transaction_status == 'refund':
            payment.status = 'refunded'
        
        payment.save()
        return payment
```

### 8.4 Views

```python
class CreatePaymentView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, order_id):
        """Create payment for order"""
        order = get_object_or_404(Order, pk=order_id, user=request.user)
        
        if order.status != 'pending':
            return Response({'error': 'Order is not pending payment'}, status=400)
        
        try:
            service = PaymentService(provider='midtrans')
            payment = service.create_payment(order)
            
            return Response({
                'payment_id': payment.id,
                'payment_url': payment.payment_url,
                'expires_at': payment.expired_at
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class PaymentWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    
    def post(self, request):
        """Handle payment webhook"""
        try:
            service = PaymentService(provider='midtrans')
            payment = service.handle_notification(request.data)
            
            return Response({'status': 'ok'})
        except ValueError as e:
            return Response({'error': str(e)}, status=400)
        except Exception as e:
            # Log error but return 200 to prevent retries
            print(f"Webhook error: {e}")
            return Response({'status': 'ok'})


class PaymentStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, order_id):
        """Check payment status"""
        order = get_object_or_404(Order, pk=order_id, user=request.user)
        
        if not hasattr(order, 'payment'):
            return Response({'error': 'No payment found'}, status=404)
        
        payment = order.payment
        
        return Response({
            'status': payment.status,
            'method': payment.method,
            'paid_at': payment.paid_at,
            'payment_url': payment.payment_url if payment.status == 'pending' else None
        })
```

### 8.5 URLs

```python
urlpatterns = [
    path('orders/<int:order_id>/pay/', CreatePaymentView.as_view(), name='create-payment'),
    path('orders/<int:order_id>/payment-status/', PaymentStatusView.as_view(), name='payment-status'),
    path('webhooks/midtrans/', PaymentWebhookView.as_view(), name='midtrans-webhook'),
]
```

---

## 🔄 Payment Flow

```
1. Customer checkout -> Order created (status: pending)
2. Customer clicks "Pay Now"
   -> POST /api/orders/{id}/pay/
   -> Returns payment_url (Midtrans Snap)
3. Customer redirected to Midtrans
4. Customer completes payment
5. Midtrans sends webhook
   -> POST /api/webhooks/midtrans/
   -> Payment updated, Order status -> paid
6. Customer redirected back to frontend
```

---

## ✅ Checklist

- [ ] Payment model
- [ ] Midtrans configuration
- [ ] MidtransService dengan Snap
- [ ] PaymentService untuk abstraction
- [ ] Create payment endpoint
- [ ] Webhook handler
- [ ] Signature verification
- [ ] Status mapping
- [ ] Order status update on payment
- [ ] Stock release on failed payment
- [ ] Payment status endpoint

---

## 🔒 Security

```
□ Verify webhook signatures
□ Use HTTPS for webhook URLs
□ Validate order ownership
□ Don't expose server keys
□ Log all payment events
□ Handle idempotency (same notification multiple times)
```

---

## 🎉 Project Complete!

Selamat! Kamu sudah menyelesaikan Project 02: E-Commerce API.

**Yang sudah dipelajari:**
- ✅ Complex data models (Products, Orders)
- ✅ File upload ke S3
- ✅ Email notifications dengan Celery
- ✅ Export reports (PDF, Excel)
- ✅ Payment gateway integration
- ✅ Webhook handling
- ✅ Caching dengan Redis

**Next Step:** Lanjut ke [Project 03: Collaboration Platform](../../03-senior-collab-platform/README.md)
