# points/views.py
from decimal import Decimal

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Wallet, Transaction
from .serializers import WalletSerializer, TransactionSerializer
from .services import BalanceService

class WalletViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Wallet.objects.select_related('user')
    serializer_class = WalletSerializer

    @action(detail=False, methods=['post'])
    def deduct(self, request):
        try:
            amount = request.data.get('amount')
            reference = request.data.get('ref', '')
            
            txn = BalanceService.deduct_balance(
                user=request.user,
                amount=amount,
                reference=reference
            )
            return Response(TransactionSerializer(txn).data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': 'Failed to deduct balance'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def refund(self, request):
        try:
            amount = request.data.get('amount')
            reference = request.data.get('ref', '')
            
            txn = BalanceService.refund_balance(
                user=request.user,
                amount=amount,
                reference=reference
            )
            return Response(TransactionSerializer(txn).data)
        except Exception as e:
            return Response({'error': 'Failed to refund balance'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def balance(self, request):
        """Get current user balance"""
        try:
            balance = BalanceService.get_balance(request.user)
            return Response({'balance': balance})
        except Exception as e:
            return Response({'error': 'Failed to get balance'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


