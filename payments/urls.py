from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CreatePaymentIntentView, ConfirmPaymentView, PaymentMethodViewSet,
    PaymentHistoryView, stripe_webhook
)

router = DefaultRouter()
router.register(r'payment-methods', PaymentMethodViewSet, basename='payment-method')

urlpatterns = [
    # Payment processing
    path('create-intent/', CreatePaymentIntentView.as_view(), name='create-payment-intent'),
    path('confirm/', ConfirmPaymentView.as_view(), name='confirm-payment'),
    
    # Payment history
    path('history/', PaymentHistoryView.as_view(), name='payment-history'),
    
    # Stripe webhook
    path('webhook/', stripe_webhook, name='stripe-webhook'),
    
    # Payment methods
    path('', include(router.urls)),
] 