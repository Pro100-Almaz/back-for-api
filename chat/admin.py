from django.contrib import admin
from .models import Topic, ChatThread, ChatMessage


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'title', 'is_active', 'updated_at']
    search_fields = ['title', 'user__email']
    list_filter = ['is_active', 'created_at']
    ordering = ['-updated_at']


@admin.register(ChatThread)
class ChatThreadAdmin(admin.ModelAdmin):
    list_display = ['id', 'topic', 'title', 'is_archived', 'updated_at']
    search_fields = ['title', 'topic__title', 'topic__user__email']
    list_filter = ['is_archived']
    ordering = ['-updated_at']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'thread', 'role', 'is_visible', 'created_at']
    search_fields = ['content', 'thread__title', 'thread__topic__title', 'thread__topic__user__email']
    list_filter = ['role', 'is_visible', 'created_at']
    ordering = ['-created_at']


