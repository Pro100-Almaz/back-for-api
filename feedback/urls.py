# feedback/urls.py
from rest_framework.routers import DefaultRouter
from .views import SuggestionViewSet, BugReportViewSet

router = DefaultRouter()
router.register('suggestions', SuggestionViewSet)
router.register('bugs', BugReportViewSet)
urlpatterns = router.urls
