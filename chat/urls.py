from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TopicViewSet, ChatThreadViewSet, ChatMessageListView


router = DefaultRouter()
router.register(r'topics', TopicViewSet, basename='topic')
router.register(r'threads', ChatThreadViewSet, basename='thread')


urlpatterns = [
    path('', include(router.urls)),
    path('threads/<uuid:thread_id>/messages/', ChatMessageListView.as_view(), name='thread-messages'),
]


