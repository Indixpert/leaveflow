from django.contrib import admin
from .models import LeaveType, LeaveRequest, ApprovalStep, LeavePolicy, LeaveBalance, BalanceAuditLog

@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'status')
    list_filter = ('status', 'leave_type')
    search_fields = ('employee__username', 'employee__first_name', 'employee__last_name')

@admin.register(ApprovalStep)
class ApprovalStepAdmin(admin.ModelAdmin):
    list_display = ('request', 'approver', 'role', 'decision')
    list_filter = ('role', 'decision')

@admin.register(LeavePolicy)
class LeavePolicyAdmin(admin.ModelAdmin):
    list_display = ('leave_type', 'employment_type', 'days_per_month', 'max_balance', 'carry_forward_max')
    list_filter = ('employment_type', 'leave_type')

@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'year', 'balance')
    search_fields = ('employee__username', 'employee__first_name', 'employee__last_name')
    list_filter = ('year', 'leave_type')
    readonly_fields = ('balance',)

@admin.register(BalanceAuditLog)
class BalanceAuditLogAdmin(admin.ModelAdmin):
    list_display = ('balance_entry', 'change', 'reason', 'timestamp', 'actor', 'related_request')
    list_filter = ('reason', 'timestamp')
    search_fields = ('balance_entry__employee__username',)
    readonly_fields = ('balance_entry', 'change', 'reason', 'timestamp', 'actor', 'related_request')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
