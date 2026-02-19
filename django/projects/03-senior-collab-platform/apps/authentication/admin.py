from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, EmailVerificationToken, PasswordResetToken, RefreshToken, LoginHistory


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for User model."""
    
    list_display = ['email', 'first_name', 'last_name', 'is_active', 'email_verified', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'email_verified', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'display_name', 'avatar', 'bio', 'phone')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'email_verified')}),
        ('Settings', {'fields': ('timezone', 'language', 'notification_preferences')}),
        ('Security', {'fields': ('two_factor_enabled',)}),
        ('Timestamps', {'fields': ('last_login', 'date_joined', 'last_activity')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name'),
        }),
    )


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    """Admin for email verification tokens."""
    
    list_display = ['user', 'token', 'expires_at', 'used', 'created_at']
    list_filter = ['used', 'created_at']
    search_fields = ['user__email']
    readonly_fields = ['token', 'created_at']


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """Admin for password reset tokens."""
    
    list_display = ['user', 'token', 'expires_at', 'used', 'created_at']
    list_filter = ['used', 'created_at']
    search_fields = ['user__email', 'ip_address']
    readonly_fields = ['token', 'created_at']


@admin.register(RefreshToken)
class RefreshTokenAdmin(admin.ModelAdmin):
    """Admin for refresh tokens."""
    
    list_display = ['user', 'jti', 'expires_at', 'revoked', 'created_at']
    list_filter = ['revoked', 'created_at']
    search_fields = ['user__email', 'ip_address']


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    """Admin for login history."""
    
    list_display = ['user', 'ip_address', 'device_name', 'success', 'created_at']
    list_filter = ['success', 'created_at']
    search_fields = ['user__email', 'ip_address']
    readonly_fields = ['created_at']
