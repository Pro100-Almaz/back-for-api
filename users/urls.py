from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ToolCreatorViewSet, ClientViewSet, UserDetailView, UserAvatarUploadView,
    ClientRegistrationView, ToolCreatorRegistrationView, AdminRegistrationView,
    CurrentUserIdView
)

router = DefaultRouter()
router.register(r'tool-creators', ToolCreatorViewSet, basename='tool-creator')
router.register(r'clients', ClientViewSet, basename='client')

urlpatterns = [
    path('me/', UserDetailView.as_view(), name='user-detail'),
    path('me/user_id/', CurrentUserIdView.as_view(), name='current-user-id'),
    path('profile/avatar/', UserAvatarUploadView.as_view(), name='profile-avatar-upload'),

    path('register/client/', ClientRegistrationView.as_view(), name='client-register'),
    path('register/tool-creator/', ToolCreatorRegistrationView.as_view(), name='tool-creator-register'),
    path('register/admin/', AdminRegistrationView.as_view(), name='admin-register'),

    path('', include(router.urls))
]