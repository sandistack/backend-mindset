"""
Email service for sending notifications.
"""

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending HTML emails."""
    
    @staticmethod
    def send_email(to_email, subject, template_name, context):
        """
        Send HTML email with plain text fallback.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            template_name: Template name (without extension)
            context: Dict of template context variables
        
        Returns:
            bool: True if sent successfully
        """
        try:
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
            
            logger.info(f"Email sent to {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            raise
    
    @classmethod
    def send_order_confirmation(cls, order):
        """
        Send order confirmation email.
        
        Args:
            order: Order instance
        """
        return cls.send_email(
            to_email=order.user.email,
            subject=f'Order Confirmation - {order.order_number}',
            template_name='order_confirmation',
            context={
                'order': order,
                'items': order.items.select_related('variant__product').all(),
                'user': order.user,
            }
        )
    
    @classmethod
    def send_order_shipped(cls, order, tracking_number=''):
        """
        Send shipping notification email.
        
        Args:
            order: Order instance
            tracking_number: Tracking number for shipment
        """
        return cls.send_email(
            to_email=order.user.email,
            subject=f'Your Order Has Been Shipped - {order.order_number}',
            template_name='order_shipped',
            context={
                'order': order,
                'tracking_number': tracking_number or order.tracking_number,
                'user': order.user,
            }
        )
    
    @classmethod
    def send_payment_confirmation(cls, order):
        """
        Send payment confirmation email.
        
        Args:
            order: Order instance
        """
        return cls.send_email(
            to_email=order.user.email,
            subject=f'Payment Received - {order.order_number}',
            template_name='payment_confirmation',
            context={
                'order': order,
                'items': order.items.select_related('variant__product').all(),
                'user': order.user,
            }
        )
