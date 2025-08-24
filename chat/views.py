from django.db.models import Q
from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from .models import Topic, ChatThread, ChatMessage
from .serializers import (
    TopicSerializer, ChatThreadSerializer, ChatMessageSerializer, SendMessageSerializer
)
from .services import GPTService


class TopicViewSet(viewsets.ModelViewSet):
    serializer_class = TopicSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Topic.objects.filter(user=self.request.user, is_active=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ChatThreadViewSet(viewsets.ModelViewSet):
    serializer_class = ChatThreadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatThread.objects.filter(topic__user=self.request.user, topic__is_active=True)

    def perform_create(self, serializer):
        topic = serializer.validated_data['topic']
        if topic.user != self.request.user:
            raise PermissionError('Cannot create thread under a topic you do not own')
        serializer.save()

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        thread = self.get_object()
        qs = ChatMessage.objects.filter(thread=thread, is_visible=True).order_by('created_at')
        page = self.paginate_queryset(qs)
        serializer = ChatMessageSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        thread = self.get_object()
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        system_prompt = serializer.validated_data.get('system_prompt') or thread.system_prompt or ''
        max_ctx = serializer.validated_data.get('max_context_messages') or thread.max_context_messages
        user_content = serializer.validated_data['content']

        # Save the user message first
        user_msg = ChatMessage.objects.create(
            thread=thread,
            role=ChatMessage.Role.USER,
            content=user_content,
        )

        # Build context from last N visible messages
        prior_messages = ChatMessage.objects.filter(thread=thread, is_visible=True).order_by('created_at').values('role', 'content')

        gpt = GPTService()
        try:
            assistant_content, total_tokens, raw = gpt.chat(system_prompt, prior_messages, max_context_messages=max_ctx)
            assistant_msg = ChatMessage.objects.create(
                thread=thread,
                role=ChatMessage.Role.ASSISTANT,
                content=assistant_content,
                tokens=total_tokens or 0,
                meta={'id': getattr(raw, 'id', None)}
            )
            return Response(ChatMessageSerializer(assistant_msg).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            user_msg.error = str(e)
            user_msg.save(update_fields=['error'])
            return Response({'error': 'Failed to generate response'}, status=status.HTTP_502_BAD_GATEWAY)


class ChatMessageListView(generics.ListAPIView):
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        thread_id = self.kwargs['thread_id']
        return ChatMessage.objects.filter(thread__id=thread_id, thread__topic__user=self.request.user, is_visible=True)


