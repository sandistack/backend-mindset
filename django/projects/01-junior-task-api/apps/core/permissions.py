from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """
    Object-level permission to only allow owners of an object to access it.
    Assumes the model instance has a `user` attribute.
    """
    
    def has_object_permission(self, request, view, obj):
        # Check if the object has a user attribute and if it matches the request user
        return hasattr(obj, 'user') and obj.user == request.user
