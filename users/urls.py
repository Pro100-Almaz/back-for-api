from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserRegistrationView, UserViewSet, ToolCreatorViewSet, ClientViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'tool-creators', ToolCreatorViewSet, basename='tool-creator')
router.register(r'clients', ClientViewSet, basename='client')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', UserRegistrationView.as_view(), name='user-register'),
] 