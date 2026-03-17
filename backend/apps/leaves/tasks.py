from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from decimal import Decimal

from .models import LeaveRequest, ApprovalStep, LeavePolicy, LeaveBalance, BalanceAuditLog

User = get_user_model()

@shared_task
def process_leave_request_change(leave_request_id):
    """
    Handles notifications and other side effects of a leave request status change.
    """
    try:
        request = LeaveRequest.objects.get(id=leave_request_id)
    except LeaveRequest.DoesNotExist:
        return f"LeaveRequest with id {leave_request_id} not found."

    # Example: Send email to employee on final approval/rejection
    if request.status in [LeaveRequest.Status.APPROVED, LeaveRequest.Status.REJECTED]:
        send_mail(
            subject=f'Your leave request has been {request.status}',
            message=f'Hi {request.employee.first_name},\n\nYour leave request from {request.start_date} to {request.end_date} has been {request.status}.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.employee.email],
        )

    # Example: Send email to next approver
    if request.status in [LeaveRequest.Status.PENDING_MANAGER, LeaveRequest.Status.PENDING_HR]:
        try:
            next_approver_step = request.approval_steps.filter(decision=ApprovalStep.Decision.PENDING).first()
            if next_approver_step:
                approver = next_approver_step.approver
                send_mail(
                    subject='New Leave Request for Approval',
                    message=f'Hi {approver.first_name},\n\nA new leave request from {request.employee.get_full_name()} is awaiting your approval.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[approver.email],
                )
                # create_google_calendar_event(request, approver) # Placeholder for calendar integration
        except ApprovalStep.DoesNotExist:
            # No pending approval steps
            pass
            
    return f"Processed leave request {leave_request_id} with status {request.status}"


@shared_task
def accrue_monthly_leave():
    """
    Scheduled task to accrue leave for all active employees.
    Runs on the 1st of each month.
    Handles year-end carry-forward in January.
    """
    today = timezone.now().date()
    current_year = today.year
    is_january = today.month == 1

    active_employees = User.objects.filter(is_active=True)
    
    for employee in active_employees:
        # Assuming employee has 'employment_type' attribute from the custom User model
        if not hasattr(employee, 'employment_type'):
            continue

        policies = LeavePolicy.objects.filter(employment_type=employee.employment_type)
        
        for policy in policies:
            with transaction.atomic():
                # Year-end rollover logic
                if is_january:
                    previous_year = current_year - 1
                    try:
                        prev_balance_obj = LeaveBalance.objects.get(
                            employee=employee,
                            leave_type=policy.leave_type,
                            year=previous_year
                        )
                        
                        carry_forward_amount = min(prev_balance_obj.balance, policy.carry_forward_max)
                        
                        if carry_forward_amount > 0:
                            # Get or create new balance for current year with carry-forward amount
                            new_balance_obj, created = LeaveBalance.objects.get_or_create(
                                employee=employee,
                                leave_type=policy.leave_type,
                                year=current_year,
                                defaults={'balance': carry_forward_amount}
                            )
                            if not created:
                                new_balance_obj.balance += carry_forward_amount
                                new_balance_obj.save(update_fields=['balance'])

                            BalanceAuditLog.objects.create(
                                balance_entry=new_balance_obj,
                                change=carry_forward_amount,
                                reason=BalanceAuditLog.Reason.CARRY_FORWARD
                            )
                    except LeaveBalance.DoesNotExist:
                        # No balance in the previous year, nothing to carry forward.
                        pass

                # Monthly accrual logic
                balance_obj, created = LeaveBalance.objects.get_or_create(
                    employee=employee,
                    leave_type=policy.leave_type,
                    year=current_year
                )
                
                current_balance = balance_obj.balance
                accrual_amount = policy.days_per_month
                
                # Cap the balance at max_balance
                new_balance = min(current_balance + accrual_amount, policy.max_balance)
                actual_accrual = new_balance - current_balance
                
                if actual_accrual > Decimal('0.00'):
                    balance_obj.balance = new_balance
                    balance_obj.save(update_fields=['balance'])
                    
                    BalanceAuditLog.objects.create(
                        balance_entry=balance_obj,
                        change=actual_accrual,
                        reason=BalanceAuditLog.Reason.ACCRUAL
                    )
                    
    return f"Leave accrual process completed for {today}."
