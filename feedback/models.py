# feedback/models.py
from django.conf import settings
from django.db import models

class Suggestion(models.Model):
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name        = models.CharField(max_length=255)
    category    = models.CharField(max_length=100)
    description = models.TextField()
    created_at  = models.DateTimeField(auto_now_add=True)


class BugReport(models.Model):
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title       = models.CharField(max_length=255)
    description = models.TextField()
    screenshot  = models.FileField(upload_to='bugs/', null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

class Upvote(models.Model):
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    suggestion = models.ForeignKey(Suggestion, on_delete=models.CASCADE, related_name='upvotes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'suggestion')
