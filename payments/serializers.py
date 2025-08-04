from rest_framework import serializers
from .models import Payment, PaymentMethod, PaymentWebhook


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for payment objects"""
    
    class Meta:
        model = Payment
        fields = [
            'id', 'amount', 'currency', 'payment_type', 'status',
            'description', 'points_amount', 'created_at', 'updated_at',
            'completed_at'
        ]
        read_only_fields = ['id', 'status', 'created_at', 'updated_at', 'completed_at']


class CreatePaymentIntentSerializer(serializers.Serializer):
    """Serializer for creating payment intents"""
    
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.50)
    payment_type = serializers.ChoiceField(choices=Payment.PaymentType.choices)
    description = serializers.CharField(max_length=500, required=False, allow_blank=True)
    points_amount = serializers.IntegerField(min_value=1, required=False)
    payment_method_id = serializers.CharField(max_length=255, required=False)
    save_payment_method = serializers.BooleanField(default=False)
    
    def validate(self, attrs):
        """Validate payment data"""
        if attrs['payment_type'] == Payment.PaymentType.POINTS_PURCHASE:
            if 'points_amount' not in attrs:
                raise serializers.ValidationError("points_amount is required for points purchase")
        return attrs


class ConfirmPaymentSerializer(serializers.Serializer):
    """Serializer for confirming payments"""
    
    payment_intent_id = serializers.CharField(max_length=255)
    payment_method_id = serializers.CharField(max_length=255, required=False)


class PaymentMethodSerializer(serializers.ModelSerializer):
    """Serializer for payment methods"""
    
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'stripe_payment_method_id', 'card_brand', 'card_last4',
            'card_exp_month', 'card_exp_year', 'is_default', 'is_active',
            'created_at'
        ]
        read_only_fields = [
            'id', 'stripe_payment_method_id', 'card_brand', 'card_last4',
            'card_exp_month', 'card_exp_year', 'created_at'
        ]


class SetupPaymentMethodSerializer(serializers.Serializer):
    """Serializer for setting up new payment methods"""
    
    payment_method_id = serializers.CharField(max_length=255)
    set_as_default = serializers.BooleanField(default=False)


class PaymentHistorySerializer(serializers.ModelSerializer):
    """Serializer for payment history"""
    
    class Meta:
        model = Payment
        fields = [
            'id', 'amount', 'currency', 'payment_type', 'status',
            'description', 'points_amount', 'created_at', 'completed_at'
        ]


class RefundPaymentSerializer(serializers.Serializer):
    """Serializer for refunding payments"""
    
    payment_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    reason = serializers.CharField(max_length=500, required=False) 