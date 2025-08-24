from rest_framework import serializers
from .models import Topic, ChatThread, ChatMessage


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ['id', 'title', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ChatThreadSerializer(serializers.ModelSerializer):
    topic = serializers.PrimaryKeyRelatedField(queryset=Topic.objects.all())

    class Meta:
        model = ChatThread
        fields = [
            'id', 'topic', 'title', 'is_archived', 'system_prompt',
            'max_context_messages', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = [
            'id', 'thread', 'role', 'content', 'tokens', 'meta',
            'error', 'is_visible', 'created_at'
        ]
        read_only_fields = ['id', 'tokens', 'meta', 'error', 'is_visible', 'created_at', 'role']


class SendMessageSerializer(serializers.Serializer):
    content = serializers.CharField()
    system_prompt = serializers.CharField(required=False, allow_blank=True)
    max_context_messages = serializers.IntegerField(required=False, min_value=1, max_value=100)


