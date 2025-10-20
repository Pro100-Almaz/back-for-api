# in points/urls.py
from rest_framework.routers import DefaultRouter
from .views import WalletViewSet

router = DefaultRouter()
router.register('', WalletViewSet)
urlpatterns = router.urls