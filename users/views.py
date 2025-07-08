from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import UserProfile
from .serializers import (
    UserSerializer, UserRegistrationSerializer, UserListSerializer,
    AdminUserSerializer, ToolCreatorSerializer, ClientSerializer
)
from .permissions import (
    IsAdmin, IsToolCreator, IsClient, IsOwnerOrAdmin,
    CanManageUsers, CanBrowseTools, CanUseTools
)

User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    """View for user registration"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for user management"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            if self.request.user.is_admin:
                return AdminUserSerializer
            return UserSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        elif self.action in ['list', 'destroy']:
            return [CanManageUsers()]
        elif self.action in ['update', 'partial_update']:
            return [IsOwnerOrAdmin()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        
        # Admins can see all users
        if user.is_admin:
            return User.objects.all()
        
        # Tool creators can see their own data and clients
        if user.is_tool_creator:
            return User.objects.filter(
                Q(id=user.id) | Q(role=User.Role.CLIENT)
            )
        
        # Clients can only see their own data
        return User.objects.filter(id=user.id)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get current user's profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'], permission_classes=[IsAuthenticated])
    def update_me(self, request):
        """Update current user's profile"""
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdmin])
    def clients(self, request):
        """Get all clients (admin only)"""
        clients = User.objects.filter(role=User.Role.CLIENT)
        serializer = ClientSerializer(clients, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdmin])
    def tool_creators(self, request):
        """Get all tool creators (admin only)"""
        tool_creators = User.objects.filter(role=User.Role.TOOL_CREATOR)
        serializer = ToolCreatorSerializer(tool_creators, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def change_role(self, request, pk=None):
        """Change user role (admin only)"""
        user = self.get_object()
        new_role = request.data.get('role')
        
        if new_role not in [choice[0] for choice in User.Role.choices]:
            return Response(
                {'error': 'Invalid role'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.role = new_role
        user.save()
        
        serializer = self.get_serializer(user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def add_points(self, request, pk=None):
        """Add points to client (admin only)"""
        user = self.get_object()
        points = request.data.get('points', 0)
        
        if user.role != User.Role.CLIENT:
            return Response(
                {'error': 'Can only add points to clients'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.points_balance += points
        user.save()
        
        serializer = ClientSerializer(user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def deduct_points(self, request, pk=None):
        """Deduct points from client (admin only)"""
        user = self.get_object()
        points = request.data.get('points', 0)
        
        if user.role != User.Role.CLIENT:
            return Response(
                {'error': 'Can only deduct points from clients'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if user.points_balance < points:
            return Response(
                {'error': 'Insufficient points'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.points_balance -= points
        user.save()
        
        serializer = ClientSerializer(user)
        return Response(serializer.data)


class ToolCreatorViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for tool creator specific operations"""
    serializer_class = ToolCreatorSerializer
    permission_classes = [IsToolCreator]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return User.objects.filter(role=User.Role.TOOL_CREATOR)
        return User.objects.filter(id=user.id)
    
    @action(detail=False, methods=['get'])
    def revenue_stats(self, request):
        """Get revenue statistics for tool creator"""
        user = request.user
        if not user.is_tool_creator:
            return Response(
                {'error': 'Access denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        data = {
            'total_revenue': float(user.total_revenue),
            'total_payouts': float(user.total_payouts),
            'pending_balance': float(user.total_revenue - user.total_payouts),
        }
        return Response(data)


class ClientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for client specific operations"""
    serializer_class = ClientSerializer
    permission_classes = [IsClient]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return User.objects.filter(role=User.Role.CLIENT)
        return User.objects.filter(id=user.id)
    
    @action(detail=False, methods=['get'])
    def points_balance(self, request):
        """Get current points balance"""
        user = request.user
        if not user.is_client:
            return Response(
                {'error': 'Access denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        data = {
            'points_balance': user.points_balance,
            'can_use_tools': user.can_use_tools(),
        }
        return Response(data) 