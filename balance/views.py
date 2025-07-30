# points/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Wallet, Transaction
from .serializers import WalletSerializer, TransactionSerializer

class WalletViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Wallet.objects.select_related('user')
    serializer_class = WalletSerializer

    @action(detail=False, methods=['post'])
    def deduct(self, request):
        wallet = request.user.wallet
        amount = Decimal(request.data.get('amount'))
        if wallet.balance < amount:
            return Response({'error': 'Insufficient funds'}, status=status.HTTP_400_BAD_REQUEST)

        wallet.balance -= amount
        wallet.save()
        txn = Transaction.objects.create(wallet=wallet, txn_type=Transaction.DEDUCT, amount=amount, reference=request.data.get('ref'))
        return Response(TransactionSerializer(txn).data)

    @action(detail=False, methods=['post'])
    def refund(self, request):
        wallet = request.user.wallet
        amount = Decimal(request.data.get('amount'))
        wallet.balance += amount
        wallet.save()
        txn = Transaction.objects.create(wallet=wallet, txn_type=Transaction.REFUND, amount=amount, reference=request.data.get('ref'))
        return Response(TransactionSerializer(txn).data)


