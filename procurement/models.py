from common.models import FinanceYear, TimeStampedModel
from django.db import models
from hr.models import Department

# Create your models here.

class ProcurementItem(TimeStampedModel):
    """Model representing a procurement item."""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


# procurement budget model
class ProcurementBudget(TimeStampedModel):
    """Model representing a procurement budget."""
    item = models.ForeignKey(ProcurementItem, on_delete=models.CASCADE, related_name='budgets')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fiscal_year = models.ForeignKey(FinanceYear, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='procurement_budgets')

    class Meta:
        unique_together = ('item', 'fiscal_year', 'department')
        verbose_name_plural = "Procurement Budgets"
        permissions = (
            ("can_manage_procurement_budget", "Can manage procurement budget"),
        )

    def save(self, *args, **kwargs):
        # Ensure that the current balance does not exceed the budgeted amount
        
        if self.current_balance > self.amount:
            raise ValueError("Current balance cannot exceed the budgeted amount.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item.name} - {self.fiscal_year}"


class ProcurementExpenditure(TimeStampedModel):
    """Model representing a procurement expenditure."""
    reference = models.CharField(max_length=255, unique=True, blank=True)
    budget = models.ForeignKey(ProcurementBudget, on_delete=models.CASCADE, related_name='expenditures')
    procurement_subject = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(auto_now=True)

    class Meta:
        verbose_name_plural = "Procurement Expenditures"

    def save(self, *args, **kwargs):
        # Ensure that the expenditure amount does not exceed the budgeted amount
        if self.amount > self.budget.amount:
            raise ValueError("Expenditure amount cannot exceed the budgeted amount.")
        if self.reference is None or self.reference == "":
            # Generate a unique reference number if not provided
            last_expenditure = ProcurementExpenditure.objects.order_by('-id').first()
            if last_expenditure:
                last_id = last_expenditure.id
            else:
                last_id = 0
            self.reference = f"EXP-{last_id + 1:05d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.budget.item.name} - {self.date}"


