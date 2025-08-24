from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
import uuid

User = get_user_model()


class Payment(models.Model):
    """Model to track payment transactions"""
    
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        PROCESSING = 'processing', _('Processing')
        SUCCEEDED = 'succeeded', _('Succeeded')
        FAILED = 'failed', _('Failed')
        CANCELED = 'canceled', _('Canceled')
        REFUNDED = 'refunded', _('Refunded')
    
    class PaymentType(models.TextChoices):
        POINTS_PURCHASE = 'points_purchase', _('Points Purchase')
        SUBSCRIPTION = 'subscription', _('Subscription')
        ONE_TIME = 'one_time', _('One Time Payment')
    
    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text=_('Amount in USD'))
    currency = models.CharField(max_length=3, default='USD')
    payment_type = models.CharField(max_length=20, choices=PaymentType.choices)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    
    # Stripe fields
    stripe_payment_intent_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    stripe_payment_method_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)
    
    # Additional data
    description = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True, help_text=_('Additional payment metadata'))
    
    # Points-specific fields
    points_amount = models.PositiveIntegerField(null=True, blank=True, help_text=_('Points purchased'))
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('payment')
        verbose_name_plural = _('payments')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment {self.id} - {self.user.email} - ${self.amount}"
    
    @property
    def is_successful(self):
        return self.status == self.PaymentStatus.SUCCEEDED
    
    @property
    def can_be_refunded(self):
        return self.status == self.PaymentStatus.SUCCEEDED


class PaymentMethod(models.Model):
    """Model to store user's payment methods"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    stripe_payment_method_id = models.CharField(max_length=255, unique=True)
    stripe_customer_id = models.CharField(max_length=255)
    
    # Card details (for display purposes)
    card_brand = models.CharField(max_length=20, blank=True)
    card_last4 = models.CharField(max_length=4, blank=True)
    card_exp_month = models.PositiveIntegerField(null=True, blank=True)
    card_exp_year = models.PositiveIntegerField(null=True, blank=True)
    
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('payment method')
        verbose_name_plural = _('payment methods')
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.card_brand} ****{self.card_last4} - {self.user.email}"


class PaymentWebhook(models.Model):
    """Model to track Stripe webhook events"""
    
    stripe_event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=100)
    processed = models.BooleanField(default=False)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, null=True, blank=True, related_name='webhooks')
    
    # Raw event data
    event_data = models.JSONField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('payment webhook')
        verbose_name_plural = _('payment webhooks')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Webhook {self.stripe_event_id} - {self.event_type}"


class Subscription(models.Model):
    """Stripe subscription state synced via webhooks"""

    class SubscriptionStatus(models.TextChoices):
        TRIALING = 'trialing', _('Trialing')
        ACTIVE = 'active', _('Active')
        PAST_DUE = 'past_due', _('Past Due')
        CANCELED = 'canceled', _('Canceled')
        UNPAID = 'unpaid', _('Unpaid')
        INCOMPLETE = 'incomplete', _('Incomplete')
        INCOMPLETE_EXPIRED = 'incomplete_expired', _('Incomplete Expired')

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    stripe_customer_id = models.CharField(max_length=255, db_index=True)
    stripe_subscription_id = models.CharField(max_length=255, unique=True)

    status = models.CharField(max_length=30, choices=SubscriptionStatus.choices)
    price_id = models.CharField(max_length=255, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(null=True, blank=True)

    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('subscription')
        verbose_name_plural = _('subscriptions')
        ordering = ['-created_at']

    def __str__(self):
        return f"Subscription {self.stripe_subscription_id} - {self.user.email} - {self.status}"
