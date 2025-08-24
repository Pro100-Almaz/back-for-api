from django.contrib import admin
from .models import Payment, PaymentMethod, PaymentWebhook, Subscription


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'amount', 'currency', 'payment_type', 'status',
        'points_amount', 'created_at', 'completed_at'
    ]
    list_filter = ['status', 'payment_type', 'currency', 'created_at']
    search_fields = ['user__email', 'stripe_payment_intent_id', 'description']
    readonly_fields = [
        'id', 'stripe_payment_intent_id', 'stripe_payment_method_id',
        'stripe_customer_id', 'created_at', 'updated_at', 'completed_at'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'amount', 'currency', 'payment_type', 'status')
        }),
        ('Payment Details', {
            'fields': ('description', 'points_amount', 'metadata')
        }),
        ('Stripe Information', {
            'fields': ('stripe_payment_intent_id', 'stripe_payment_method_id', 'stripe_customer_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at')
        })
    )


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'card_brand', 'card_last4', 'card_exp_month',
        'card_exp_year', 'is_default', 'is_active', 'created_at'
    ]
    list_filter = ['card_brand', 'is_default', 'is_active', 'created_at']
    search_fields = ['user__email', 'stripe_payment_method_id', 'card_last4']
    readonly_fields = [
        'stripe_payment_method_id', 'stripe_customer_id', 'card_brand',
        'card_last4', 'card_exp_month', 'card_exp_year', 'created_at', 'updated_at'
    ]
    ordering = ['-created_at']


@admin.register(PaymentWebhook)
class PaymentWebhookAdmin(admin.ModelAdmin):
    list_display = [
        'stripe_event_id', 'event_type', 'processed', 'payment',
        'created_at', 'processed_at'
    ]
    list_filter = ['event_type', 'processed', 'created_at']
    search_fields = ['stripe_event_id', 'event_type']
    readonly_fields = [
        'stripe_event_id', 'event_type', 'event_data',
        'created_at', 'processed_at'
    ]
    ordering = ['-created_at']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'stripe_subscription_id', 'user', 'status', 'price_id',
        'current_period_end', 'cancel_at_period_end', 'canceled_at', 'created_at'
    ]
    list_filter = ['status', 'cancel_at_period_end', 'created_at']
    search_fields = ['user__email', 'stripe_subscription_id', 'stripe_customer_id', 'price_id']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
