from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ToolCreatorViewSet, ClientViewSet,
    ClientRegistrationView, ToolCreatorRegistrationView, AdminRegistrationView
)

router = DefaultRouter()
router.register(r'tool-creators', ToolCreatorViewSet, basename='tool-creator')
router.register(r'clients', ClientViewSet, basename='client')

urlpatterns = [
    # Registration endpoints
    path('register/client/', ClientRegistrationView.as_view(), name='client-register'),
    path('register/tool-creator/', ToolCreatorRegistrationView.as_view(), name='tool-creator-register'),
    path('register/admin/', AdminRegistrationView.as_view(), name='admin-register'),
    
    # ViewSet endpoints
    path('', include(router.urls))
]