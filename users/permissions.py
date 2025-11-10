from django.contrib.auth import get_user_model
from rest_framework import permissions

User = get_user_model()


class IsClient(permissions.BasePermission):
    """Permission to check if user is a client"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_client


class IsToolCreator(permissions.BasePermission):
    """Permission to check if user is a tool creator"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_tool_creator


class IsAdmin(permissions.BasePermission):
    """Permission to check if user is an admin"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin


class IsToolCreatorOrAdmin(permissions.BasePermission):
    """Permission to check if user is a tool creator or admin"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_tool_creator or request.user.is_admin
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """Permission to check if user is the owner or admin"""
    
    def has_object_permission(self, request, view, obj):
        # Admin can access everything
        if request.user.is_admin:
            return True
        
        # Check if user is the owner
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return False


class CanBrowseContent(permissions.BasePermission):
    """Permission to check if user can browse content"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.can_browse_content()


class CanUseServices(permissions.BasePermission):
    """Permission to check if user can use services"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.can_use_services()


class CanSubmitContent(permissions.BasePermission):
    """Permission to check if user can submit content"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.can_submit_content()


class CanManageApiKeys(permissions.BasePermission):
    """Permission to check if user can manage API keys"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.can_manage_api_keys()


class CanTrackUsageRevenue(permissions.BasePermission):
    """Permission to check if user can track usage and revenue"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.can_track_usage_revenue()


class CanReceivePayouts(permissions.BasePermission):
    """Permission to check if user can receive payouts"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.can_receive_payouts()


class CanManageUsers(permissions.BasePermission):
    """Permission to check if user can manage users"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.can_manage_users()


class CanManageContent(permissions.BasePermission):
    """Permission to check if user can manage content"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.can_manage_content()


class CanManagePayouts(permissions.BasePermission):
    """Permission to check if user can manage payouts"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.can_manage_payouts()


class CanManageRefunds(permissions.BasePermission):
    """Permission to check if user can manage refunds"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.can_manage_refunds()


class CanManageSupport(permissions.BasePermission):
    """Permission to check if user can manage support"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.can_manage_support()


class CanManageSiteContent(permissions.BasePermission):
    """Permission to check if user can manage site content"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.can_manage_site_content() 