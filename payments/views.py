import stripe
import logging
from decimal import Decimal
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample, OpenApiParameter

from .models import Payment, PaymentMethod, PaymentWebhook
from .serializers import (
    PaymentSerializer, CreatePaymentIntentSerializer, ConfirmPaymentSerializer,
    PaymentMethodSerializer, SetupPaymentMethodSerializer, PaymentHistorySerializer,
    RefundPaymentSerializer
)
from .utils import StripeService

# Configure Stripe

User = get_user_model()
logger = logging.getLogger(__name__)


@extend_schema_view(
    post=extend_schema(
        summary="Create payment intent",
        description="Create a new payment intent for processing payments",
        tags=["Payments"],
        examples=[
            OpenApiExample(
                "Points Purchase",
                value={
                    "amount": "10.00",
                    "payment_type": "points_purchase",
                    "description": "Purchase 1000 points",
                    "points_amount": 1000
                }
            )
        ]
    )
)
class CreatePaymentIntentView(generics.CreateAPIView):
    """Create payment intent for processing payments"""
    serializer_class = CreatePaymentIntentSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Get or create Stripe customer
            customer = StripeService.get_or_create_customer(request.user)
            
            # Create payment record
            payment = Payment.objects.create(
                user=request.user,
                amount=serializer.validated_data['amount'],
                currency=settings.STRIPE_CURRENCY.upper(),
                payment_type=serializer.validated_data['payment_type'],
                description=serializer.validated_data.get('description', ''),
                points_amount=serializer.validated_data.get('points_amount'),
                stripe_customer_id=customer.id,
                metadata={
                    'user_id': str(request.user.id),
                    'payment_type': serializer.validated_data['payment_type']
                }
            )
            
            # Create Stripe payment intent
            payment_intent = StripeService.create_payment_intent(
                amount=payment.amount,
                currency=payment.currency,
                customer_id=customer.id,
                payment_method_id=serializer.validated_data.get('payment_method_id'),
                metadata=payment.metadata
            )
            
            # Update payment with Stripe data
            payment.stripe_payment_intent_id = payment_intent.id
            payment.stripe_payment_method_id = serializer.validated_data.get('payment_method_id')
            payment.save()
            
            return Response({
                'payment_id': payment.id,
                'client_secret': payment_intent.client_secret,
                'payment_intent_id': payment_intent.id,
                'amount': payment.amount,
                'currency': payment.currency
            }, status=status.HTTP_201_CREATED)
            
        except stripe.error.StripeError as e:
            return Response({
                'error': f'Stripe error: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Payment intent creation error: {e}")
            return Response({
                'error': 'Failed to create payment intent'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema_view(
    post=extend_schema(
        summary="Confirm payment",
        description="Confirm a payment intent",
        tags=["Payments"]
    )
)
class ConfirmPaymentView(generics.CreateAPIView):
    """Confirm payment intent"""
    serializer_class = ConfirmPaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            payment_intent_id = serializer.validated_data['payment_intent_id']
            payment_method_id = serializer.validated_data.get('payment_method_id')
            
            # Get payment record
            try:
                payment = Payment.objects.get(
                    stripe_payment_intent_id=payment_intent_id,
                    user=request.user
                )
            except Payment.DoesNotExist:
                return Response({
                    'error': 'Payment not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Confirm payment intent
            payment_intent = StripeService.confirm_payment_intent(
                payment_intent_id, payment_method_id
            )
            
            # Update payment status
            if payment_intent.status == 'succeeded':
                payment.status = Payment.PaymentStatus.SUCCEEDED
                payment.completed_at = timezone.now()
                
                # Add points to user if it's a points purchase
                if payment.payment_type == Payment.PaymentType.POINTS_PURCHASE and payment.points_amount:
                    request.user.points_balance += payment.points_amount
                    request.user.save()
            elif payment_intent.status == 'requires_action':
                payment.status = Payment.PaymentStatus.PROCESSING
            else:
                payment.status = Payment.PaymentStatus.FAILED
            
            payment.save()
            
            return Response({
                'payment_id': payment.id,
                'status': payment.status,
                'payment_intent_status': payment_intent.status,
                'requires_action': payment_intent.status == 'requires_action',
                'client_secret': payment_intent.client_secret if payment_intent.status == 'requires_action' else None
            })
            
        except stripe.error.StripeError as e:
            return Response({
                'error': f'Stripe error: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Payment confirmation error: {e}")
            return Response({
                'error': 'Failed to confirm payment'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema_view(
    list=extend_schema(
        summary="List payment methods",
        description="Get user's saved payment methods",
        tags=["Payment Methods"]
    ),
    create=extend_schema(
        summary="Add payment method",
        description="Add a new payment method",
        tags=["Payment Methods"]
    )
)
class PaymentMethodViewSet(viewsets.ModelViewSet):
    """ViewSet for managing payment methods"""
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return PaymentMethod.objects.filter(user=self.request.user, is_active=True)
    
    def create(self, request, *args, **kwargs):
        serializer = SetupPaymentMethodSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Get or create Stripe customer
            customer = StripeService.get_or_create_customer(request.user)
            
            # Attach payment method to customer
            payment_method_id = serializer.validated_data['payment_method_id']
            stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer.id
            )
            
            # Get payment method details
            payment_method = stripe.PaymentMethod.retrieve(payment_method_id)
            
            # Create payment method record
            pm = PaymentMethod.objects.create(
                user=request.user,
                stripe_payment_method_id=payment_method_id,
                stripe_customer_id=customer.id,
                card_brand=payment_method.card.brand,
                card_last4=payment_method.card.last4,
                card_exp_month=payment_method.card.exp_month,
                card_exp_year=payment_method.card.exp_year,
                is_default=serializer.validated_data.get('set_as_default', False)
            )
            
            # Set as default if requested
            if pm.is_default:
                PaymentMethod.objects.filter(user=request.user).exclude(id=pm.id).update(is_default=False)
            
            return Response(PaymentMethodSerializer(pm).data, status=status.HTTP_201_CREATED)
            
        except stripe.error.StripeError as e:
            return Response({
                'error': f'Stripe error: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Payment method creation error: {e}")
            return Response({
                'error': 'Failed to add payment method'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Set payment method as default"""
        try:
            payment_method = self.get_object()
            PaymentMethod.objects.filter(user=request.user).update(is_default=False)
            payment_method.is_default = True
            payment_method.save()
            
            return Response({'status': 'Payment method set as default'})
        except Exception as e:
            logger.error(f"Set default payment method error: {e}")
            return Response({
                'error': 'Failed to set default payment method'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema_view(
    list=extend_schema(
        summary="Payment history",
        description="Get user's payment history",
        tags=["Payments"]
    )
)
class PaymentHistoryView(generics.ListAPIView):
    """View for payment history"""
    serializer_class = PaymentHistorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def stripe_webhook(request):
    """Handle Stripe webhooks"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        logger.error("Invalid payload in webhook")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature in webhook")
        return HttpResponse(status=400)
    
    # Store webhook event
    webhook, created = PaymentWebhook.objects.get_or_create(
        stripe_event_id=event['id'],
        defaults={
            'event_type': event['type'],
            'event_data': event['data']
        }
    )
    
    if not created and webhook.processed:
        return HttpResponse(status=200)
    
    # Handle the event
    try:
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            
            try:
                payment = Payment.objects.get(
                    stripe_payment_intent_id=payment_intent['id']
                )
                payment.status = Payment.PaymentStatus.SUCCEEDED
                payment.completed_at = timezone.now()
                payment.save()
                
                # Add points if it's a points purchase
                if payment.payment_type == Payment.PaymentType.POINTS_PURCHASE and payment.points_amount:
                    payment.user.points_balance += payment.points_amount
                    payment.user.save()
                
                webhook.payment = payment
                
            except Payment.DoesNotExist:
                logger.error(f"Payment not found for intent: {payment_intent['id']}")
        
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            
            try:
                payment = Payment.objects.get(
                    stripe_payment_intent_id=payment_intent['id']
                )
                payment.status = Payment.PaymentStatus.FAILED
                payment.save()
                
                webhook.payment = payment
                
            except Payment.DoesNotExist:
                logger.error(f"Payment not found for intent: {payment_intent['id']}")
        
        # Mark webhook as processed
        webhook.processed = True
        webhook.processed_at = timezone.now()
        webhook.save()
        
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return HttpResponse(status=500)
    
    return HttpResponse(status=200)
