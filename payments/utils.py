import stripe
import logging
from django.conf import settings

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)


class StripeService:
    """Service class for Stripe operations"""
    
    @staticmethod
    def get_or_create_customer(user):
        """Get or create Stripe customer for user"""
        try:
            # Try to find existing customer
            customers = stripe.Customer.list(email=user.email, limit=1)
            if customers.data:
                return customers.data[0]
            
            # Create new customer
            customer = stripe.Customer.create(
                email=user.email,
                name=f"{user.first_name} {user.last_name}".strip(),
                metadata={'user_id': str(user.id)}
            )
            return customer
        except stripe.error.StripeError as e:
            logger.error(f"Stripe customer error: {e}")
            raise
    
    @staticmethod
    def create_payment_intent(amount, currency, customer_id, payment_method_id=None, metadata=None):
        """Create Stripe payment intent"""
        try:
            intent_data = {
                'amount': int(amount * 100),  # Convert to cents
                'currency': currency.lower(),
                'customer': customer_id,
                'metadata': metadata or {},
                'automatic_payment_methods': {'enabled': True}
            }
            
            if payment_method_id:
                intent_data['payment_method'] = payment_method_id
                intent_data['confirmation_method'] = 'manual'
                intent_data['confirm'] = True
            
            return stripe.PaymentIntent.create(**intent_data)
        except stripe.error.StripeError as e:
            logger.error(f"Stripe payment intent error: {e}")
            raise
    
    @staticmethod
    def confirm_payment_intent(payment_intent_id, payment_method_id=None):
        """Confirm Stripe payment intent"""
        try:
            confirm_data = {}
            if payment_method_id:
                confirm_data['payment_method'] = payment_method_id
            
            return stripe.PaymentIntent.confirm(payment_intent_id, **confirm_data)
        except stripe.error.StripeError as e:
            logger.error(f"Stripe payment confirmation error: {e}")
            raise