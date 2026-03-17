from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from ..accounts.models import User as AccountUser

class LeaveType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class LeaveRequest(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', _('Draft')
        PENDING_MANAGER = 'PENDING_MANAGER', _('Pending Manager Approval')
        PENDING_HR = 'PENDING_HR', _('Pending HR Approval')
        APPROVED = 'APPROVED', _('Approved')
        REJECTED = 'REJECTED', _('Rejected')
        CANCELLED = 'CANCELLED', _('Cancelled')

    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True)
    document = models.FileField(upload_to='leave_documents/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee}'s {self.leave_type.name} request"

class ApprovalStep(models.Model):
    class Role(models.TextChoices):
        MANAGER = 'MANAGER', _('Manager')
        HR = 'HR', _('HR')

    class Decision(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        APPROVED = 'APPROVED', _('Approved')
        REJECTED = 'REJECTED', _('Rejected')

    request = models.ForeignKey(LeaveRequest, on_delete=models.CASCADE, related_name='approval_steps')
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='approvals')
    role = models.CharField(max_length=10, choices=Role.choices)
    decision = models.CharField(max_length=10, choices=Decision.choices, default=Decision.PENDING)
    comment = models.TextField(blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        unique_together = ('request', 'approver')
        ordering = ['order']

    def __str__(self):
        return f"Approval for {self.request} by {self.approver} ({self.get_role_display()})"

# New Models for Leave Accrual

class LeavePolicy(models.Model):
    leave_type = models.ForeignKey('LeaveType', on_delete=models.CASCADE, related_name='policies')
    employment_type = models.CharField(
        max_length=20,
        choices=AccountUser.EmploymentType.choices,
        help_text="The employment type this policy applies to."
    )
    days_per_month = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        help_text="Number of leave days accrued per month."
    )
    max_balance = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Maximum number of leave days that can be accumulated."
    )
    carry_forward_max = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Maximum number of leave days that can be carried forward to the next year."
    )

    class Meta:
        unique_together = ('leave_type', 'employment_type')
        verbose_name = _("Leave Policy")
        verbose_name_plural = _("Leave Policies")

    def __str__(self):
        return f"{self.leave_type.name} Policy for {self.get_employment_type_display()}"


class LeaveBalance(models.Model):
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey('LeaveType', on_delete=models.CASCADE, related_name='balances')
    balance = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.00
    )
    year = models.PositiveIntegerField(
        help_text="The calendar year for which this balance is applicable."
    )

    class Meta:
        unique_together = ('employee', 'leave_type', 'year')
        verbose_name = _("Leave Balance")
        verbose_name_plural = _("Leave Balances")

    def __str__(self):
        return f"{self.employee.get_full_name()}'s {self.leave_type.name} Balance for {self.year}: {self.balance}"


class BalanceAuditLog(models.Model):
    class Reason(models.TextChoices):
        ACCRUAL = 'monthly_accrual', _('Monthly Accrual')
        LEAVE_REQUEST = 'leave_request', _('Leave Request')
        CARRY_FORWARD = 'carry_forward', _('Year-End Carry Forward')
        MANUAL_ADJUSTMENT = 'manual_adjustment', _('Manual Adjustment')
        INITIAL_BALANCE = 'initial_balance', _('Initial Balance')

    balance_entry = models.ForeignKey('LeaveBalance', on_delete=models.CASCADE, related_name='audit_logs')
    change = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="The change in balance. Positive for accrual, negative for deduction."
    )
    reason = models.CharField(
        max_length=50,
        choices=Reason.choices
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="The user who initiated the change (e.g., for manual adjustments)."
    )
    related_request = models.ForeignKey(
        'LeaveRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Link to the leave request that caused this change."
    )

    class Meta:
        ordering = ['-timestamp']
        verbose_name = _("Balance Audit Log")
        verbose_name_plural = _("Balance Audit Logs")

    def __str__(self):
        return f"Change of {self.change} for {self.balance_entry.employee.get_full_name()} on {self.timestamp.date()} due to {self.get_reason_display()}"
