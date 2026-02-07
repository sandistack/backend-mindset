"""
Audit logging utility

Maintainable: Centralized audit logic
Reusable: Dipanggil dari semua services
Predictable: Consistent logging format
"""

from apps.core.models import AuditLog
import logging

logger = logging.getLogger('apps')


def log_activity(user, action, feature, description, request=None, status='SUCCESS'):
    """
    Log user activity to database
    
    Args:
        user: User instance
        action: 'CREATE', 'UPDATE', 'DELETE', 'ERROR'
        feature: 'task', 'user', etc.
        description: Human-readable description
        request: HTTP request object (optional)
        status: 'SUCCESS' or 'FAILED'
    
    Returns:
        AuditLog instance
    
    Example:
        log_activity(
            user=request.user,
            action='CREATE',
            feature='task',
            description='Created task: Buy milk',
            request=request
        )
    """
    
    # Extract IP from request
    ip_address = None
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')
    
    # Save to database
    audit_log = AuditLog.objects.create(
        user=user,
        action=action,
        feature=feature,
        description=description,
        ip_address=ip_address,
        status=status
    )
    
    # Also log to file
    log_message = f"{action} | {feature} | {description} | User: {user.username if user else 'Anonymous'}"
    
    if status == 'SUCCESS':
        logger.info(log_message)
    else:
        logger.error(log_message)
    
    return audit_log


def get_client_ip(request):
    """
    Helper to get client IP from request
    
    Reusable: DRY principle
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip