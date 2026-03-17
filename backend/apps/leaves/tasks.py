from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
# from .utils import create_google_calendar_event # Assuming a utility function exists

@shared_task
def process_leave_request_change(leave_request_id):
    """
    Handles notifications and other side effects of a leave request status change.
    """
    from .models import LeaveRequest, ApprovalStep
    
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
