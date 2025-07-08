from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta

from .models import Tool, ToolUsage, ToolFeedback, ToolApiKey
from .serializers import (
    ToolSerializer, ToolListSerializer, ToolCreateSerializer,
    ToolUsageSerializer, ToolUsageCreateSerializer, ToolFeedbackSerializer,
    ToolApiKeySerializer, ToolUsageStatsSerializer
)
from users.permissions import (
    CanBrowseTools, CanUseTools, CanSubmitTools, CanManageTools,
    IsToolCreator, IsAdmin, IsOwnerOrAdmin
)

User = get_user_model()


class ToolViewSet(viewsets.ModelViewSet):
    """ViewSet for tool management"""
    queryset = Tool.objects.all()
    serializer_class = ToolSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ToolListSerializer
        elif self.action == 'create':
            return ToolCreateSerializer
        return ToolSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [CanBrowseTools()]
        elif self.action == 'create':
            return [CanSubmitTools()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsOwnerOrAdmin()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        
        # Filter by status
        queryset = Tool.objects.filter(status=Tool.Status.ACTIVE)
        
        # Admins can see all tools
        if user.is_admin:
            return Tool.objects.all()
        
        # Tool creators can see their own tools and all active tools
        if user.is_tool_creator:
            return Tool.objects.filter(
                Q(creator=user) | Q(status=Tool.Status.ACTIVE)
            )
        
        # Clients can only see active tools
        return queryset
    
    @action(detail=True, methods=['post'], permission_classes=[CanUseTools])
    def use(self, request, pk=None):
        """Use a tool"""
        tool = self.get_object()
        serializer = ToolUsageCreateSerializer(
            data={'tool': tool.id, 'input_data': request.data.get('input_data')},
            context={'request': request}
        )
        
        if serializer.is_valid():
            usage = serializer.save()
            
            # Simulate tool execution (in real app, this would call the actual tool)
            import time
            time.sleep(0.1)  # Simulate processing time
            
            # Update usage record with mock output
            usage.output_data = {
                'result': f'Processed data from {tool.name}',
                'status': 'success'
            }
            usage.execution_time = timedelta(milliseconds=100)
            usage.save()
            
            return Response({
                'usage_id': usage.id,
                'output_data': usage.output_data,
                'points_spent': usage.points_spent,
                'remaining_points': request.user.points_balance
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def feedback(self, request, pk=None):
        """Get feedback for a tool"""
        tool = self.get_object()
        feedback = ToolFeedback.objects.filter(tool=tool, is_public=True)
        serializer = ToolFeedbackSerializer(feedback, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def submit_feedback(self, request, pk=None):
        """Submit feedback for a tool"""
        tool = self.get_object()
        serializer = ToolFeedbackSerializer(
            data={'tool': tool.id, **request.data},
            context={'request': request}
        )
        
        if serializer.is_valid():
            feedback = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[CanBrowseTools])
    def search(self, request):
        """Search tools by name, description, or tags"""
        query = request.query_params.get('q', '')
        category = request.query_params.get('category', '')
        
        queryset = self.get_queryset()
        
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(tags__contains=[query])
            )
        
        if category:
            queryset = queryset.filter(category=category)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsToolCreator])
    def my_tools(self, request):
        """Get tools created by the current user"""
        tools = Tool.objects.filter(creator=request.user)
        serializer = self.get_serializer(tools, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[IsOwnerOrAdmin])
    def stats(self, request, pk=None):
        """Get statistics for a tool"""
        tool = self.get_object()
        
        # Get recent usage
        recent_usage = ToolUsage.objects.filter(tool=tool).order_by('-created_at')[:10]
        usage_data = ToolUsageSerializer(recent_usage, many=True).data
        
        stats = {
            'total_uses': tool.total_uses,
            'total_revenue': float(tool.total_revenue),
            'average_rating': float(tool.average_rating),
            'recent_usage': usage_data
        }
        
        return Response(stats)


class ToolUsageViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for tool usage tracking"""
    serializer_class = ToolUsageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_admin:
            return ToolUsage.objects.all()
        elif user.is_tool_creator:
            return ToolUsage.objects.filter(tool__creator=user)
        else:
            return ToolUsage.objects.filter(user=user)
    
    @action(detail=False, methods=['get'])
    def my_usage(self, request):
        """Get current user's usage history"""
        usage = ToolUsage.objects.filter(user=request.user).order_by('-created_at')
        serializer = self.get_serializer(usage, many=True)
        return Response(serializer.data)


class ToolFeedbackViewSet(viewsets.ModelViewSet):
    """ViewSet for tool feedback"""
    serializer_class = ToolFeedbackSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_admin:
            return ToolFeedback.objects.all()
        elif user.is_tool_creator:
            return ToolFeedback.objects.filter(tool__creator=user)
        else:
            return ToolFeedback.objects.filter(user=user)
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsOwnerOrAdmin()]
        return [IsAuthenticated()]


class ToolApiKeyViewSet(viewsets.ModelViewSet):
    """ViewSet for managing API keys"""
    serializer_class = ToolApiKeySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_admin:
            return ToolApiKey.objects.all()
        else:
            return ToolApiKey.objects.filter(user=user)
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsOwnerOrAdmin()]
        return [IsAuthenticated()]
    
    @action(detail=True, methods=['post'])
    def regenerate(self, request, pk=None):
        """Regenerate API key"""
        api_key = self.get_object()
        
        import secrets
        api_key.api_key = f"tk_{secrets.token_urlsafe(32)}"
        api_key.save()
        
        serializer = self.get_serializer(api_key)
        return Response(serializer.data) 