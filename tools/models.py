from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class Tool(models.Model):
    """Model for tools that can be used by clients"""
    
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', _('Draft')
        ACTIVE = 'ACTIVE', _('Active')
        INACTIVE = 'INACTIVE', _('Inactive')
        SUSPENDED = 'SUSPENDED', _('Suspended')
    
    class Category(models.TextChoices):
        AI = 'AI', _('Artificial Intelligence')
        PRODUCTIVITY = 'PRODUCTIVITY', _('Productivity')
        CREATIVE = 'CREATIVE', _('Creative')
        DEVELOPMENT = 'DEVELOPMENT', _('Development')
        BUSINESS = 'BUSINESS', _('Business')
        OTHER = 'OTHER', _('Other')
    
    # Basic information
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    
    # Creator information
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tools')
    
    # Pricing and usage
    points_cost = models.PositiveIntegerField(default=1, help_text=_('Points required to use this tool'))
    api_endpoint = models.URLField(blank=True, null=True, help_text=_('API endpoint for the tool'))
    api_documentation = models.URLField(blank=True, null=True, help_text=_('Documentation URL'))
    
    # Metadata
    tags = models.JSONField(default=list, blank=True, help_text=_('List of tags for the tool'))
    version = models.CharField(max_length=20, default='1.0.0')
    
    # Statistics
    total_uses = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('tool')
        verbose_name_plural = _('tools')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE
    
    def can_be_used_by(self, user):
        """Check if user can use this tool"""
        if not self.is_active:
            return False
        
        if user.is_client:
            return user.points_balance >= self.points_cost
        
        return True


class ToolUsage(models.Model):
    """Model for tracking tool usage"""
    
    tool = models.ForeignKey(Tool, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tool_usages')
    
    # Usage details
    input_data = models.JSONField(blank=True, null=True, help_text=_('Input data sent to the tool'))
    output_data = models.JSONField(blank=True, null=True, help_text=_('Output data received from the tool'))
    points_spent = models.PositiveIntegerField(default=0)
    
    # Metadata
    execution_time = models.DurationField(blank=True, null=True, help_text=_('Time taken to execute'))
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('tool usage')
        verbose_name_plural = _('tool usages')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} used {self.tool.name} at {self.created_at}"


class ToolFeedback(models.Model):
    """Model for tool feedback from users"""
    
    tool = models.ForeignKey(Tool, on_delete=models.CASCADE, related_name='feedbacks')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tool_feedbacks')
    
    # Feedback details
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_('Rating from 1 to 5')
    )
    comment = models.TextField(blank=True, null=True)
    
    # Metadata
    is_public = models.BooleanField(default=True, help_text=_('Whether this feedback is visible to others'))
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('tool feedback')
        verbose_name_plural = _('tool feedbacks')
        ordering = ['-created_at']
        unique_together = ['tool', 'user']  # One feedback per user per tool
    
    def __str__(self):
        return f"{self.user.email} rated {self.tool.name} {self.rating}/5"


class ToolApiKey(models.Model):
    """Model for managing API keys for tools"""
    
    tool = models.ForeignKey(Tool, on_delete=models.CASCADE, related_name='api_keys')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tool_api_keys')
    
    # API key details
    key_name = models.CharField(max_length=100)
    api_key = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    
    # Usage limits
    daily_limit = models.PositiveIntegerField(default=1000, help_text=_('Daily API call limit'))
    monthly_limit = models.PositiveIntegerField(default=30000, help_text=_('Monthly API call limit'))
    
    # Statistics
    daily_usage = models.PositiveIntegerField(default=0)
    monthly_usage = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = _('tool API key')
        verbose_name_plural = _('tool API keys')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.key_name} for {self.tool.name}"
    
    def can_make_request(self):
        """Check if API key can make a request"""
        if not self.is_active:
            return False
        
        # Check daily limit
        if self.daily_usage >= self.daily_limit:
            return False
        
        # Check monthly limit
        if self.monthly_usage >= self.monthly_limit:
            return False
        
        return True 