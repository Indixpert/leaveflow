from django.contrib import admin
from .models import LeavePolicy, LeaveBalance, BalanceAuditLog


@admin.register(LeavePolicy)
class LeavePolicyAdmin(admin.ModelAdmin):
    list_display = ('leave_type', 'employment_type', 'days_per_month', 'max_balance', 'carry_forward_max')
    list_filter = ('employment_type', 'leave_type')


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'year', 'balance')
    list_filter = ('year', 'leave_type')
    search_fields = ('employee__username', 'employee__first_name', 'employee__last_name')
    raw_id_fields = ('employee',)


@admin.register(BalanceAuditLog)
class BalanceAuditLogAdmin(admin.ModelAdmin):
    list_display = ('balance', 'action', 'delta', 'balance_after', 'performed_by', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('balance__employee__username',)
    raw_id_fields = ('balance', 'performed_by')
