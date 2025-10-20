# points/views.py
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Wallet
from .serializers import WalletSerializer, TransactionSerializer
from .services import BalanceService

class WalletViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Wallet.objects.select_related('user')
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def list(self, request, *args, **kwargs):
        balance = BalanceService.get_balance(request.user)
        return Response({"balance": str(balance)})

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
