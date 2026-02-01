# 📧 EMAIL - Django (Junior → Senior)

Dokumentasi lengkap tentang sending emails di Django, dari SMTP sederhana hingga templated async emails.

---

## 🎯 Kapan Butuh Email?

```
Use Cases:
✅ Welcome email setelah register
✅ Password reset
✅ Email verification
✅ Order confirmation
✅ Notification alerts
✅ Weekly reports/digest
✅ Invoice/receipt
```

---

## 1️⃣ JUNIOR LEVEL - Basic Email Setup

### Settings Configuration

```python
# config/settings/base.py

# Email backend for development (console output)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Basic email settings
DEFAULT_FROM_EMAIL = 'noreply@yourapp.com'
EMAIL_SUBJECT_PREFIX = '[YourApp] '
```

```python
# config/settings/production.py

# SMTP Email backend for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@yourapp.com')
```

### Send Simple Email

```python
from django.core.mail import send_mail

# Basic send
send_mail(
    subject='Welcome to Our App!',
    message='Thank you for signing up.',
    from_email='noreply@yourapp.com',
    recipient_list=['user@example.com'],
    fail_silently=False,
)
```

### Send HTML Email

```python
from django.core.mail import send_mail

send_mail(
    subject='Welcome to Our App!',
    message='Thank you for signing up.',  # Fallback plain text
    from_email='noreply@yourapp.com',
    recipient_list=['user@example.com'],
    html_message='<h1>Welcome!</h1><p>Thank you for signing up.</p>',
    fail_silently=False,
)
```

---

## 2️⃣ MID LEVEL - Email Templates

### Create Email Templates

```html
<!-- templates/emails/base.html -->
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
        <h1>{% block header %}{{ app_name }}{% endblock %}</h1>
    </div>
    
    <div class="content">
        {% block content %}{% endblock %}
    </div>
    
    <div class="footer">
        {% block footer %}
        <p>&copy; {{ year }} {{ app_name }}. All rights reserved.</p>
        <p>
            <a href="{{ unsubscribe_url }}">Unsubscribe</a> | 
            <a href="{{ privacy_url }}">Privacy Policy</a>
        </p>
        {% endblock %}
    </div>
</body>
</html>
```

```html
<!-- templates/emails/welcome.html -->
{% extends "emails/base.html" %}

{% block header %}Welcome to {{ app_name }}!{% endblock %}

{% block content %}
<h2>Hi {{ user.first_name }}!</h2>

<p>Thank you for joining {{ app_name }}. We're excited to have you on board!</p>

<p>Here's what you can do next:</p>
<ul>
    <li>Complete your profile</li>
    <li>Explore our features</li>
    <li>Connect with others</li>
</ul>

<a href="{{ dashboard_url }}" class="button">Go to Dashboard</a>

<p>If you have any questions, feel free to reply to this email.</p>

<p>Best regards,<br>The {{ app_name }} Team</p>
{% endblock %}
```

```html
<!-- templates/emails/password_reset.html -->
{% extends "emails/base.html" %}

{% block header %}Password Reset{% endblock %}

{% block content %}
<h2>Hi {{ user.first_name }},</h2>

<p>We received a request to reset your password.</p>

<p>Click the button below to reset your password:</p>

<a href="{{ reset_url }}" class="button">Reset Password</a>

<p><small>This link will expire in {{ expiry_hours }} hours.</small></p>

<p>If you didn't request this, you can safely ignore this email.</p>

<p>Best regards,<br>The {{ app_name }} Team</p>
{% endblock %}
```

### Email Service

```python
# apps/core/services/email_service.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from datetime import datetime


class EmailService:
    """
    Service untuk mengirim templated emails
    """
    
    def __init__(self):
        self.from_email = settings.DEFAULT_FROM_EMAIL
        self.app_name = getattr(settings, 'APP_NAME', 'YourApp')
        self.base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
    
    def _get_base_context(self) -> dict:
        """
        Context default untuk semua email
        """
        return {
            'app_name': self.app_name,
            'year': datetime.now().year,
            'base_url': self.base_url,
            'unsubscribe_url': f'{self.base_url}/unsubscribe',
            'privacy_url': f'{self.base_url}/privacy',
        }
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        context: dict = None,
        attachments: list = None
    ) -> bool:
        """
        Send templated email
        """
        # Merge base context with custom context
        full_context = self._get_base_context()
        if context:
            full_context.update(context)
        
        # Render templates
        html_content = render_to_string(f'emails/{template_name}.html', full_context)
        text_content = render_to_string(f'emails/{template_name}.txt', full_context)
        
        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=self.from_email,
            to=[to_email]
        )
        email.attach_alternative(html_content, 'text/html')
        
        # Add attachments
        if attachments:
            for attachment in attachments:
                email.attach(
                    attachment['filename'],
                    attachment['content'],
                    attachment.get('mimetype', 'application/octet-stream')
                )
        
        try:
            email.send(fail_silently=False)
            return True
        except Exception as e:
            # Log error
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Failed to send email to {to_email}: {e}')
            return False
    
    def send_welcome_email(self, user) -> bool:
        """
        Send welcome email to new user
        """
        return self.send_email(
            to_email=user.email,
            subject=f'Welcome to {self.app_name}!',
            template_name='welcome',
            context={
                'user': user,
                'dashboard_url': f'{self.base_url}/dashboard',
            }
        )
    
    def send_password_reset_email(self, user, reset_token: str) -> bool:
        """
        Send password reset email
        """
        reset_url = f'{self.base_url}/reset-password?token={reset_token}'
        
        return self.send_email(
            to_email=user.email,
            subject='Password Reset Request',
            template_name='password_reset',
            context={
                'user': user,
                'reset_url': reset_url,
                'expiry_hours': 24,
            }
        )
    
    def send_verification_email(self, user, verification_token: str) -> bool:
        """
        Send email verification
        """
        verify_url = f'{self.base_url}/verify-email?token={verification_token}'
        
        return self.send_email(
            to_email=user.email,
            subject='Verify Your Email',
            template_name='verify_email',
            context={
                'user': user,
                'verify_url': verify_url,
            }
        )
```

### Usage in Views

```python
# apps/authentication/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.core.services.email_service import EmailService

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.save()
        
        # Send welcome email
        email_service = EmailService()
        email_service.send_welcome_email(user)
        
        return Response({'message': 'Registration successful'})
```

---

## 3️⃣ MID-SENIOR LEVEL - Async Email with Celery

### Celery Tasks

```python
# apps/core/tasks.py
from celery import shared_task
from django.contrib.auth import get_user_model

User = get_user_model()


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # Retry after 1 minute
)
def send_email_task(self, email_type: str, user_id: int, **kwargs):
    """
    Async task untuk send email
    """
    from apps.core.services.email_service import EmailService
    
    try:
        user = User.objects.get(id=user_id)
        email_service = EmailService()
        
        if email_type == 'welcome':
            success = email_service.send_welcome_email(user)
        elif email_type == 'password_reset':
            success = email_service.send_password_reset_email(
                user,
                kwargs.get('reset_token')
            )
        elif email_type == 'verification':
            success = email_service.send_verification_email(
                user,
                kwargs.get('verification_token')
            )
        else:
            raise ValueError(f'Unknown email type: {email_type}')
        
        if not success:
            raise Exception('Email sending failed')
        
        return {'status': 'sent', 'user_id': user_id, 'email_type': email_type}
        
    except User.DoesNotExist:
        return {'status': 'failed', 'error': 'User not found'}
    except Exception as e:
        # Retry on failure
        self.retry(exc=e)


@shared_task
def send_bulk_email_task(user_ids: list, subject: str, template_name: str, context: dict = None):
    """
    Send bulk emails to multiple users
    """
    from apps.core.services.email_service import EmailService
    
    email_service = EmailService()
    results = {'sent': 0, 'failed': 0}
    
    for user_id in user_ids:
        try:
            user = User.objects.get(id=user_id)
            ctx = context.copy() if context else {}
            ctx['user'] = user
            
            success = email_service.send_email(
                to_email=user.email,
                subject=subject,
                template_name=template_name,
                context=ctx
            )
            
            if success:
                results['sent'] += 1
            else:
                results['failed'] += 1
                
        except User.DoesNotExist:
            results['failed'] += 1
    
    return results
```

### Async Email Service

```python
# apps/core/services/email_service.py (updated)
from apps.core.tasks import send_email_task

class EmailService:
    # ... previous methods ...
    
    def send_welcome_email_async(self, user) -> None:
        """
        Send welcome email asynchronously
        """
        send_email_task.delay('welcome', user.id)
    
    def send_password_reset_email_async(self, user, reset_token: str) -> None:
        """
        Send password reset email asynchronously
        """
        send_email_task.delay('password_reset', user.id, reset_token=reset_token)
    
    def send_verification_email_async(self, user, verification_token: str) -> None:
        """
        Send verification email asynchronously
        """
        send_email_task.delay('verification', user.id, verification_token=verification_token)
```

### Using Signals for Auto-Email

```python
# apps/authentication/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from apps.core.services.email_service import EmailService

User = get_user_model()

@receiver(post_save, sender=User)
def send_welcome_email_on_register(sender, instance, created, **kwargs):
    """
    Auto-send welcome email when user is created
    """
    if created:
        email_service = EmailService()
        email_service.send_welcome_email_async(instance)
```

---

## 4️⃣ SENIOR LEVEL - Email Providers (SendGrid, Mailgun)

### SendGrid Setup

```bash
pip install sendgrid
```

```python
# config/settings/production.py

# SendGrid Configuration
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
SENDGRID_SANDBOX_MODE_IN_DEBUG = False

# Alternative: Using SMTP
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = os.environ.get('SENDGRID_API_KEY')
```

### SendGrid Service

```python
# apps/core/services/sendgrid_service.py
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType
from django.conf import settings
from django.template.loader import render_to_string
import base64


class SendGridService:
    """
    SendGrid email service with advanced features
    """
    
    def __init__(self):
        self.client = SendGridAPIClient(settings.SENDGRID_API_KEY)
        self.from_email = settings.DEFAULT_FROM_EMAIL
    
    def send_email(
        self,
        to_emails: list,
        subject: str,
        template_name: str,
        context: dict = None,
        attachments: list = None,
        categories: list = None
    ) -> dict:
        """
        Send email via SendGrid API
        """
        # Render template
        html_content = render_to_string(f'emails/{template_name}.html', context or {})
        
        message = Mail(
            from_email=self.from_email,
            to_emails=to_emails,
            subject=subject,
            html_content=html_content
        )
        
        # Add categories for analytics
        if categories:
            for category in categories:
                message.add_category(category)
        
        # Add attachments
        if attachments:
            for att in attachments:
                attachment = Attachment()
                attachment.file_content = FileContent(
                    base64.b64encode(att['content']).decode()
                )
                attachment.file_name = FileName(att['filename'])
                attachment.file_type = FileType(att.get('mimetype', 'application/octet-stream'))
                message.add_attachment(attachment)
        
        try:
            response = self.client.send(message)
            return {
                'success': True,
                'status_code': response.status_code,
                'message_id': response.headers.get('X-Message-Id')
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_with_template(
        self,
        to_emails: list,
        template_id: str,
        dynamic_data: dict
    ) -> dict:
        """
        Send email using SendGrid Dynamic Template
        """
        message = Mail(
            from_email=self.from_email,
            to_emails=to_emails
        )
        message.template_id = template_id
        message.dynamic_template_data = dynamic_data
        
        try:
            response = self.client.send(message)
            return {
                'success': True,
                'status_code': response.status_code
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
```

### Mailgun Setup

```bash
pip install requests
```

```python
# apps/core/services/mailgun_service.py
import requests
from django.conf import settings
from django.template.loader import render_to_string


class MailgunService:
    """
    Mailgun email service
    """
    
    def __init__(self):
        self.api_key = settings.MAILGUN_API_KEY
        self.domain = settings.MAILGUN_DOMAIN
        self.base_url = f'https://api.mailgun.net/v3/{self.domain}'
        self.from_email = settings.DEFAULT_FROM_EMAIL
    
    def send_email(
        self,
        to_emails: list,
        subject: str,
        template_name: str = None,
        html_content: str = None,
        context: dict = None,
        tags: list = None
    ) -> dict:
        """
        Send email via Mailgun API
        """
        if template_name:
            html_content = render_to_string(f'emails/{template_name}.html', context or {})
        
        data = {
            'from': self.from_email,
            'to': to_emails,
            'subject': subject,
            'html': html_content
        }
        
        if tags:
            data['o:tag'] = tags
        
        try:
            response = requests.post(
                f'{self.base_url}/messages',
                auth=('api', self.api_key),
                data=data
            )
            response.raise_for_status()
            
            return {
                'success': True,
                'message_id': response.json().get('id')
            }
        except requests.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }
```

---

## 5️⃣ EXPERT LEVEL - Email Tracking & Analytics

### Email Log Model

```python
# apps/core/models.py
from django.db import models

class EmailLog(models.Model):
    """
    Track all sent emails
    """
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SENT = 'sent', 'Sent'
        DELIVERED = 'delivered', 'Delivered'
        OPENED = 'opened', 'Opened'
        CLICKED = 'clicked', 'Clicked'
        BOUNCED = 'bounced', 'Bounced'
        FAILED = 'failed', 'Failed'
    
    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    template = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    message_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Tracking
    sent_at = models.DateTimeField(null=True)
    delivered_at = models.DateTimeField(null=True)
    opened_at = models.DateTimeField(null=True)
    clicked_at = models.DateTimeField(null=True)
    
    # Error info
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'status']),
            models.Index(fields=['created_at']),
        ]
```

### Webhook Handler for Tracking

```python
# apps/core/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone
from .models import EmailLog

class SendGridWebhookView(APIView):
    """
    Handle SendGrid event webhooks
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        events = request.data
        
        for event in events:
            message_id = event.get('sg_message_id', '').split('.')[0]
            event_type = event.get('event')
            
            try:
                email_log = EmailLog.objects.get(message_id__startswith=message_id)
                
                if event_type == 'delivered':
                    email_log.status = EmailLog.Status.DELIVERED
                    email_log.delivered_at = timezone.now()
                elif event_type == 'open':
                    email_log.status = EmailLog.Status.OPENED
                    email_log.opened_at = timezone.now()
                elif event_type == 'click':
                    email_log.status = EmailLog.Status.CLICKED
                    email_log.clicked_at = timezone.now()
                elif event_type == 'bounce':
                    email_log.status = EmailLog.Status.BOUNCED
                    email_log.error_message = event.get('reason', '')
                
                email_log.save()
                
            except EmailLog.DoesNotExist:
                pass
        
        return Response({'status': 'ok'})
```

### Email Analytics

```python
# apps/core/services/email_analytics.py
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from datetime import timedelta
from django.utils import timezone
from apps.core.models import EmailLog


class EmailAnalytics:
    """
    Analytics for email performance
    """
    
    @staticmethod
    def get_daily_stats(days: int = 30) -> list:
        """
        Get daily email statistics
        """
        start_date = timezone.now() - timedelta(days=days)
        
        return EmailLog.objects.filter(
            created_at__gte=start_date
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            total=Count('id'),
            sent=Count('id', filter=Q(status='sent')),
            delivered=Count('id', filter=Q(status='delivered')),
            opened=Count('id', filter=Q(status='opened')),
            clicked=Count('id', filter=Q(status='clicked')),
            bounced=Count('id', filter=Q(status='bounced')),
            failed=Count('id', filter=Q(status='failed')),
        ).order_by('date')
    
    @staticmethod
    def get_template_performance() -> list:
        """
        Get performance by template
        """
        return EmailLog.objects.values('template').annotate(
            total=Count('id'),
            delivered=Count('id', filter=Q(status='delivered')),
            opened=Count('id', filter=Q(status='opened')),
            clicked=Count('id', filter=Q(status='clicked')),
        ).annotate(
            open_rate=Count('id', filter=Q(status='opened')) * 100.0 / Count('id'),
            click_rate=Count('id', filter=Q(status='clicked')) * 100.0 / Count('id'),
        ).order_by('-total')
```

---

## 📋 Quick Reference

### Email Providers Comparison

| Provider | Free Tier | Best For |
|----------|-----------|----------|
| **SendGrid** | 100/day | Transactional + Marketing |
| **Mailgun** | 5,000/mo (3 months) | Developers |
| **Amazon SES** | 62,000/mo (from EC2) | High volume |
| **Postmark** | 100/mo | Transactional only |
| **Mailchimp** | 500/mo | Marketing campaigns |

### Email Checklist

```
□ Use async sending (Celery) for non-blocking
□ Validate email addresses before sending
□ Handle bounces and unsubscribes
□ Include unsubscribe link (legally required)
□ Test emails in multiple clients
□ Use responsive email templates
□ Log all sent emails
□ Set up webhooks for tracking
□ Rate limit bulk sending
□ Use separate domain for transactional emails
```

---

## 🔗 Related Docs

- [BACKGROUND_JOBS.md](BACKGROUND_JOBS.md) - Async email sending
- [SIGNALS.md](SIGNALS.md) - Auto-send on events
- [LOG.md](../06-operations/LOG.md) - Email logging
