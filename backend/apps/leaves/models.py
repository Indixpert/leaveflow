import uuid
from datetime import date, timedelta

from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

class LeaveType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    max_days_per_year = models.PositiveIntegerField()
    requires_document = models.BooleanField(default=False)
    carry_forward_limit = models.IntegerField(default=0, help_text="Number of days that can be carried over to the next year.")

    def __str__(self):
        return self.name

class PublicHoliday(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateField(unique=True)

    def __str__(self):
        return f"{self.name} ({self.date})"

    class Meta:
        ordering = ['date']

class LeaveRequest(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PENDING_MANAGER = 'pending_manager', 'Pending Manager Approval'
        PENDING_HR = 'pending_hr', 'Pending HR Approval'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        CANCELLED = 'cancelled', 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.IntegerField(editable=False, default=0)
    reason = models.TextField(blank=True)
    document = models.FileField(upload_to='leave_documents/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    _original_status = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_status = self.status

    def __str__(self):
        return f"Leave for {self.employee} from {self.start_date} to {self.end_date}"

    def calculate_total_days(self):
        if not self.start_date or not self.end_date:
            return 0
        
        holidays = set(PublicHoliday.objects.filter(
            date__range=[self.start_date, self.end_date]
        ).values_list('date', flat=True))

        total_days = 0
        current_date = self.start_date
        while current_date <= self.end_date:
            if current_date.weekday() < 5 and current_date not in holidays:
                total_days += 1
            current_date += timedelta(days=1)
        return total_days

    def save(self, *args, **kwargs):
        self.total_days = self.calculate_total_days()
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            self._original_status = self.status

    class Meta:
        ordering = ['-created_at']

class ApprovalStep(models.Model):
    class ApproverRole(models.TextChoices):
        MANAGER = 'manager', 'Manager'
        HR = 'hr', 'HR'

    class Decision(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    request = models.ForeignKey(LeaveRequest, on_delete=models.CASCADE, related_name='approval_steps')
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='approvals')
    role = models.CharField(max_length=10, choices=ApproverRole.choices)
    decision = models.CharField(max_length=10, choices=Decision.choices, default=Decision.PENDING)
    comment = models.TextField(blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Approval for {self.request.id} by {self.approver} ({self.role})"

    class Meta:
        unique_together = ('request', 'role')

@receiver(post_save, sender=LeaveRequest)
def on_leave_request_status_change(sender, instance, created, **kwargs):
    from .tasks import send_notification_email, create_calendar_event

    if not created and instance._original_status != instance.status:
        if instance.status == LeaveRequest.Status.PENDING_MANAGER:
            manager_step = instance.approval_steps.filter(role=ApprovalStep.ApproverRole.MANAGER).first()
            if manager_step:
                send_notification_email.delay(instance.id, manager_step.approver.id)
                create_calendar_event.delay(instance.id, manager_step.approver.id)
        
        if instance.status in [LeaveRequest.Status.APPROVED, LeaveRequest.Status.REJECTED]:
            send_notification_email.delay(instance.id, instance.employee.id, is_final_decision=True)
