from celery import shared_task
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.contrib.auth import get_user_model

from . import services

User = get_user_model()

@shared_task(bind=True)
def export_report_task(self, report_type, export_format, filters, user_id):
    """
    A Celery task to generate and save a report file.
    """
    user = User.objects.get(id=user_id) # For context, if needed
    
    data = []
    field_names = []
    template_name = 'reports/pdf_template.html'
    context = {}

    if report_type == 'leave_utilization':
        data = services.get_leave_utilization_data(filters)
        field_names = ['department', 'leave_type', 'taken', 'entitled']
        context = {'title': 'Leave Utilization Report', 'data': data, 'headers': field_names}
    elif report_type == 'absenteeism_trend':
        data = services.get_absenteeism_trend_data(filters)
        field_names = ['month', 'absenteeism_rate', 'days_absent']
        context = {'title': 'Absenteeism Trend Report', 'data': data, 'headers': field_names}
    elif report_type == 'pending_approvals':
        # get_pending_approvals_data returns model objects, need to serialize
        pending_requests = services.get_pending_approvals_data()
        data = [
            {
                'id': r.id,
                'employee': r.employee.get_full_name(),
                'leave_type': r.leave_type.name,
                'start_date': r.start_date,
                'end_date': r.end_date,
                'status': r.get_status_display(),
                'pending_since': r.updated_at.isoformat()
            } for r in pending_requests
        ]
        field_names = ['id', 'employee', 'leave_type', 'start_date', 'end_date', 'status', 'pending_since']
        context = {'title': 'Pending Approvals Report', 'data': data, 'headers': field_names}

    if not data:
        # Handle case with no data
        return "No data for report."

    file_content = None
    file_extension = export_format
    
    if export_format == 'csv':
        file_content = services.generate_csv(data, field_names).encode('utf-8')
    elif export_format == 'pdf':
        file_content = services.generate_pdf(template_name, context)

    if file_content:
        file_name = f"reports/{report_type}_{self.request.id}.{file_extension}"
        path = default_storage.save(file_name, ContentFile(file_content))
        return default_storage.url(path)
    
    return "Failed to generate report."
