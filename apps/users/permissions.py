from rest_framework import permissions


class IsStaffUser(permissions.BasePermission):
    """
    Permission to only allow staff users to access a view
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff
    
    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_authenticated and request.user.is_staff 