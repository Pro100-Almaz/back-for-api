# feedback/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema

from .models import Suggestion, BugReport, Upvote
from .serializers import SuggestionSerializer, BugReportSerializer, UpvoteSerializer


class SuggestionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Suggestion.objects.all().order_by('-created_at')
    serializer_class = SuggestionSerializer

    http_method_names = ['get', 'post', 'head', 'options']

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def upvote(self, request, pk=None):
        suggestion = self.get_object()
        upvote, created = Upvote.objects.get_or_create(user=request.user, suggestion=suggestion)
        if not created:
            upvote.delete()  # toggle off
        return Response({'votes': suggestion.upvotes.count()})

@extend_schema(
    request={
        'multipart/form-data': BugReportSerializer
    }
)
class BugReportViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    queryset = BugReport.objects.all().order_by('-created_at')
    serializer_class = BugReportSerializer

    http_method_names = ['get', 'post', 'head', 'options']

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
