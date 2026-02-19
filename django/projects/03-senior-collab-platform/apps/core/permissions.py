"""
Core permissions for role-based access control.
"""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only allowed to owner
        return obj.owner == request.user


class IsWorkspaceMember(permissions.BasePermission):
    """
    Permission to check if user is a member of the workspace.
    """
    
    def has_object_permission(self, request, view, obj):
        # Check if user is a member of the workspace
        if hasattr(obj, 'workspace'):
            workspace = obj.workspace
        else:
            workspace = obj
        
        return workspace.members.filter(user=request.user).exists()


class IsWorkspaceAdmin(permissions.BasePermission):
    """
    Permission to check if user is an admin or owner of the workspace.
    """
    
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'workspace'):
            workspace = obj.workspace
        else:
            workspace = obj
        
        return workspace.members.filter(
            user=request.user,
            role__in=['owner', 'admin']
        ).exists()


class IsWorkspaceOwner(permissions.BasePermission):
    """
    Permission to check if user is the owner of the workspace.
    """
    
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'workspace'):
            workspace = obj.workspace
        else:
            workspace = obj
        
        return workspace.owner == request.user
