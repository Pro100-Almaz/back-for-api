from rest_framework import viewsets, status, generics, permissions
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample

from .serializers import (
    ToolCreatorSerializer, ClientSerializer, UserSerializer,
    ClientRegistrationSerializer, ToolCreatorRegistrationSerializer, AdminRegistrationSerializer, AvatarCreateSerializer, AvatarDetailSerializer
)
from .permissions import IsToolCreator, IsClient, IsAdmin
from .models import Avatar

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
    get=extend_schema(
        summary="Get current user details",
        description="Get detailed information about the currently authenticated user",
        tags=["User Profile"]
    ),
    put=extend_schema(
        summary="Update current user details",
        description="Update all fields of the current user",
        tags=["User Profile"]
    ),
    patch=extend_schema(
        summary="Partially update current user details",
        description="Update some fields of the current user",
        tags=["User Profile"]
    ),
)
class UserDetailView(generics.RetrieveUpdateAPIView):
    """View for getting and updating current user details"""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


@extend_schema_view(
    get=extend_schema(
        summary="Get current user id",
        description="Get user_id for current user",
        tags=["User Profile"]
    )
)
class CurrentUserIdView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return self.request.user.pk


@extend_schema_view(
    get=extend_schema(
        summary="Upload user avatar",
        description="Upload user avatar",
        tags=["User Profile"]
    )
)

class AvatarCreateView(generics.CreateAPIView):
    """
    POST /api/users/avatar/
      form-data: path=<desired S3 key>, image=@<file>
    Returns: { key, url }
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AvatarCreateSerializer
    parser_classes = [MultiPartParser, FormParser]

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        payload = ser.save()
        return Response(payload, status=201)


@extend_schema_view(
    get=extend_schema(
        summary="Get user avatar list",
        description="Get user avatar list",
        tags=["User Profile"]
    )
)

class AvatarsListView(generics.ListAPIView):
    """
    GET /api/users/avatar/
    Lists caller's avatars (keys + signed URLs).
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AvatarDetailSerializer

    def get_queryset(self):
        return Avatar.objects.filter(user=self.request.user).order_by("-created_at")

class PublicUserAvatarView(generics.GenericAPIView):
    """
    GET /api/users/<int:user_id>/avatar/
    Returns: { user, url } with a signed S3 URL or null if no avatar.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = AvatarDetailSerializer

    def get(self, request, user_id: int, *args, **kwargs):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=404)

        av, _ = Avatar.objects.get_or_create(user=user)
        data = self.get_serializer(av, context={"request": request}).data
        return Response(data, status=200)

#
# class UserAvatarUploadView(generics.UpdateAPIView):
#     serializer_class = AvatarUploadSerializer
#     permission_classes = [IsAuthenticated]
#     parser_classes = [MultiPartParser, FormParser]
#
#     def get_object(self):
#         profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
#         return profile
#
#     def update(self, request, *args, **kwargs):
#         # partial update lets you send just the avatar field
#         instance = self.get_object()
#         serializer = self.get_serializer(instance, data=request.data, partial=True)
#         serializer.is_valid(raise_exception=True)
#         self.perform_update(serializer)
#         # ensure file is saved and url is resolvable
#         instance.refresh_from_db()
#         return Response(serializer.data, status=status.HTTP_200_OK)
#
#     # (optional) delete old avatar to avoid orphans
#     def perform_update(self, serializer):
#         instance = self.get_object()
#         old = instance.avatar.name if instance.avatar else None
#         obj = serializer.save()
#         if old and old != obj.avatar.name:
#             try:
#                 obj.avatar.storage.delete(old)
#             except Exception:
#                 pass


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