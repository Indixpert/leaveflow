import uuid
from datetime import date, timedelta
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
# from .tasks import process_leave_request_change

class LeaveType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    max_days_per_year = models.PositiveIntegerField(default=0)
    requires_document = models.BooleanField(default=False)
    carry_forward_limit = models.IntegerField(default=0, help_text="Number of days that can be carried over to the next year. 0 for no carry forward.")

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

    def calculate_total_days(self):
        if not self.start_date or not self.end_date:
            return 0
        
        holidays = PublicHoliday.objects.filter(
            date__range=(self.start_date, self.end_date)
        ).values_list('date', flat=True)
        
        total_days = 0
        current_date = self.start_date
        while current_date <= self.end_date:
            # Monday is 0 and Sunday is 6
            if current_date.weekday() < 5 and current_date not in holidays:
                total_days += 1
            current_date += timedelta(days=1)
        return total_days

    def save(self, *args, **kwargs):
        self.total_days = self.calculate_total_days()
        # Defer importing tasks to avoid circular dependency
        from .tasks import process_leave_request_change
        # Check if status is being updated
        if self.pk is not None:
            orig = LeaveRequest.objects.get(pk=self.pk)
            if orig.status != self.status:
                # Status has changed, trigger task after saving
                # We use on_commit to ensure the transaction is complete
                from django.db import transaction
                transaction.on_commit(lambda: process_leave_request_change.delay(self.id))
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee}'s {self.leave_type.name} request"

class ApprovalStep(models.Model):
    class Role(models.TextChoices):
        MANAGER = 'manager', 'Manager'
        HR = 'hr', 'HR'
    
    class Decision(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    request = models.ForeignKey(LeaveRequest, on_delete=models.CASCADE, related_name='approval_steps')
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='approvals')
    role = models.CharField(max_length=10, choices=Role.choices)
    decision = models.CharField(max_length=10, choices=Decision.choices, default=Decision.PENDING)
    comment = models.TextField(blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('request', 'role')
        ordering = ['request', 'role']

    def __str__(self):
        return f"{self.get_role_display()} approval for {self.request}"

@receiver(post_save, sender=LeaveRequest)
def on_leave_request_created(sender, instance, created, **kwargs):
    """
    Trigger a Celery task when a leave request is first created.
    """
    if created:
        from .tasks import process_leave_request_change
        process_leave_request_change.delay(instance.id)
