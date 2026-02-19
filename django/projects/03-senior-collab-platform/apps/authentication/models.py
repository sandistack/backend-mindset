"""
Custom User model for Senior Collaboration Platform.
Uses email as the primary authentication method instead of username.
"""

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from apps.core.models import BaseModel
import uuid


class UserManager(BaseUserManager):
    """
    Custom manager for User model.
    Handles user creation with email-based authentication.
    """
    
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and return a regular user with email and password.
        """
        if not email:
            raise ValueError('Email address is required')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and return a superuser with email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('email_verified', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    """
    Custom User model with email-based authentication.
    
    Features:
    - Email-based authentication (no username)
    - Email verification
    - Profile information
    - Two-factor authentication support
    - Account status tracking
    """
    
    # Authentication fields
    email = models.EmailField(
        unique=True,
        db_index=True,
        help_text="Email address used for authentication"
    )
    
    # Profile fields
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    display_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Public display name"
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True
    )
    bio = models.TextField(
        max_length=500,
        blank=True,
        help_text="Short bio or description"
    )
    
    # Contact information
    phone_validator = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone = models.CharField(
        validators=[phone_validator],
        max_length=17,
        blank=True,
        help_text="Contact phone number"
    )
    
    # Account status
    is_active = models.BooleanField(
        default=True,
        help_text="Designates whether this user account is active"
    )
    is_staff = models.BooleanField(
        default=False,
        help_text="Designates whether the user can log into admin site"
    )
    email_verified = models.BooleanField(
        default=False,
        help_text="Designates whether the user has verified their email"
    )
    
    # Two-factor authentication
    two_factor_enabled = models.BooleanField(
        default=False,
        help_text="Designates whether 2FA is enabled"
    )
    two_factor_secret = models.CharField(
        max_length=32,
        blank=True,
        help_text="Secret key for 2FA"
    )
    
    # Activity tracking
    last_login = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last login timestamp"
    )
    date_joined = models.DateTimeField(
        default=timezone.now,
        help_text="Date when user joined"
    )
    last_activity = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last activity timestamp"
    )
    
    # Settings
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        help_text="User's preferred timezone"
    )
    language = models.CharField(
        max_length=10,
        default='en',
        help_text="User's preferred language"
    )
    notification_preferences = models.JSONField(
        default=dict,
        help_text="User notification preferences"
    )
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        db_table = 'users'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active', 'email_verified']),
        ]
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return the user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.email
    
    def get_short_name(self):
        """Return the user's short name."""
        return self.first_name or self.email.split('@')[0]
    
    @property
    def full_name(self):
        """Property for full name."""
        return self.get_full_name()
    
    def update_last_activity(self):
        """Update the last activity timestamp."""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])


class EmailVerificationToken(BaseModel):
    """
    Token for email verification.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='verification_tokens'
    )
    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'email_verification_tokens'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Verification token for {self.user.email}"
    
    def is_valid(self):
        """Check if token is still valid."""
        return not self.used and timezone.now() < self.expires_at


class PasswordResetToken(BaseModel):
    """
    Token for password reset.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens'
    )
    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        db_table = 'password_reset_tokens'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Password reset token for {self.user.email}"
    
    def is_valid(self):
        """Check if token is still valid."""
        return not self.used and timezone.now() < self.expires_at


class RefreshToken(BaseModel):
    """
    Store refresh tokens for JWT authentication.
    Allows for token revocation and tracking.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='refresh_tokens'
    )
    token = models.CharField(max_length=500, unique=True)
    jti = models.UUIDField(unique=True)  # JWT ID
    expires_at = models.DateTimeField()
    revoked = models.BooleanField(default=False)
    revoked_at = models.DateTimeField(null=True, blank=True)
    
    # Device tracking
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_name = models.CharField(max_length=100, blank=True)
    
    class Meta:
        db_table = 'refresh_tokens'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'revoked']),
            models.Index(fields=['jti']),
        ]
    
    def __str__(self):
        return f"Refresh token for {self.user.email}"
    
    def is_valid(self):
        """Check if token is still valid."""
        return not self.revoked and timezone.now() < self.expires_at
    
    def revoke(self):
        """Revoke this refresh token."""
        self.revoked = True
        self.revoked_at = timezone.now()
        self.save()


class LoginHistory(BaseModel):
    """
    Track user login history for security purposes.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='login_history'
    )
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_name = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=200, blank=True)
    success = models.BooleanField(default=True)
    failure_reason = models.CharField(max_length=200, blank=True)
    
    class Meta:
        db_table = 'login_history'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"Login by {self.user.email} at {self.created_at}"
