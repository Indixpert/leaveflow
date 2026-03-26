from django.db import models
from django.conf import settings
from decimal import Decimal

# NOTE: This implementation assumes the existence of 'apps.leaves.models.LeaveType'.
# It also assumes that the User model (settings.AUTH_USER_MODEL) has an 'employment_type'
# CharField whose choices match LeavePolicy.EmploymentType.
from apps.leaves.models import LeaveType


class LeavePolicy(models.Model):
    class EmploymentType(models.TextChoices):
        FULL_TIME = 'full_time', 'Full-time'
        PART_TIME = 'part_time', 'Part-time'
        CONTRACTOR = 'contractor', 'Contractor'

    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name='policies')
    employment_type = models.CharField(max_length=20, choices=EmploymentType.choices)
    days_per_month = models.DecimalField(max_digits=4, decimal_places=2)
    max_balance = models.DecimalField(max_digits=5, decimal_places=2)
    carry_forward_max = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"Policy for {self.leave_type.name} ({self.get_employment_type_display()})"


class LeaveBalance(models.Model):
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name='balances')
    balance = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    year = models.IntegerField()

    class Meta:
        unique_together = ('employee', 'leave_type', 'year')

    def __str__(self):
        return f"{self.employee} - {self.leave_type.name} ({self.year}): {self.balance}"


class BalanceAuditLog(models.Model):
    class ActionChoices(models.TextChoices):
        ACCRUAL = 'accrual', 'Accrual'
        DEDUCTION = 'deduction', 'Deduction'
        ADJUSTMENT = 'adjustment', 'Adjustment'
        CARRY_FORWARD = 'carry_forward', 'Carry Forward'

    balance = models.ForeignKey(LeaveBalance, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ActionChoices.choices)
    delta = models.DecimalField(max_digits=5, decimal_places=2)
    balance_after = models.DecimalField(max_digits=6, decimal_places=2)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_action_display()} of {self.delta} for {self.balance.employee} at {self.created_at}"
