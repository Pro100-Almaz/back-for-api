from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Suggestion, BugReport, Upvote

# Inline for Upvotes inside Suggestion admin
class UpvoteInline(admin.TabularInline):
    model = Upvote
    extra = 0              # no “blank” extra rows
    readonly_fields = ('user', 'created_at')
    can_delete = False     # if you don’t want deletes here


@admin.register(Suggestion)
class SuggestionAdmin(admin.ModelAdmin):
    list_display    = ('id', 'user', 'name', 'category', 'created_at')
    list_filter     = ('category', 'created_at', 'user')
    search_fields   = ('name', 'category', 'description', 'user__username')
    readonly_fields = ('created_at',)
    inlines         = (UpvoteInline,)


@admin.register(BugReport)
class BugReportAdmin(admin.ModelAdmin):
    list_display    = ('id', 'user', 'title', 'created_at')
    list_filter     = ('created_at', 'user')
    search_fields   = ('title', 'description', 'user__username')
    readonly_fields = ('created_at',)
    # show the screenshot thumbnail in detail view (optional)
    def screenshot_preview(self, obj):
        if obj.screenshot:
            return mark_safe(f'<img src="{obj.screenshot.url}" style="max-height:200px;"/>')
        return "-"
    readonly_fields += ('screenshot_preview',)


@admin.register(Upvote)
class UpvoteAdmin(admin.ModelAdmin):
    list_display    = ('id', 'user', 'suggestion', 'created_at')
    list_filter     = ('created_at', 'user')
    search_fields   = ('user__username', 'suggestion__name')
    readonly_fields = ('created_at',)
