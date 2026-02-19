"""
Tests for workspace models and functionality.
"""

import pytest
from django.contrib.auth import get_user_model
from apps.workspaces.models import Workspace, Member, Invite
from datetime import timedelta
from django.utils import timezone

User = get_user_model()


@pytest.fixture
def test_user(db):
    """Create a test user."""
    return User.objects.create_user(
        email='owner@example.com',
        password='TestPass123!',
        first_name='Owner',
        last_name='User'
    )


@pytest.fixture
def test_workspace(db, test_user):
    """Create a test workspace."""
    return Workspace.objects.create(
        name='Test Workspace',
        description='A test workspace',
        owner=test_user
    )


@pytest.mark.django_db
class TestWorkspace:
    """Tests for Workspace model."""
    
    def test_create_workspace(self, test_user):
        """Test workspace creation."""
        workspace = Workspace.objects.create(
            name='My Workspace',
            owner=test_user
        )
        
        assert workspace.name == 'My Workspace'
        assert workspace.slug == 'my-workspace'
        assert workspace.owner == test_user
    
    def test_slug_auto_generation(self, test_user):
        """Test that slug is auto-generated from name."""
        workspace = Workspace.objects.create(
            name='Test Workspace 123',
            owner=test_user
        )
        
        assert workspace.slug == 'test-workspace-123'
    
    def test_add_member(self, test_workspace):
        """Test adding member to workspace."""
        user = User.objects.create_user(
            email='member@example.com',
            password='TestPass123!',
            first_name='Member',
            last_name='User'
        )
        
        member = test_workspace.add_member(user, role='member')
        
        assert member.workspace == test_workspace
        assert member.user == user
        assert member.role == 'member'
    
    def test_is_member(self, test_workspace, test_user):
        """Test checking if user is member."""
        # Owner should not be in members by default
        assert not test_workspace.is_member(test_user)
        
        # Add as member
        test_workspace.add_member(test_user)
        assert test_workspace.is_member(test_user)


@pytest.mark.django_db
class TestMember:
    """Tests for Member model."""
    
    def test_member_permissions(self, test_workspace, test_user):
        """Test role-based permissions."""
        member = Member.objects.create(
            workspace=test_workspace,
            user=test_user,
            role='admin'
        )
        
        # Admin should have edit permissions
        assert member.has_permission('workspace.edit')
        assert member.has_permission('document.create')
        
        # But not ownership transfer
        assert not member.has_permission('workspace.transfer_ownership')
    
    def test_guest_permissions(self, test_workspace, test_user):
        """Test guest has limited permissions."""
        member = Member.objects.create(
            workspace=test_workspace,
            user=test_user,
            role='guest'
        )
        
        # Guest should only have view permissions
        assert member.has_permission('document.view')
        assert not member.has_permission('document.edit')


@pytest.mark.django_db
class TestInvite:
    """Tests for Invite model."""
    
    def test_create_invite(self, test_workspace, test_user):
        """Test creating an invitation."""
        invite = Invite.objects.create(
            workspace=test_workspace,
            email='invitee@example.com',
            role='member',
            invited_by=test_user,
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        assert invite.token is not None
        assert len(invite.token) > 0
        assert invite.is_valid()
    
    def test_accept_invite(self, test_workspace, test_user):
        """Test accepting an invitation."""
        invite = Invite.objects.create(
            workspace=test_workspace,
            email='invitee@example.com',
            role='member',
            invited_by=test_user,
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        invitee = User.objects.create_user(
            email='invitee@example.com',
            password='TestPass123!',
            first_name='Invitee',
            last_name='User'
        )
        
        member = invite.accept(invitee)
        
        assert member.workspace == test_workspace
        assert member.user == invitee
        assert member.role == 'member'
        assert invite.accepted_at is not None
        assert invite.accepted_by == invitee
