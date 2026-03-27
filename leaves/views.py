from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Sum
import numpy as np
from .models import LeaveRequest, LeaveType, ApprovalStep, PublicHoliday
from .serializers import LeaveRequestSerializer, LeaveTypeSerializer, ApprovalStepSerializer

print('print for testing')

class LeaveTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows leave types to be viewed.
    """
    queryset = LeaveType.objects.all()
    serializer_class = LeaveTypeSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'])
    def balance(self, request, pk=None):
        """
        Calculates the remaining leave balance for the current user for a specific leave type.
        This is a simplified calculation and may not cover all edge cases like leaves spanning years.
        """
        leave_type = self.get_object()
        user = request.user
        current_year = timezone.now().year
        last_year = current_year - 1

        # This is a simplification: it assumes requests don't span years.
        taken_this_year = LeaveRequest.objects.filter(
            employee=user,
            leave_type=leave_type,
            status=LeaveRequest.Status.APPROVED,
            start_date__year=current_year
        ).aggregate(total=Sum('total_days'))['total'] or 0

        # This is also simplified.
        taken_last_year = LeaveRequest.objects.filter(
            employee=user,
            leave_type=leave_type,
            status=LeaveRequest.Status.APPROVED,
            start_date__year=last_year
        ).aggregate(total=Sum('total_days'))['total'] or 0
        
        unused_last_year = leave_type.max_days_per_year - taken_last_year
        carry_forward = 0
        if leave_type.carry_forward_limit > 0 and unused_last_year > 0:
            carry_forward = min(unused_last_year, leave_type.carry_forward_limit)

        total_allowance = leave_type.max_days_per_year + carry_forward
        remaining_balance = total_allowance - taken_this_year

        return Response({
            'balance': remaining_balance,
            'allowance': leave_type.max_days_per_year,
            'carry_forward': carry_forward,
            'taken': taken_this_year,
        })

class LeaveRequestViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows leave requests to be viewed or edited.
    """
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        This view should return a list of all the leave requests
        for the currently authenticated user.
        """
        return LeaveRequest.objects.filter(employee=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        # The serializer's create method already handles setting the employee
        # and initial status.
        serializer.save()

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Action to cancel a leave request.
        """
        leave_request = self.get_object()
        if leave_request.status in [LeaveRequest.Status.DRAFT, LeaveRequest.Status.PENDING_MANAGER]:
            leave_request.status = LeaveRequest.Status.CANCELLED
            leave_request.save(update_fields=['status'])
            return Response(self.get_serializer(leave_request).data)
        else:
            return Response(
                {'error': 'Cannot cancel a request that is already being processed by HR or is finalized.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def calculate_days(self, request):
        """
        Calculates the number of working days between two dates, excluding weekends and public holidays.
        """
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')

        if not start_date_str or not end_date_str:
            return Response({'error': 'start_date and end_date query parameters are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_date = timezone.datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = timezone.datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        if start_date > end_date:
            return Response({'total_days': 0})

        holidays = PublicHoliday.objects.values_list('date', flat=True)
        total_days = np.busday_count(start_date, end_date + timezone.timedelta(days=1), holidays=list(holidays))
        
        return Response({'total_days': int(total_days)})

class ApprovalViewSet(mixins.ListModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin,
                      viewsets.GenericViewSet):
    """
    API endpoint for approvers to view and act on leave requests.
    """
    serializer_class = ApprovalStepSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        This view should return a list of all approval steps
        for the currently authenticated user.
        """
        return ApprovalStep.objects.filter(approver=self.request.user).order_by('request__created_at')

    def update(self, request, *args, **kwargs):
        """
        Handle an approver's decision.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        decision = serializer.validated_data.get('decision')
        
        if instance.decision != ApprovalStep.Decision.PENDING:
            return Response({'error': 'This request has already been decided upon.'}, status=status.HTTP_400_BAD_REQUEST)

        if decision not in [ApprovalStep.Decision.APPROVED, ApprovalStep.Decision.REJECTED]:
            return Response({'error': 'Invalid decision.'}, status=status.HTTP_400_BAD_REQUEST)

        instance.decision = decision
        instance.comment = serializer.validated_data.get('comment', '')
        instance.decided_at = timezone.now()
        instance.save()
        
        leave_request = instance.request
        if decision == ApprovalStep.Decision.REJECTED:
            leave_request.status = LeaveRequest.Status.REJECTED
        elif instance.role == ApprovalStep.Role.MANAGER:
            if ApprovalStep.objects.filter(request=leave_request, role=ApprovalStep.Role.HR).exists():
                leave_request.status = LeaveRequest.Status.PENDING_HR
            else:
                leave_request.status = LeaveRequest.Status.APPROVED
        elif instance.role == ApprovalStep.Role.HR:
            leave_request.status = LeaveRequest.Status.APPROVED
            
        leave_request.save(update_fields=['status'])

        return Response(LeaveRequestSerializer(leave_request).data)
