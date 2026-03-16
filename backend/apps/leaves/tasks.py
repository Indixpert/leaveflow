from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import LeaveRequest, ApprovalStep

User = get_user_model()

@shared_task
def send_notification_email(leave_request_id, recipient_user_id, is_final_decision=False):
    try:
        leave_request = LeaveRequest.objects.select_related('employee', 'leave_type').get(id=leave_request_id)
        recipient = User.objects.get(id=recipient_user_id)
        
        if is_final_decision:
            subject = f"Update on your leave request: {leave_request.get_status_display()}"
            message = (
                f"Hi {leave_request.employee.first_name},\n\n"
                f"Your leave request from {leave_request.start_date} to {leave_request.end_date} has been {leave_request.get_status_display()}.\n\n"
                f"Thank you."
            )
        else:
            subject = f"Action Required: Leave Request for {leave_request.employee.get_full_name()}"
            message = (
                f"Hi {recipient.first_name},\n\n"
                f"A new leave request from {leave_request.employee.get_full_name()} requires your approval.\n\n"
                f"Dates: {leave_request.start_date} to {leave_request.end_date}\n"
                f"Type: {leave_request.leave_type.name}\n"
                f"Reason: {leave_request.reason}\n\n"
                f"Please review it in the leave management system.\n\n"
                f"Thank you."
            )

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient.email],
            fail_silently=False,
        )
    except (LeaveRequest.DoesNotExist, User.DoesNotExist) as e:
        print(f"Could not send email for leave request {leave_request_id}: {e}")
    except Exception as e:
        print(f"An error occurred while sending email: {e}")


@shared_task
def create_calendar_event(leave_request_id, approver_user_id):
    try:
        leave_request = LeaveRequest.objects.select_related('employee').get(id=leave_request_id)
        approver = User.objects.get(id=approver_user_id)

        print(f"--- MOCK CALENDAR EVENT CREATION ---")
        print(f"Creating calendar event for approver: {approver.email}")
        print(f"Leave Request: {leave_request.id}")
        print(f"Summary: Review leave for {leave_request.employee.get_full_name()}")
        print(f"Start Time: {leave_request.created_at.isoformat()}")
        print(f"Description: Please review the leave request in the portal.")
        print(f"--- END MOCK ---")
        
        return f"Mock calendar event created for leave request {leave_request_id}"
    except (LeaveRequest.DoesNotExist, User.DoesNotExist) as e:
        print(f"Could not create calendar event for leave request {leave_request_id}: {e}")
        return f"Failed to create event: {e}"
