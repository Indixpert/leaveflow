from celery.result import AsyncResult
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import JSONParser

from . import services
from . import tasks
from ..leaves.serializers import LeaveRequestSerializer

class IsHRAdminPermission(permissions.BasePermission):
    """
    Custom permission to only allow HR admins to access the view.
    (A simple placeholder for a real permission class)
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_staff # Simplified check

class LeaveUtilizationView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsHRAdminPermission]

    def get(self, request):
        # TODO: Add validation for query params
        filters = {
            'start_date': request.query_params.get('start_date'),
            'end_date': request.query_params.get('end_date'),
            'department_id': request.query_params.get('department_id'),
            'leave_type_id': request.query_params.get('leave_type_id'),
        }
        data = services.get_leave_utilization_data(filters)
        return Response(data)

class AbsenteeismTrendView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsHRAdminPermission]

    def get(self, request):
        filters = {
            'department_id': request.query_params.get('department_id'),
        }
        data = services.get_absenteeism_trend_data(filters)
        return Response(data)

class PendingApprovalsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsHRAdminPermission]

    def get(self, request):
        pending_requests = services.get_pending_approvals_data()
        serializer = LeaveRequestSerializer(pending_requests, many=True)
        return Response(serializer.data)

class ReportExportView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsHRAdminPermission]
    parser_classes = [JSONParser]

    def post(self, request):
        report_type = request.data.get('report_type')
        export_format = request.data.get('format', 'csv') # 'csv' or 'pdf'
        filters = request.data.get('filters', {})

        if report_type not in ['leave_utilization', 'absenteeism_trend', 'pending_approvals']:
            return Response({'error': 'Invalid report type'}, status=status.HTTP_400_BAD_REQUEST)

        if export_format not in ['csv', 'pdf']:
            return Response({'error': 'Invalid export format'}, status=status.HTTP_400_BAD_REQUEST)

        task = tasks.export_report_task.delay(report_type, export_format, filters, request.user.id)

        return Response({'task_id': task.id}, status=status.HTTP_202_ACCEPTED)

class ExportStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsHRAdminPermission]

    def get(self, request, task_id):
        task_result = AsyncResult(task_id)
        result = {
            'task_id': task_id,
            'status': task_result.status,
            'result': task_result.result if task_result.ready() else None
        }
        return Response(result)
