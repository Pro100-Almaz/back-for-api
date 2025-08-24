from decimal import Decimal
from django.db import transaction
from django.contrib.auth import get_user_model
from .models import Wallet, Transaction
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class BalanceService:
    """Service class for balance operations"""
    
    @staticmethod
    def get_or_create_wallet(user):
        """Get or create wallet for user"""
        wallet, created = Wallet.objects.get_or_create(user=user)
        return wallet
    
    @staticmethod
    @transaction.atomic
    def add_balance(user, amount, reference=None, description=None):
        """Add balance to user wallet"""
        try:
            wallet = BalanceService.get_or_create_wallet(user)
            amount = Decimal(str(amount))
            
            # Update wallet balance
            wallet.balance += amount
            wallet.save()
            
            # Create transaction record
            txn = Transaction.objects.create(
                wallet=wallet,
                txn_type=Transaction.DEPOSIT,
                amount=amount,
                reference=reference or ''
            )
            
            logger.info(f"Added {amount} to wallet for user {user.email}. New balance: {wallet.balance}")
            return txn
            
        except Exception as e:
            logger.error(f"Error adding balance for user {user.email}: {e}")
            raise
    
    @staticmethod
    @transaction.atomic
    def deduct_balance(user, amount, reference=None, description=None):
        """Deduct balance from user wallet"""
        try:
            wallet = BalanceService.get_or_create_wallet(user)
            amount = Decimal(str(amount))
            
            # Check if sufficient balance
            if wallet.balance < amount:
                raise ValueError(f"Insufficient balance. Current: {wallet.balance}, Required: {amount}")
            
            # Update wallet balance
            wallet.balance -= amount
            wallet.save()
            
            # Create transaction record
            txn = Transaction.objects.create(
                wallet=wallet,
                txn_type=Transaction.DEDUCT,
                amount=amount,
                reference=reference or ''
            )
            
            logger.info(f"Deducted {amount} from wallet for user {user.email}. New balance: {wallet.balance}")
            return txn
            
        except Exception as e:
            logger.error(f"Error deducting balance for user {user.email}: {e}")
            raise
    
    @staticmethod
    @transaction.atomic
    def refund_balance(user, amount, reference=None, description=None):
        """Refund balance to user wallet"""
        try:
            wallet = BalanceService.get_or_create_wallet(user)
            amount = Decimal(str(amount))
            
            # Update wallet balance
            wallet.balance += amount
            wallet.save()
            
            # Create transaction record
            txn = Transaction.objects.create(
                wallet=wallet,
                txn_type=Transaction.REFUND,
                amount=amount,
                reference=reference or ''
            )
            
            logger.info(f"Refunded {amount} to wallet for user {user.email}. New balance: {wallet.balance}")
            return txn
            
        except Exception as e:
            logger.error(f"Error refunding balance for user {user.email}: {e}")
            raise
    
    @staticmethod
    def get_balance(user):
        """Get user's current balance"""
        try:
            wallet = BalanceService.get_or_create_wallet(user)
            return wallet.balance
        except Exception as e:
            logger.error(f"Error getting balance for user {user.email}: {e}")
            return Decimal('0.00')
    
    @staticmethod
    def convert_payment_to_balance(payment_amount, points_amount=None):
        """Convert payment amount to balance amount"""
        # For now, we'll use a simple 1:1 conversion
        # You can implement your own conversion logic here
        if points_amount:
            # If points are specified, use that
            return Decimal(str(points_amount))
        else:
            # Otherwise, convert payment amount (e.g., $1 = 100 points)
            return Decimal(str(payment_amount)) * 100