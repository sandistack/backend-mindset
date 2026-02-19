"""
Signal handlers for authentication app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for post-save User model.
    """
    if created:
        # User was just created
        logger.info(f"New user created: {instance.email}")
        
        # Set display name if not provided
        if not instance.display_name:
            instance.display_name = instance.get_short_name()
            instance.save(update_fields=['display_name'])
        
        # Initialize notification preferences if not set
        if not instance.notification_preferences:
            instance.notification_preferences = {
                'email': {
                    'mentions': True,
                    'comments': True,
                    'updates': True,
                    'digest': True,
                },
                'push': {
                    'mentions': True,
                    'comments': True,
                    'updates': False,
                },
                'in_app': {
                    'all': True,
                }
            }
            instance.save(update_fields=['notification_preferences'])
