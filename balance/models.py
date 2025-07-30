# points/models.py
from django.conf import settings
from django.db import models

class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

class Transaction(models.Model):
    DEPOSIT = 'DEPOSIT'
    DEDUCT  = 'DEDUCT'
    REFUND  = 'REFUND'
    TYPE_CHOICES = [(DEPOSIT, 'Deposit'), (DEDUCT, 'Deduct'), (REFUND, 'Refund')]

    wallet      = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    txn_type    = models.CharField(max_length=10, choices=TYPE_CHOICES)
    amount      = models.DecimalField(max_digits=12, decimal_places=2)
    created_at  = models.DateTimeField(auto_now_add=True)
    reference   = models.CharField(max_length=255, blank=True, help_text="e.g. Stripe payment ID or tool-run ID")
