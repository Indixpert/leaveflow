from django.urls import path
from .views import (
    LeaveUtilizationView,
    AbsenteeismTrendView,
    PendingApprovalsView,
    ReportExportView,
    ExportStatusView,
)

urlpatterns = [
    path('leave-utilization/', LeaveUtilizationView.as_view(), name='report-leave-utilization'),
    path('absenteeism-trend/', AbsenteeismTrendView.as_view(), name='report-absenteeism-trend'),
    path('pending-approvals/', PendingApprovalsView.as_view(), name='report-pending-approvals'),
    path('export/', ReportExportView.as_view(), name='report-export-trigger'),
    path('export-status/<str:task_id>/', ExportStatusView.as_view(), name='report-export-status'),
]
