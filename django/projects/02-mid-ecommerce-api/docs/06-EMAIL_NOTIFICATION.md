# 📧 Step 6: Email Notifications

**Waktu:** 4-6 jam  
**Prerequisite:** Step 5 selesai

---

## 🎯 Tujuan

- Setup email configuration
- HTML email templates
- Order confirmation email
- Shipping notification
- Async email dengan Celery

---

## 📋 Tasks

### 6.1 Email Configuration

**Di `settings/base.py`:**

```python
# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@yourstore.com')
```

**Di `settings/development.py`:**

```python
# Development: Print emails to console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

### 6.2 Email Service

**Buat `apps/core/services/email_service.py`:**

```python
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

class EmailService:
    
    @staticmethod
    def send_email(to_email, subject, template_name, context):
        """Send HTML email with plain text fallback"""
        
        # Add common context
        context.update({
            'site_name': settings.SITE_NAME,
            'base_url': settings.BASE_URL,
        })
        
        # Render templates
        html_content = render_to_string(f'emails/{template_name}.html', context)
        text_content = render_to_string(f'emails/{template_name}.txt', context)
        
        # Create email
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email]
        )
        msg.attach_alternative(html_content, "text/html")
        
        # Send
        msg.send()
        
        return True
    
    @classmethod
    def send_order_confirmation(cls, order):
        """Send order confirmation email"""
        cls.send_email(
            to_email=order.user.email,
            subject=f'Order Confirmation - {order.order_number}',
            template_name='order_confirmation',
            context={
                'order': order,
                'items': order.items.all(),
                'user': order.user,
            }
        )
    
    @classmethod
    def send_order_shipped(cls, order, tracking_number):
        """Send shipping notification"""
        cls.send_email(
            to_email=order.user.email,
            subject=f'Your Order Has Been Shipped - {order.order_number}',
            template_name='order_shipped',
            context={
                'order': order,
                'tracking_number': tracking_number,
                'user': order.user,
            }
        )
    
    @classmethod
    def send_payment_confirmation(cls, order):
        """Send payment confirmation"""
        cls.send_email(
            to_email=order.user.email,
            subject=f'Payment Received - {order.order_number}',
            template_name='payment_confirmation',
            context={
                'order': order,
                'user': order.user,
            }
        )
```

### 6.3 Email Templates

**Buat struktur folder:**

```
templates/
└── emails/
    ├── base.html
    ├── order_confirmation.html
    ├── order_confirmation.txt
    ├── order_shipped.html
    ├── order_shipped.txt
    ├── payment_confirmation.html
    └── payment_confirmation.txt
```

**`templates/emails/base.html`:**

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background-color: #4A90D9;
            color: white;
            padding: 20px;
            text-align: center;
        }
        .content {
            padding: 20px;
            background-color: #f9f9f9;
        }
        .button {
            display: inline-block;
            padding: 12px 24px;
            background-color: #4A90D9;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            margin: 20px 0;
        }
        .order-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        .order-table th, .order-table td {
            padding: 10px;
            border-bottom: 1px solid #ddd;
            text-align: left;
        }
        .total-row {
            font-weight: bold;
            background-color: #f0f0f0;
        }
        .footer {
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ site_name }}</h1>
    </div>
    <div class="content">
        {% block content %}{% endblock %}
    </div>
    <div class="footer">
        <p>&copy; {% now "Y" %} {{ site_name }}. All rights reserved.</p>
        <p>Questions? Contact us at support@yourstore.com</p>
    </div>
</body>
</html>
```

**`templates/emails/order_confirmation.html`:**

```html
{% extends "emails/base.html" %}

{% block content %}
<h2>Thank You for Your Order!</h2>

<p>Hi {{ user.name }},</p>

<p>We've received your order and it's being processed.</p>

<div style="background: #fff; padding: 15px; border-radius: 4px; margin: 20px 0;">
    <p><strong>Order Number:</strong> {{ order.order_number }}</p>
    <p><strong>Order Date:</strong> {{ order.created_at|date:"F d, Y" }}</p>
</div>

<h3>Order Summary</h3>

<table class="order-table">
    <thead>
        <tr>
            <th>Product</th>
            <th>Qty</th>
            <th>Price</th>
        </tr>
    </thead>
    <tbody>
        {% for item in items %}
        <tr>
            <td>{{ item.product_name }} - {{ item.variant_name }}</td>
            <td>{{ item.quantity }}</td>
            <td>Rp {{ item.subtotal|floatformat:0 }}</td>
        </tr>
        {% endfor %}
    </tbody>
    <tfoot>
        <tr>
            <td colspan="2">Subtotal</td>
            <td>Rp {{ order.subtotal|floatformat:0 }}</td>
        </tr>
        {% if order.discount_amount %}
        <tr>
            <td colspan="2">Discount</td>
            <td>-Rp {{ order.discount_amount|floatformat:0 }}</td>
        </tr>
        {% endif %}
        <tr>
            <td colspan="2">Shipping</td>
            <td>Rp {{ order.shipping_cost|floatformat:0 }}</td>
        </tr>
        <tr class="total-row">
            <td colspan="2">Total</td>
            <td>Rp {{ order.total|floatformat:0 }}</td>
        </tr>
    </tfoot>
</table>

<h3>Shipping Address</h3>
<p>
    {{ order.shipping_name }}<br>
    {{ order.shipping_address }}<br>
    {{ order.shipping_city }} {{ order.shipping_postal_code }}<br>
    {{ order.shipping_phone }}
</p>

<a href="{{ base_url }}/orders/{{ order.id }}" class="button">View Order</a>

<p>We'll send you another email when your order ships.</p>
{% endblock %}
```

### 6.4 Celery Tasks

**Di `apps/orders/tasks.py`:**

```python
from celery import shared_task
from apps.core.services.email_service import EmailService

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60  # 1 minute
)
def send_order_confirmation_email(self, order_id):
    """Send order confirmation email asynchronously"""
    from .models import Order
    
    try:
        order = Order.objects.get(pk=order_id)
        EmailService.send_order_confirmation(order)
    except Order.DoesNotExist:
        pass  # Order was deleted
    except Exception as exc:
        # Retry on failure
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3)
def send_shipping_notification_email(self, order_id, tracking_number):
    """Send shipping notification asynchronously"""
    from .models import Order
    
    try:
        order = Order.objects.get(pk=order_id)
        EmailService.send_order_shipped(order, tracking_number)
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3)
def send_payment_confirmation_email(self, order_id):
    """Send payment confirmation asynchronously"""
    from .models import Order
    
    try:
        order = Order.objects.get(pk=order_id)
        EmailService.send_payment_confirmation(order)
    except Exception as exc:
        raise self.retry(exc=exc)
```

**Referensi:** [EMAIL.md](../../../docs/04-advanced/EMAIL.md) - Celery section

### 6.5 Trigger Emails

**Update `apps/orders/services.py`:**

```python
from .tasks import (
    send_order_confirmation_email,
    send_shipping_notification_email,
    send_payment_confirmation_email
)

class OrderService:
    
    @staticmethod
    def create_from_cart(user, cart, shipping_data):
        # ... existing code ...
        
        order = Order.objects.create(...)
        
        # Trigger confirmation email (async)
        send_order_confirmation_email.delay(order.id)
        
        return order
    
    @staticmethod
    def update_status(order, new_status, **kwargs):
        # ... existing code ...
        
        if new_status == 'paid':
            send_payment_confirmation_email.delay(order.id)
        
        elif new_status == 'shipped':
            tracking = kwargs.get('tracking_number')
            send_shipping_notification_email.delay(order.id, tracking)
        
        return order
```

### 6.6 SendGrid (Production)

**Install:**
```bash
pip install django-anymail
```

**Di `settings/production.py`:**

```python
INSTALLED_APPS += ['anymail']

EMAIL_BACKEND = 'anymail.backends.sendgrid.EmailBackend'
ANYMAIL = {
    'SENDGRID_API_KEY': env('SENDGRID_API_KEY'),
}
```

**Referensi:** [EMAIL.md](../../../docs/04-advanced/EMAIL.md) - SendGrid section

---

## ✅ Checklist

- [ ] Email configuration (SMTP)
- [ ] Console backend for development
- [ ] EmailService class
- [ ] Base email template
- [ ] Order confirmation template
- [ ] Shipping notification template
- [ ] Payment confirmation template
- [ ] Celery tasks dengan retry
- [ ] Trigger emails from OrderService
- [ ] SendGrid setup (production)

---

## 🔗 Referensi

- [EMAIL.md](../../../docs/04-advanced/EMAIL.md) - Complete email guide
- [BACKGROUND_JOBS.md](../../../docs/04-advanced/BACKGROUND_JOBS.md) - Celery

---

## ➡️ Next Step

Lanjut ke [07-EXPORT_REPORTS.md](07-EXPORT_REPORTS.md) - Sales Reports
