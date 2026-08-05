from django.shortcuts import render
from django.utils import timezone
from rest_framework import permissions, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ProcurementBudget, ProcurementExpenditure, ProcurementItem
from .serializers import (ProcurementBudgetSerializer,
                          ProcurementExpenditureSerializer,
                          ProcurementItemSerializer)

# Create your views here.

class ProcurementItemViewSet(viewsets.ModelViewSet):
    """ViewSet for managing ProcurementItem."""
    queryset = ProcurementItem.objects.all()
    serializer_class = ProcurementItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='items-dropdown')
    def items_dropdown(self, request):
        items = self.get_queryset()
        data = [{'id': item.id, 'name': item.name} for item in items]
        return Response(data)

class ProcurementBudgetViewSet(viewsets.ModelViewSet):
    """ViewSet for managing ProcurementBudget."""
    queryset = ProcurementBudget.objects.all()
    serializer_class = ProcurementBudgetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """current balance is equal to the amount on create."""
        serializer.save(current_balance=serializer.validated_data['amount'])

    @action(detail=False, methods=['get'], url_path='budgets-dropdown')
    def budgets_dropdown(self, request):
        budgets = self.get_queryset().filter(fiscal_year__current=True)
        data = [
            {
                'id': budget.id,
                'name': f"{budget.department.name} - {budget.item.name} - {budget.current_balance:,.0f}",
                'balance': budget.current_balance,
            }
            for budget in budgets
        ]
        return Response(data)

class ProcurementExpenditureViewSet(viewsets.ModelViewSet):
    """ViewSet for managing ProcurementExpenditure."""
    queryset = ProcurementExpenditure.objects.all()
    serializer_class = ProcurementExpenditureSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """Override to ensure expenditure does not exceed budget."""
        budget = serializer.validated_data['budget']
        amount = serializer.validated_data['amount']
        if amount > budget.current_balance:
            raise ValueError("Expenditure amount cannot exceed the budgeted amount.")
        # Deduct the expenditure amount from the current balance
        budget.current_balance -= amount
        budget.save()
        serializer.save()