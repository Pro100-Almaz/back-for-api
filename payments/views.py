import stripe
import logging
import json
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample
from datetime import datetime

from .models import Payment, PaymentMethod, PaymentWebhook, Subscription
from .serializers import (
    CreatePaymentIntentSerializer, ConfirmPaymentSerializer,
    PaymentMethodSerializer, SetupPaymentMethodSerializer, PaymentHistorySerializer, SubscriptionSerializer
)
from .utils import StripeService
from balance.services import BalanceService

# Configure Stripe

User = get_user_model()
logger = logging.getLogger(__name__)


def _safe_ts_to_dt(timestamp_value):
    if not timestamp_value:
        return None
    try:
        return timezone.make_aware(datetime.utcfromtimestamp(int(timestamp_value)))
    except Exception:
        return None


def _get_user_by_stripe_customer(customer_id):
    if not customer_id:
        return None
    pm = PaymentMethod.objects.filter(stripe_customer_id=customer_id).select_related('user').first()
    if pm:
        return pm.user
    payment = Payment.objects.filter(stripe_customer_id=customer_id).select_related('user').first()
    if payment:
        return payment.user
    try:
        customer = stripe.Customer.retrieve(customer_id)
        email = getattr(customer, 'email', None) or (customer.get('email') if isinstance(customer, dict) else None)
        if email:
            return User.objects.filter(email=email).first()
    except Exception:
        pass
    return None


def _upsert_subscription_from_stripe_object(stripe_subscription_obj):
    customer_id = stripe_subscription_obj.get('customer') if isinstance(stripe_subscription_obj, dict) else getattr(stripe_subscription_obj, 'customer', None)
    user = _get_user_by_stripe_customer(customer_id)
    if not user:
        logger.error(f"Unable to map Stripe customer {customer_id} to a user for subscription sync")
        return None

    # Pull primary item for price/quantity
    items = (stripe_subscription_obj.get('items', {}) if isinstance(stripe_subscription_obj, dict) else getattr(stripe_subscription_obj, 'items', {})) or {}
    items_data = items.get('data') if isinstance(items, dict) else getattr(items, 'data', [])
    primary_item = items_data[0] if items_data else None
    price_id = None
    quantity = 1
    if primary_item:
        price = primary_item.get('price') if isinstance(primary_item, dict) else getattr(primary_item, 'price', None)
        price_id = (price.get('id') if isinstance(price, dict) else getattr(price, 'id', None)) if price else None
        quantity = primary_item.get('quantity') if isinstance(primary_item, dict) else getattr(primary_item, 'quantity', 1)

    sub_id = stripe_subscription_obj.get('id') if isinstance(stripe_subscription_obj, dict) else getattr(stripe_subscription_obj, 'id', None)
    status = stripe_subscription_obj.get('status') if isinstance(stripe_subscription_obj, dict) else getattr(stripe_subscription_obj, 'status', None)
    cancel_at_period_end = stripe_subscription_obj.get('cancel_at_period_end') if isinstance(stripe_subscription_obj, dict) else getattr(stripe_subscription_obj, 'cancel_at_period_end', False)
    current_period_start = stripe_subscription_obj.get('current_period_start') if isinstance(stripe_subscription_obj, dict) else getattr(stripe_subscription_obj, 'current_period_start', None)
    current_period_end = stripe_subscription_obj.get('current_period_end') if isinstance(stripe_subscription_obj, dict) else getattr(stripe_subscription_obj, 'current_period_end', None)
    trial_end = stripe_subscription_obj.get('trial_end') if isinstance(stripe_subscription_obj, dict) else getattr(stripe_subscription_obj, 'trial_end', None)
    canceled_at = stripe_subscription_obj.get('canceled_at') if isinstance(stripe_subscription_obj, dict) else getattr(stripe_subscription_obj, 'canceled_at', None)
    metadata = stripe_subscription_obj.get('metadata') if isinstance(stripe_subscription_obj, dict) else getattr(stripe_subscription_obj, 'metadata', {})

    defaults = {
        'user': user,
        'stripe_customer_id': customer_id,
        'status': status or Subscription.SubscriptionStatus.INCOMPLETE,
        'price_id': price_id or '',
        'quantity': quantity or 1,
        'current_period_start': _safe_ts_to_dt(current_period_start),
        'current_period_end': _safe_ts_to_dt(current_period_end),
        'trial_end': _safe_ts_to_dt(trial_end),
        'cancel_at_period_end': bool(cancel_at_period_end),
        'canceled_at': _safe_ts_to_dt(canceled_at),
        'metadata': metadata or {},
    }

    subscription, created = Subscription.objects.get_or_create(
        stripe_subscription_id=sub_id,
        defaults=defaults,
    )

    if not created:
        for field, value in defaults.items():
            setattr(subscription, field, value)
        if subscription.user_id != user.id:
            subscription.user = user
        subscription.save()

    return subscription
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
                
                # Add balance to user if it's a points purchase
                if payment.payment_type == Payment.PaymentType.POINTS_PURCHASE and payment.points_amount:
                    balance_amount = BalanceService.convert_payment_to_balance(
                        payment.amount, payment.points_amount
                    )
                    BalanceService.add_balance(
                        user=request.user,
                        amount=balance_amount,
                        reference=f"payment_{payment.id}",
                        description=f"Points purchase: {payment.description}"
                    )
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

    def get_serializer_class(self):
        if self.action == 'create':
            return SetupPaymentMethodSerializer
        return PaymentMethodSerializer
    
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
            print(str(e))
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


@extend_schema_view(
    list=extend_schema(
        summary="List subscriptions for current user",
        tags=["Subscriptions"],
    ),
    retrieve=extend_schema(
        summary="Get subscription detail",
        tags=["Subscriptions"],
    ),
)
class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def create_checkout_session(request):
    data = request.data

    mode = data.get("mode", "payment")
    user = request.user

    try:
        # Subscription mode via Checkout (https://docs.stripe.com/billing/quickstart)
        if mode == 'subscription':
            price_id = data.get('price_id')
            quantity = int(data.get('quantity', 1))
            if not price_id:
                return JsonResponse({"error": "price_id is required for subscription checkout"}, status=400)

            session = stripe.checkout.Session.create(
                line_items=[{
                    'price': price_id,
                    'quantity': quantity,
                }],
                mode='subscription',
                success_url='http://localhost:3000/subscription?success=true',
                cancel_url='http://localhost:3000/subscription',
                customer_email=getattr(user, 'email', None) or None,
            )

            return JsonResponse({"url": session.url}, status=status.HTTP_201_CREATED)

        # One-time payment for points purchase (default)
        amount = data.get("amount")
        payment_type = data.get("payment_type", "points_purchase")
        description = data.get("description", "")
        points_amount = data.get("points_amount", 0)

        if not amount or float(amount) < 0.5:
            return JsonResponse({"error": "Amount is required and must be >= 0.5"}, status=400)

        # Build success URL with user_id (handled by success_payment view)
        success_url = f"http://localhost:8000/api/payments/success?user_id={user.id}"

        session = stripe.checkout.Session.create(
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': description or 'Points Purchase',
                    },
                    'unit_amount': int(float(amount) * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url='http://localhost:3000/subscription',
        )

        # Record Payment in DB (status: pending)
        Payment.objects.create(
            user=user,
            amount=amount,
            currency='USD',
            payment_type=payment_type,
            status=Payment.PaymentStatus.PENDING,
            description=description,
            points_amount=points_amount,
            stripe_payment_intent_id=None,
            stripe_payment_method_id=None,
            stripe_customer_id=None,
            metadata=session.metadata,
        )

        return JsonResponse({"url": session.url}, status=status.HTTP_201_CREATED)

    except stripe.error.StripeError as e:
        return JsonResponse({"error": f"Stripe error: {str(e)}"}, status=400)


@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def success_payment(request):
    user_id = request.GET.get('user_id')

    if not user_id:
        return JsonResponse({'error': 'user_id is required in query params'}, status=400)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    # Find the latest pending payment for this user (assuming only one in progress)
    payment = Payment.objects.filter(
        user=user,
        status=Payment.PaymentStatus.PENDING  # or PROCESSING if you want to include that state
    ).order_by('-created_at').first()

    if not payment:
        return JsonResponse({'error': 'No pending payment found for this user'}, status=404)

    # Mark the payment as succeeded (for demo purposes - in production, use Stripe webhook!)
    payment.status = Payment.PaymentStatus.SUCCEEDED
    payment.completed_at = timezone.now()
    payment.save(update_fields=['status', 'completed_at'])

    # Auto-credit user's wallet for points purchases
    try:
        if payment.payment_type == Payment.PaymentType.POINTS_PURCHASE and payment.points_amount:
            balance_amount = BalanceService.convert_payment_to_balance(
                payment.amount, payment.points_amount
            )
            BalanceService.add_balance(
                user=payment.user,
                amount=balance_amount,
                reference=f"payment_{payment.id}",
                description=f"Points purchase: {payment.description or ''}"
            )
    except Exception as e:
        logger.error(f"Auto-credit on success_payment failed for payment {payment.id}: {e}")

    # Optionally, return payment info
    url = f"http://localhost:3000/subscription?success=true"
    return HttpResponseRedirect(url)


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
                
                # Add balance if it's a points purchase
                if payment.payment_type == Payment.PaymentType.POINTS_PURCHASE and payment.points_amount:
                    balance_amount = BalanceService.convert_payment_to_balance(
                        payment.amount, payment.points_amount
                    )
                    BalanceService.add_balance(
                        user=payment.user,
                        amount=balance_amount,
                        reference=f"payment_{payment.id}",
                        description=f"Points purchase: {payment.description}"
                    )
                
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
        
        # Subscription lifecycle events
        elif event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            mode = session.get('mode') if isinstance(session, dict) else getattr(session, 'mode', None)
            if mode == 'subscription':
                customer_id = session.get('customer') if isinstance(session, dict) else getattr(session, 'customer', None)
                sub_id = session.get('subscription') if isinstance(session, dict) else getattr(session, 'subscription', None)
                try:
                    if sub_id:
                        stripe_subscription = stripe.Subscription.retrieve(sub_id)
                        _upsert_subscription_from_stripe_object(stripe_subscription)
                except Exception as inner_e:
                    logger.error(f"Subscribe checkout completion handling error: {inner_e}")

        elif event['type'].startswith('customer.subscription.'):
            stripe_subscription = event['data']['object']
            _upsert_subscription_from_stripe_object(stripe_subscription)

        elif event['type'] in ('invoice.payment_succeeded', 'invoice.payment_failed'):
            invoice = event['data']['object']
            sub_id = invoice.get('subscription') if isinstance(invoice, dict) else getattr(invoice, 'subscription', None)
            if sub_id:
                try:
                    stripe_subscription = stripe.Subscription.retrieve(sub_id)
                    _upsert_subscription_from_stripe_object(stripe_subscription)
                except Exception as inner_e:
                    logger.error(f"Invoice subscription sync error: {inner_e}")

        # Mark webhook as processed
        webhook.processed = True
        webhook.processed_at = timezone.now()
        webhook.save()
        
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return HttpResponse(status=500)
    
    return HttpResponse(status=200)
