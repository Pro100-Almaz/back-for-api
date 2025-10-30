from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from storages.backends.s3boto3 import S3Boto3Storage


def user_avatar_upload_path(instance, filename):
    return f"avatars/user_{instance.user.id}/{filename}"

avatar_storage = S3Boto3Storage()


class User(AbstractUser):
    """
    Custom User model with role-based permissions.
    
    Roles:
    - CLIENT: Browse content, view history, submit feedback
    - TOOL_CREATOR: Manage API keys, track usage/revenue, receive payouts
    - ADMIN: Full access: manage users, payouts, refunds, support, and site content
    """

    class Role(models.TextChoices):
        CLIENT = 'CLIENT', _('Client')
        TOOL_CREATOR = 'TOOL_CREATOR', _('Tool Creator')
        ADMIN = 'ADMIN', _('Admin')

    # Basic fields
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CLIENT,
        verbose_name=_('role')
    )

    # Profile fields
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    company_name = models.CharField(max_length=100, blank=True, null=True)
    avatar = models.ImageField(upload_to=user_avatar_upload_path, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    # Points system for clients
    points_balance = models.PositiveIntegerField(default=0, help_text=_('Available points for usage'))

    # Tool creator specific fields
    api_key = models.CharField(max_length=255, blank=True, null=True, help_text=_('API key for tool creators'))
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text=_('Total revenue earned'))
    total_payouts = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text=_('Total payouts received'))

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Use email as username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-created_at']

    def __str__(self):
        return self.email

    @property
    def is_client(self):
        return self.role == self.Role.CLIENT

    @property
    def is_tool_creator(self):
        return self.role == self.Role.TOOL_CREATOR

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    def can_browse_content(self):
        """Check if user can browse content (all roles can)"""
        return True

    def can_use_services(self):
        """Check if user can use services (clients need points)"""
        if self.is_client:
            return self.points_balance > 0
        return True

    def can_submit_content(self):
        """Check if user can submit content"""
        return self.is_tool_creator or self.is_admin

    def can_manage_api_keys(self):
        """Check if user can manage API keys"""
        return self.is_tool_creator or self.is_admin

    def can_track_usage_revenue(self):
        """Check if user can track usage and revenue"""
        return self.is_tool_creator or self.is_admin

    def can_receive_payouts(self):
        """Check if user can receive payouts"""
        return self.is_tool_creator

    def can_manage_users(self):
        """Check if user can manage other users"""
        return self.is_admin

    def can_manage_content(self):
        """Check if user can manage content"""
        return self.is_admin

    def can_manage_payouts(self):
        """Check if user can manage payouts"""
        return self.is_admin

    def can_manage_refunds(self):
        """Check if user can manage refunds"""
        return self.is_admin

    def can_manage_support(self):
        """Check if user can manage support"""
        return self.is_admin

    def can_manage_site_content(self):
        """Check if user can manage site content"""
        return self.is_admin



class UserProfile(models.Model):
    """Extended user profile for additional information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(storage = avatar_storage, upload_to=user_avatar_upload_path, blank=True, null=True)

    # Additional profile fields
    website = models.URLField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    skills = models.JSONField(default=list, blank=True, help_text=_('List of user skills'))

    # Preferences
    email_notifications = models.BooleanField(default=True)
    marketing_emails = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')

    def __str__(self):
        return f"{self.user.email} Profile"