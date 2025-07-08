from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ToolViewSet, ToolUsageViewSet, ToolFeedbackViewSet, ToolApiKeyViewSet
)

router = DefaultRouter()
router.register(r'tools', ToolViewSet)
router.register(r'usage', ToolUsageViewSet, basename='tool-usage')
router.register(r'feedback', ToolFeedbackViewSet, basename='tool-feedback')
router.register(r'api-keys', ToolApiKeyViewSet, basename='tool-api-key')

urlpatterns = [
    path('', include(router.urls)),
] 