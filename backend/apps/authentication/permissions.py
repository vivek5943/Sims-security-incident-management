"""
MOD-01: RBAC Permission Classes
Enforces the granular role-based access matrix (Section 8.1):
  - Security Analyst: incident entry, mutation, note appending
  - Security Manager: assignment, escalation, analytics, reports
  - System Administrator: identity management, RBAC config, audit
"""
from rest_framework.permissions import BasePermission
from apps.authentication.models import Role


class IsAnalystOrAbove(BasePermission):
    """Allow access to Security Analysts, Managers, and Admins."""
    message = 'Access denied. Security Analyst role or above required.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role is not None
        )


class IsManagerOrAbove(BasePermission):
    """Allow access only to Security Managers and System Administrators."""
    message = 'Access denied. Security Manager role or above required.'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role_name in [Role.MANAGER, Role.ADMIN]


class IsSystemAdmin(BasePermission):
    """Allow access only to System Administrators."""
    message = 'Access denied. System Administrator role required.'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role_name == Role.ADMIN


class IsOwnerOrManagerOrAdmin(BasePermission):
    """Allow access to the owning analyst, managers, or admins."""
    message = 'Access denied. Insufficient privileges for this resource.'

    def has_object_permission(self, request, view, obj):
        if request.user.role_name in [Role.MANAGER, Role.ADMIN]:
            return True
        # For incidents: analyst can access their own created incidents
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        # For notes: analyst can access their own notes
        if hasattr(obj, 'analyst'):
            return obj.analyst == request.user
        return False
