"""
Celery tasks for authentication.
"""

from celery import shared_task
from django.utils import timezone
from .services import AuthService
import logging

logger = logging.getLogger(__name__)


@shared_task
def cleanup_expired_tokens():
    """
    Cleanup expired verification and password reset tokens.
    Runs daily via Celery Beat.
    """
    logger.info("Starting token cleanup task")
    result = AuthService.cleanup_expired_tokens()
    logger.info(f"Token cleanup completed: {result}")
    return result


@shared_task
def send_verification_email_task(user_id):
    """
    Send verification email asynchronously.
    """
    from .models import User
    
    try:
        user = User.objects.get(id=user_id)
        AuthService.send_verification_email(user)
        logger.info(f"Verification email sent to {user.email}")
        return {'success': True, 'user': user.email}
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for verification email")
        return {'success': False, 'error': 'User not found'}


@shared_task
def send_password_reset_email_task(user_id):
    """
    Send password reset email asynchronously.
    """
    from .models import User
    
    try:
        user = User.objects.get(id=user_id)
        AuthService.send_password_reset_email(user)
        logger.info(f"Password reset email sent to {user.email}")
        return {'success': True, 'user': user.email}
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for password reset email")
        return {'success': False, 'error': 'User not found'}
