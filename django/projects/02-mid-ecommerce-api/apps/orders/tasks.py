"""
Celery tasks for order notifications.
"""

from celery import shared_task
from apps.core.services.email_service import EmailService
import logging

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60  # 1 minute
)
def send_order_confirmation_email(self, order_id):
    """
    Send order confirmation email asynchronously.
    
    Args:
        order_id: Order ID
    """
    from .models import Order
    
    try:
        order = Order.objects.get(pk=order_id)
        EmailService.send_order_confirmation(order)
        logger.info(f"Order confirmation email sent for order {order.order_number}")
    except Order.DoesNotExist:
        logger.warning(f"Order {order_id} not found, email not sent")
    except Exception as exc:
        logger.error(f"Failed to send order confirmation email: {str(exc)}")
        # Retry on failure
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def send_shipping_notification_email(self, order_id, tracking_number=''):
    """
    Send shipping notification email asynchronously.
    
    Args:
        order_id: Order ID
        tracking_number: Tracking number for shipment
    """
    from .models import Order
    
    try:
        order = Order.objects.get(pk=order_id)
        EmailService.send_order_shipped(order, tracking_number)
        logger.info(f"Shipping notification email sent for order {order.order_number}")
    except Order.DoesNotExist:
        logger.warning(f"Order {order_id} not found, email not sent")
    except Exception as exc:
        logger.error(f"Failed to send shipping notification email: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def send_payment_confirmation_email(self, order_id):
    """
    Send payment confirmation email asynchronously.
    
    Args:
        order_id: Order ID
    """
    from .models import Order
    
    try:
        order = Order.objects.get(pk=order_id)
        EmailService.send_payment_confirmation(order)
        logger.info(f"Payment confirmation email sent for order {order.order_number}")
    except Order.DoesNotExist:
        logger.warning(f"Order {order_id} not found, email not sent")
    except Exception as exc:
        logger.error(f"Failed to send payment confirmation email: {str(exc)}")
        raise self.retry(exc=exc)
