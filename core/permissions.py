"""
Centralized permission classes for VivaCRM v2.

This module defines all permission classes used across the application,
ensuring consistent access control and helping maintain DRY principles.
"""
from rest_framework import permissions
from django.utils import timezone
from typing import List, Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)


class IsAdminUser(permissions.IsAdminUser):
    """
    Permission class that allows access only to admin users.
    """
    message = "Only admin users can perform this action."


class IsStaffUser(permissions.BasePermission):
    """
    Permission class that allows access only to staff users.
    """
    message = "Only staff users can perform this action."
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)


class IsAdminUserOrReadOnly(permissions.BasePermission):
    """
    Permission class that allows read access to all users,
    but only allows write access to admin users.
    """
    message = "Only admin users can modify data."
    
    def has_permission(self, request, view):
        # Allow GET, HEAD, OPTIONS requests for all users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for admin users
        return bool(request.user and request.user.is_superuser)


class IsStaffUserOrReadOnly(permissions.BasePermission):
    """
    Permission class that allows read access to all users,
    but only allows write access to staff users.
    """
    message = "Only staff users can modify data."
    
    def has_permission(self, request, view):
        # Allow GET, HEAD, OPTIONS requests for all users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for staff users
        return bool(request.user and request.user.is_staff)


class IsOwnerOrStaff(permissions.BasePermission):
    """
    Permission class that allows access to the owner of an object
    or to staff members.
    """
    message = "You must be the owner of this object or a staff member."
    
    def has_object_permission(self, request, view, obj):
        # Staff members can access any object
        if request.user.is_staff:
            return True
        
        # Check if object has an owner field
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        
        # Check if object has a created_by field
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        # Check if object has a user field
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # If not owner-related fields found, deny permission
        return False


class IsUserOrAdmin(permissions.BasePermission):
    """
    Permission class that allows access to the user themselves
    or to admin users.
    """
    message = "You can only view your own profile or you must be an admin."
    
    def has_object_permission(self, request, view, obj):
        # Allow admin users
        if request.user.is_superuser:
            return True
        
        # Allow if the user is accessing their own profile
        return obj == request.user


class IsSuperUser(permissions.BasePermission):
    """
    Permission class that allows access only to superusers.
    """
    message = "Only superusers can perform this action."
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)


class CanExportData(permissions.BasePermission):
    """
    Permission class that allows data export operations 
    for staff users or users with specific permissions.
    """
    message = "You don't have permission to export data."
    
    def has_permission(self, request, view):
        # Allow staff users
        if request.user.is_staff:
            return True
        
        # Allow users with specific export permission
        if request.user.has_perm('core.can_export_data'):
            # Log the export operation
            logger.info(f"User {request.user.username} ({request.user.email}) "
                       f"initiated data export at {timezone.now()}")
            return True
        
        return False


class CanImportData(permissions.BasePermission):
    """
    Permission class that allows data import operations 
    for staff users only.
    """
    message = "Only staff users can import data."
    
    def has_permission(self, request, view):
        # Allow staff users
        if request.user.is_staff:
            # Log the import operation
            logger.info(f"User {request.user.username} ({request.user.email}) "
                       f"initiated data import at {timezone.now()}")
            return True
        
        return False


class ReadOnly(permissions.BasePermission):
    """
    Permission class that allows only read operations.
    """
    message = "This endpoint is read-only."
    
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class CanAccessFinancialData(permissions.BasePermission):
    """
    Permission class that allows access to financial data
    for staff users or users with specific permissions.
    """
    message = "You don't have permission to access financial data."
    
    def has_permission(self, request, view):
        # Allow staff users
        if request.user.is_staff:
            return True
        
        # Allow users with specific permission
        return request.user.has_perm('core.can_access_financial_data')


class CanManageUsers(permissions.BasePermission):
    """
    Permission class that allows user management
    for admin users or users with specific permissions.
    """
    message = "You don't have permission to manage users."
    
    def has_permission(self, request, view):
        # Allow admin users
        if request.user.is_superuser:
            return True
        
        # Allow staff with specific permission
        if request.user.is_staff and request.user.has_perm('core.can_manage_users'):
            return True
        
        return False