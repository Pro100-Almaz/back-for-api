from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CreatePaymentIntentView, ConfirmPaymentView, PaymentMethodViewSet,
    PaymentHistoryView, SubscriptionViewSet, create_checkout_session, stripe_webhook, success_payment
)

router = DefaultRouter()
router.register(r'payment-methods', PaymentMethodViewSet, basename='payment-method')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')

urlpatterns = [
    # Payment processing
    path('create-intent/', CreatePaymentIntentView.as_view(), name='create-payment-intent'),
    path('confirm/', ConfirmPaymentView.as_view(), name='confirm-payment'),
    
    # Payment history
    path('history/', PaymentHistoryView.as_view(), name='payment-history'),
    path('create-checkout-session/', create_checkout_session, name='create-checkout-session'),
    path('success', success_payment, name='success-payment'),

    
    # Stripe webhook
    path('webhook/', stripe_webhook, name='stripe-webhook'),
    
    # Payment methods
    path('', include(router.urls)),
] 