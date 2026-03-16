from django.contrib import admin
from .models import LeaveType, LeaveRequest, ApprovalStep, PublicHoliday

@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'max_days_per_year', 'requires_document', 'carry_forward_limit')

class ApprovalStepInline(admin.TabularInline):
    model = ApprovalStep
    extra = 0
    readonly_fields = ('approver', 'role', 'decision', 'comment', 'decided_at')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'total_days', 'status', 'created_at')
    list_filter = ('status', 'leave_type', 'created_at')
    search_fields = ('employee__username', 'employee__first_name', 'employee__last_name')
    readonly_fields = ('total_days', 'created_at', 'updated_at')
    inlines = [ApprovalStepInline]

@admin.register(ApprovalStep)
class ApprovalStepAdmin(admin.ModelAdmin):
    list_display = ('request', 'approver', 'role', 'decision', 'decided_at')
    list_filter = ('role', 'decision')
    search_fields = ('request__employee__username', 'approver__username')

@admin.register(PublicHoliday)
class PublicHolidayAdmin(admin.ModelAdmin):
    list_display = ('name', 'date')
    list_filter = ('date',)
