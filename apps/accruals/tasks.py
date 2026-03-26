from celery import shared_task
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from decimal import Decimal

from .models import LeavePolicy, LeaveBalance, BalanceAuditLog

User = get_user_model()


@shared_task
def run_monthly_accrual():
    """
    Celery task to run on the 1st of each month to credit leave balances.
    Handles monthly accruals and annual carry-forward.

    To schedule, add to CELERY_BEAT_SCHEDULE in settings.py:
    'run-monthly-accrual': {
        'task': 'apps.accruals.tasks.run_monthly_accrual',
        'schedule': crontab(minute='0', hour='6', day_of_month='1'), # 6 AM on the 1st of every month
    },
    """
    today = timezone.now().date()
    current_year = today.year

    active_employees = User.objects.filter(is_active=True)

    for employee in active_employees:
        if not hasattr(employee, 'employment_type'):
            continue

        policies = LeavePolicy.objects.filter(employment_type=employee.employment_type)

        for policy in policies:
            with transaction.atomic():
                initial_balance = Decimal('0.0')
                carry_forward_note = None

                if today.month == 1:
                    previous_year = current_year - 1
                    try:
                        old_balance = LeaveBalance.objects.get(
                            employee=employee,
                            leave_type=policy.leave_type,
                            year=previous_year
                        )
                        carry_forward_amount = min(old_balance.balance, policy.carry_forward_max)
                        if carry_forward_amount > 0:
                            initial_balance = carry_forward_amount
                            carry_forward_note = f"Carried over {carry_forward_amount} from {previous_year}"
                    except LeaveBalance.DoesNotExist:
                        pass

                balance_record, created = LeaveBalance.objects.select_for_update().get_or_create(
                    employee=employee,
                    leave_type=policy.leave_type,
                    year=current_year,
                    defaults={'balance': initial_balance}
                )

                if created and carry_forward_note:
                    BalanceAuditLog.objects.create(
                        balance=balance_record,
                        action=BalanceAuditLog.ActionChoices.CARRY_FORWARD,
                        delta=initial_balance,
                        balance_after=balance_record.balance,
                        note=carry_forward_note
                    )

                has_accrued_this_month = BalanceAuditLog.objects.filter(
                    balance=balance_record,
                    action=BalanceAuditLog.ActionChoices.ACCRUAL,
                    created_at__year=today.year,
                    created_at__month=today.month
                ).exists()

                if not has_accrued_this_month:
                    accrual_amount = policy.days_per_month
                    current_balance = balance_record.balance
                    potential_new_balance = current_balance + accrual_amount
                    new_balance_value = min(potential_new_balance, policy.max_balance)

                    delta = new_balance_value - current_balance
                    
                    if delta > 0:
                        balance_record.balance = new_balance_value
                        balance_record.save()

                        BalanceAuditLog.objects.create(
                            balance=balance_record,
                            action=BalanceAuditLog.ActionChoices.ACCRUAL,
                            delta=delta,
                            balance_after=balance_record.balance,
                            note=f"Monthly accrual for {today.strftime('%B %Y')}"
                        )
