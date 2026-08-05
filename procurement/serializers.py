from rest_framework import serializers

from .models import ProcurementBudget, ProcurementExpenditure, ProcurementItem


class ProcurementItemSerializer(serializers.ModelSerializer):
    """Serializer for ProcurementItem model."""
    class Meta:
        model = ProcurementItem
        fields = "__all__"
        read_only_fields = ['id']

class ProcurementBudgetSerializer(serializers.ModelSerializer):
    """Serializer for ProcurementBudget model."""
    class Meta:
        model = ProcurementBudget
        fields = "__all__"
        read_only_fields = ['id']

    def to_representation(self, instance):
        """Custom representation to include item name, fiscal year, and department."""
        response = super().to_representation(instance)
        response['item_name'] = instance.item.name if instance.item else None
        response['fiscal_year_name'] = str(instance.fiscal_year.name) if instance.fiscal_year else None
        response['department_name'] = instance.department.name if instance.department else None
        response['amount_spent'] = sum(expenditure.amount for expenditure in instance.expenditures.all())
        return response

class ProcurementExpenditureSerializer(serializers.ModelSerializer):
    """Serializer for ProcurementExpenditure model."""
    class Meta:
        model = ProcurementExpenditure
        fields = "__all__"
        read_only_fields = ['id']

    def to_representation(self, instance):
        """Custom representation to include budget details."""
        response = super().to_representation(instance)
        response['item'] = instance.budget.item.name if instance.budget and instance.budget.item else None
        response['budget_amount'] = instance.budget.amount if instance.budget else None
        response['department'] = instance.budget.department.name if instance.budget and instance.budget.department else None
        return response