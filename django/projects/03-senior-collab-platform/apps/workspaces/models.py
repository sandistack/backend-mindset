"""
Workspace models for collaboration platform.
Workspaces are the main organizational unit where teams collaborate.
"""

from django.db import models
from django.utils.text import slugify
from django.conf import settings
from apps.core.models import BaseModel, SoftDeleteModel
import secrets


class Workspace(SoftDeleteModel):
    """
    Workspace is the main container for team collaboration.
    Contains members, documents, channels, and other resources.
    """
    
    name = models.CharField(
        max_length=100,
        help_text="Workspace name"
    )
    slug = models.SlugField(
        unique=True,
        max_length=100,
        help_text="URL-friendly workspace identifier"
    )
    description = models.TextField(
        blank=True,
        help_text="Workspace description"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_workspaces',
        help_text="Workspace owner"
    )
    logo = models.ImageField(
        upload_to='workspaces/logos/',
        blank=True,
        null=True,
        help_text="Workspace logo"
    )
    
    # Settings
    settings = models.JSONField(
        default=dict,
        help_text="Workspace settings and preferences"
    )
    
    # Features
    features_enabled = models.JSONField(
        default=list,
        help_text="List of enabled features"
    )
    
    # Limits
    max_members = models.IntegerField(
        default=50,
        help_text="Maximum number of members allowed"
    )
    storage_limit = models.BigIntegerField(
        default=10737418240,  # 10GB in bytes
        help_text="Storage limit in bytes"
    )
    storage_used = models.BigIntegerField(
        default=0,
        help_text="Storage currently used in bytes"
    )
    
    class Meta:
        db_table = 'workspaces'
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['owner']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
            # Ensure uniqueness
            original_slug = self.slug
            counter = 1
            while Workspace.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        
        # Initialize default settings
        if not self.settings:
            self.settings = {
                'require_email_verification': True,
                'allow_member_invites': True,
                'default_member_role': 'member',
                'public_workspace': False,
            }
        
        super().save(*args, **kwargs)
    
    def add_member(self, user, role='member'):
        """Add a user to the workspace."""
        member, created = Member.objects.get_or_create(
            workspace=self,
            user=user,
            defaults={'role': role}
        )
        return member
    
    def remove_member(self, user):
        """Remove a user from the workspace."""
        Member.objects.filter(workspace=self, user=user).delete()
    
    def is_member(self, user):
        """Check if user is a member of this workspace."""
        return self.members.filter(user=user).exists()
    
    def get_member_role(self, user):
        """Get the role of a user in this workspace."""
        try:
            member = self.members.get(user=user)
            return member.role
        except Member.DoesNotExist:
            return None


class Member(BaseModel):
    """
    Workspace member with role-based permissions.
    """
    
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Administrator'),
        ('member', 'Member'),
        ('guest', 'Guest'),
    ]
    
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='members'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='member',
        help_text="Member's role in the workspace"
    )
    
    # Custom permissions
    custom_permissions = models.JSONField(
        default=dict,
        help_text="Custom permissions for this member"
    )
    
    # Activity tracking
    joined_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the member joined"
    )
    last_seen = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last activity in this workspace"
    )
    
    class Meta:
        db_table = 'workspace_members'
        unique_together = ['workspace', 'user']
        ordering = ['joined_at']
        indexes = [
            models.Index(fields=['workspace', 'user']),
            models.Index(fields=['workspace', 'role']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.workspace.name} ({self.role})"
    
    def has_permission(self, permission):
        """
        Check if member has a specific permission.
        
        Permission hierarchy:
        - owner: all permissions
        - admin: most permissions except ownership transfer
        - member: basic permissions
        - guest: read-only access
        """
        role_permissions = {
            'owner': ['*'],  # All permissions
            'admin': [
                'workspace.edit',
                'workspace.delete',
                'member.invite',
                'member.remove',
                'member.edit_role',
                'document.create',
                'document.edit',
                'document.delete',
                'channel.create',
                'channel.edit',
                'channel.delete',
            ],
            'member': [
                'document.create',
                'document.edit',
                'document.delete_own',
                'channel.create',
                'channel.edit_own',
                'member.invite',
            ],
            'guest': [
                'document.view',
                'channel.view',
            ],
        }
        
        # Check custom permissions first
        if permission in self.custom_permissions:
            return self.custom_permissions[permission]
        
        # Check role-based permissions
        permissions = role_permissions.get(self.role, [])
        return '*' in permissions or permission in permissions


class Invite(BaseModel):
    """
    Workspace invitation for new members.
    """
    
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='invites'
    )
    email = models.EmailField(
        help_text="Email of the person being invited"
    )
    role = models.CharField(
        max_length=20,
        choices=Member.ROLE_CHOICES,
        default='member',
        help_text="Role to assign when invitation is accepted"
    )
    token = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique invitation token"
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_invites',
        help_text="User who sent the invitation"
    )
    expires_at = models.DateTimeField(
        help_text="When the invitation expires"
    )
    accepted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the invitation was accepted"
    )
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accepted_invites',
        help_text="User who accepted the invitation"
    )
    
    # Message from inviter
    message = models.TextField(
        blank=True,
        help_text="Optional message to the invitee"
    )
    
    class Meta:
        db_table = 'workspace_invites'
        unique_together = ['workspace', 'email']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['workspace', 'email']),
        ]
    
    def __str__(self):
        return f"Invite for {self.email} to {self.workspace.name}"
    
    def save(self, *args, **kwargs):
        """Generate token if not provided."""
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """Check if invitation is still valid."""
        from django.utils import timezone
        return (
            not self.accepted_at and
            timezone.now() < self.expires_at
        )
    
    def accept(self, user):
        """Accept the invitation and add user to workspace."""
        from django.utils import timezone
        
        if not self.is_valid():
            raise ValueError("Invitation is no longer valid")
        
        # Add user to workspace
        member = self.workspace.add_member(user, self.role)
        
        # Mark invitation as accepted
        self.accepted_at = timezone.now()
        self.accepted_by = user
        self.save()
        
        return member
