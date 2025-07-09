from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample

from .serializers import (
    ToolCreatorSerializer, ClientSerializer,
    ClientRegistrationSerializer, ToolCreatorRegistrationSerializer, AdminRegistrationSerializer
)
from .permissions import IsToolCreator, IsClient, IsAdmin

User = get_user_model()


@extend_schema_view(
    post=extend_schema(
        summary="Register a new client",
        description="Create a new client account with basic information",
        tags=["Registration"],
        examples=[
            OpenApiExample(
                "Client Registration",
                value={
                    "email": "client@example.com",
                    "username": "clientuser",
                    "password": "securepassword123",
                    "password_confirm": "securepassword123",
                    "first_name": "John",
                    "last_name": "Doe",
                    "phone_number": "+1234567890",
                    "company_name": "Example Corp",
                    "bio": "I'm a client looking to use services"
                }
            )
        ]
    )
)
class ClientRegistrationView(generics.CreateAPIView):
    """View for client registration"""
    queryset = User.objects.all()
    serializer_class = ClientRegistrationSerializer
    permission_classes = [AllowAny]


@extend_schema_view(
    post=extend_schema(
        summary="Register a new tool creator",
        description="Create a new tool creator account with basic information",
        tags=["Registration"],
        examples=[
            OpenApiExample(
                "Tool Creator Registration",
                value={
                    "email": "creator@example.com",
                    "username": "toolcreator",
                    "password": "securepassword123",
                    "password_confirm": "securepassword123",
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "phone_number": "+1234567890",
                    "company_name": "Tool Creator Inc",
                    "bio": "I create amazing content for the platform"
                }
            )
        ]
    )
)
class ToolCreatorRegistrationView(generics.CreateAPIView):
    """View for tool creator registration"""
    queryset = User.objects.all()
    serializer_class = ToolCreatorRegistrationSerializer
    permission_classes = [AllowAny]


@extend_schema_view(
    post=extend_schema(
        summary="Register a new admin",
        description="Create a new admin account (admin only)",
        tags=["Registration"],
        examples=[
            OpenApiExample(
                "Admin Registration",
                value={
                    "email": "admin@example.com",
                    "username": "adminuser",
                    "password": "securepassword123",
                    "password_confirm": "securepassword123",
                    "first_name": "Admin",
                    "last_name": "User",
                    "phone_number": "+1234567890",
                    "company_name": "Platform Admin",
                    "bio": "Platform administrator"
                }
            )
        ]
    )
)
class AdminRegistrationView(generics.CreateAPIView):
    """View for admin registration (admin only)"""
    queryset = User.objects.all()
    serializer_class = AdminRegistrationSerializer
    permission_classes = [IsAdmin]


@extend_schema_view(
    list=extend_schema(
        summary="List tool creators",
        description="Get a list of tool creators",
        tags=["Tool Creators"]
    ),
    retrieve=extend_schema(
        summary="Get tool creator details",
        description="Get detailed information about a specific tool creator",
        tags=["Tool Creators"]
    ),
    revenue_stats=extend_schema(
        summary="Get revenue statistics",
        description="Get revenue statistics for tool creator",
        tags=["Tool Creators"]
    )
)
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


@extend_schema_view(
    list=extend_schema(
        summary="List clients",
        description="Get a list of clients",
        tags=["Clients"]
    ),
    retrieve=extend_schema(
        summary="Get client details",
        description="Get detailed information about a specific client",
        tags=["Clients"]
    ),
    points_balance=extend_schema(
        summary="Get points balance",
        description="Get current points balance for client",
        tags=["Clients"]
    )
)
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
            'can_use_services': user.can_use_services(),
        }
        return Response(data) 