import csv
from datetime import timedelta, date
from dateutil.relativedelta import relativedelta
from io import StringIO, BytesIO

from django.db.models import Sum, Count, F, Value, CharField
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.core.cache import cache
from django.template.loader import render_to_string
from weasyprint import HTML

from apps.leaves.models import LeaveRequest, LeaveBalance
from apps.accounts.models import Department, User

CACHE_TIMEOUT = 3600  # 1 hour

def get_leave_utilization_data(filters):
    """
    Generates leave utilization data.
    Data is cached for 1 hour.
    """
    cache_key = f"leave_utilization_{filters.get('department_id')}_{filters.get('leave_type_id')}_{filters.get('start_date')}_{filters.get('end_date')}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data

    start_date = filters.get('start_date')
    end_date = filters.get('end_date')
    department_id = filters.get('department_id')
    leave_type_id = filters.get('leave_type_id')

    # Days taken
    taken_qs = LeaveRequest.objects.filter(
        status=LeaveRequest.Status.APPROVED,
        start_date__lte=end_date,
        end_date__gte=start_date
    ).values(
        'employee__department__name', 'leave_type__name'
    ).annotate(
        department=F('employee__department__name'),
        leave_type=F('leave_type__name'),
        total_days_taken=Sum('total_days')
    ).values('department', 'leave_type', 'total_days_taken')

    if department_id:
        taken_qs = taken_qs.filter(employee__department_id=department_id)
    if leave_type_id:
        taken_qs = taken_qs.filter(leave_type_id=leave_type_id)

    # Days entitled (current balance)
    year = date.fromisoformat(start_date).year
    entitled_qs = LeaveBalance.objects.filter(
        year=year
    ).values(
        'employee__department__name', 'leave_type__name'
    ).annotate(
        department=F('employee__department__name'),
        leave_type=F('leave_type__name'),
        total_days_entitled=Sum('balance')
    ).values('department', 'leave_type', 'total_days_entitled')

    if department_id:
        entitled_qs = entitled_qs.filter(employee__department_id=department_id)
    if leave_type_id:
        entitled_qs = entitled_qs.filter(leave_type_id=leave_type_id)

    # Combine data
    data = {}
    for item in taken_qs:
        key = (item['department'], item['leave_type'])
        if key not in data:
            data[key] = {'department': item['department'], 'leave_type': item['leave_type'], 'taken': 0, 'entitled': 0}
        data[key]['taken'] += item['total_days_taken']

    for item in entitled_qs:
        key = (item['department'], item['leave_type'])
        if key not in data:
            data[key] = {'department': item['department'], 'leave_type': item['leave_type'], 'taken': 0, 'entitled': 0}
        data[key]['entitled'] += item['total_days_entitled']

    result = list(data.values())
    cache.set(cache_key, result, timeout=CACHE_TIMEOUT)
    return result


def get_absenteeism_trend_data(filters):
    """
    Generates absenteeism trend data for the last 12 months.
    """
    department_id = filters.get('department_id')
    cache_key = f"absenteeism_trend_{department_id}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data

    today = timezone.now().date()
    results = []

    department_filter = {}
    if department_id:
        department_filter['department_id'] = department_id

    total_employees = User.objects.filter(**department_filter).count()
    if total_employees == 0:
        return []

    for i in range(12, 0, -1):
        month_date = today - relativedelta(months=i)
        month_start = month_date.replace(day=1)
        month_end = (month_start + relativedelta(months=1)) - timedelta(days=1)
        
        # A simple approximation for working days
        working_days_in_month = 22 
        total_working_days = total_employees * working_days_in_month

        days_absent = LeaveRequest.objects.filter(
            employee__department_id=department_id,
            status=LeaveRequest.Status.APPROVED,
            start_date__lte=month_end,
            end_date__gte=month_start
        ).aggregate(total=Coalesce(Sum('total_days'), 0))['total']

        rate = (days_absent / total_working_days) * 100 if total_working_days > 0 else 0

        results.append({
            'month': month_start.strftime('%Y-%m'),
            'absenteeism_rate': float(rate),
            'days_absent': float(days_absent)
        })

    cache.set(cache_key, results, timeout=CACHE_TIMEOUT)
    return results


def get_pending_approvals_data():
    """
    Gets leave requests pending approval for more than 48 hours.
    """
    cache_key = "pending_approvals"
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data

    forty_eight_hours_ago = timezone.now() - timedelta(hours=48)
    pending_requests = LeaveRequest.objects.filter(
        status__in=[LeaveRequest.Status.PENDING_MANAGER, LeaveRequest.Status.PENDING_HR],
        updated_at__lt=forty_eight_hours_ago
    ).order_by('updated_at').select_related('employee', 'leave_type')

    result = list(pending_requests) # evaluate queryset
    cache.set(cache_key, result, timeout=CACHE_TIMEOUT)
    return result

def generate_csv(data, field_names):
    """Generates a CSV file in memory."""
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=field_names)
    writer.writeheader()
    writer.writerows(data)
    return output.getvalue()

def generate_pdf(template_name, context):
    """Generates a PDF file in memory from an HTML template."""
    html_string = render_to_string(template_name, context)
    html = HTML(string=html_string)
    return html.write_pdf()
