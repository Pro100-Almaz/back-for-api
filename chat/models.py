from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _


User = get_user_model()


class Topic(models.Model):
    """High-level grouping for conversations per user."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='topics')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('topic')
        verbose_name_plural = _('topics')
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} ({self.user.email})"


class ChatThread(models.Model):
    """Thread within a topic (useful for sub-conversations)."""
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='threads')
    title = models.CharField(max_length=200)
    is_archived = models.BooleanField(default=False)

    # Context management
    system_prompt = models.TextField(blank=True, null=True)
    max_context_messages = models.PositiveIntegerField(default=20, help_text=_('How many prior messages to include'))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('chat thread')
        verbose_name_plural = _('chat threads')
        ordering = ['-updated_at']

    def __str__(self):
        return f"Thread {self.id} - {self.title}"


class ChatMessage(models.Model):
    class Role(models.TextChoices):
        USER = 'user', _('User')
        ASSISTANT = 'assistant', _('Assistant')
        SYSTEM = 'system', _('System')

    thread = models.ForeignKey(ChatThread, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=Role.choices)
    content = models.TextField()
    tokens = models.PositiveIntegerField(default=0)
    meta = models.JSONField(default=dict, blank=True)

    # For delivery/state tracking
    error = models.TextField(blank=True, null=True)
    is_visible = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('chat message')
        verbose_name_plural = _('chat messages')
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role}: {self.content[:30]}..."


