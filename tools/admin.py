from django.contrib import admin
from .models import Tool, ToolUsage, ToolFeedback, ToolApiKey


@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    list_display = ('name', 'creator', 'category', 'status', 'points_cost', 'total_uses', 'average_rating', 'created_at')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('name', 'description', 'creator__email')
    readonly_fields = ('total_uses', 'total_revenue', 'average_rating', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'status', 'creator')
        }),
        ('Pricing & Usage', {
            'fields': ('points_cost', 'api_endpoint', 'api_documentation')
        }),
        ('Metadata', {
            'fields': ('tags', 'version')
        }),
        ('Statistics', {
            'fields': ('total_uses', 'total_revenue', 'average_rating'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ToolUsage)
class ToolUsageAdmin(admin.ModelAdmin):
    list_display = ('tool', 'user', 'points_spent', 'success', 'created_at')
    list_filter = ('success', 'created_at', 'tool__category')
    search_fields = ('tool__name', 'user__email')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Usage Details', {
            'fields': ('tool', 'user', 'points_spent')
        }),
        ('Data', {
            'fields': ('input_data', 'output_data'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('execution_time', 'success', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ToolFeedback)
class ToolFeedbackAdmin(admin.ModelAdmin):
    list_display = ('tool', 'user', 'rating', 'is_public', 'created_at')
    list_filter = ('rating', 'is_public', 'created_at')
    search_fields = ('tool__name', 'user__email', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Feedback Details', {
            'fields': ('tool', 'user', 'rating', 'comment', 'is_public')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ToolApiKey)
class ToolApiKeyAdmin(admin.ModelAdmin):
    list_display = ('tool', 'user', 'key_name', 'is_active', 'daily_usage', 'monthly_usage', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('tool__name', 'user__email', 'key_name')
    readonly_fields = ('api_key', 'daily_usage', 'monthly_usage', 'created_at', 'last_used')
    
    fieldsets = (
        ('API Key Details', {
            'fields': ('tool', 'user', 'key_name', 'api_key', 'is_active')
        }),
        ('Usage Limits', {
            'fields': ('daily_limit', 'monthly_limit')
        }),
        ('Statistics', {
            'fields': ('daily_usage', 'monthly_usage', 'last_used'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    ) 