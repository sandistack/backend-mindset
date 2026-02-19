"""
Business logic services for authentication.
"""

from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import uuid
from .models import EmailVerificationToken, PasswordResetToken


class AuthService:
    """
    Service class for authentication-related business logic.
    """
    
    @staticmethod
    def send_verification_email(user, request=None):
        """
        Send email verification link to user.
        """
        # Create verification token
        token = EmailVerificationToken.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        # Build verification URL
        base_url = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'http://localhost:3000'
        verification_url = f"{base_url}/verify-email/{token.token}"
        
        # Send email
        subject = 'Verify Your Email'
        message = f"""
        Hi {user.first_name},
        
        Thank you for registering! Please verify your email address by clicking the link below:
        
        {verification_url}
        
        This link will expire in 7 days.
        
        If you didn't create an account, please ignore this email.
        
        Best regards,
        The Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        return token
    
    @staticmethod
    def send_password_reset_email(user, request=None):
        """
        Send password reset link to user.
        """
        # Create reset token
        token = PasswordResetToken.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(hours=24),
            ip_address=get_client_ip(request) if request else None,
            user_agent=request.META.get('HTTP_USER_AGENT', '') if request else ''
        )
        
        # Build reset URL
        base_url = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'http://localhost:3000'
        reset_url = f"{base_url}/reset-password/{token.token}"
        
        # Send email
        subject = 'Password Reset Request'
        message = f"""
        Hi {user.first_name},
        
        We received a request to reset your password. Click the link below to reset it:
        
        {reset_url}
        
        This link will expire in 24 hours.
        
        If you didn't request a password reset, please ignore this email or contact support if you have concerns.
        
        Best regards,
        The Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        return token
    
    @staticmethod
    def cleanup_expired_tokens():
        """
        Cleanup expired verification and reset tokens.
        This should be run periodically via Celery.
        """
        now = timezone.now()
        
        # Delete expired verification tokens
        expired_verification = EmailVerificationToken.objects.filter(
            expires_at__lt=now
        )
        count_verification = expired_verification.count()
        expired_verification.delete()
        
        # Delete expired reset tokens
        expired_reset = PasswordResetToken.objects.filter(
            expires_at__lt=now
        )
        count_reset = expired_reset.count()
        expired_reset.delete()
        
        return {
            'verification_tokens_deleted': count_verification,
            'reset_tokens_deleted': count_reset
        }


def get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
