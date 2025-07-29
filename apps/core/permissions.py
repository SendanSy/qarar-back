"""
Core permission classes for the application.
"""
from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the object.
        return obj.author == request.user or request.user.is_staff


class IsOrganizationMemberOrReadOnly(permissions.BasePermission):
    """
    Permission to only allow organization members to edit content.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Staff can edit anything
        if request.user.is_staff:
            return True
        
        # Check if user is a member of the organization
        if hasattr(obj, 'organization') and obj.organization:
            # This would need to be implemented based on your organization membership model
            # For now, return True for authenticated users
            return request.user.is_authenticated
        
        return False


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow authors of content to edit it.
    """
    
    def has_permission(self, request, view):
        # Allow GET, HEAD or OPTIONS requests for all users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Only allow authenticated users to create content
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Check if the user is the author of the content
        return obj.author == request.user or request.user.is_staff


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Permission that allows read-only access to all users but write access only to staff.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff


class IsOwnerOrStaff(permissions.BasePermission):
    """
    Permission that allows access to owners or staff members.
    """
    
    def has_object_permission(self, request, view, obj):
        # Staff can access everything
        if request.user.is_staff:
            return True
        
        # Check if user is the owner
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'author'):
            return obj.author == request.user
        
        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission that allows read access to all but write access only to admins.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.is_superuser