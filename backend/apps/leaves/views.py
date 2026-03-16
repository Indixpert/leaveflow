from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import LeaveRequest, ApprovalStep, LeaveType
from .serializers import LeaveRequestSerializer, LeaveTypeSerializer

class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to view or edit it.
    """
    def has_object_permission(self, request, view, obj):
        return obj.employee == request.user

class LeaveTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A viewset for viewing leave types.
    """
    queryset = LeaveType.objects.all()
    serializer_class = LeaveTypeSerializer
    permission_classes = [permissions.IsAuthenticated]

class LeaveRequestViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing an employee's own leave requests.
    """
    serializer_class = LeaveRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        """
        This view should return a list of all the leave requests
        for the currently authenticated user.
        """
        return LeaveRequest.objects.filter(employee=self.request.user).prefetch_related('approval_steps').order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(employee=self.request.user)

    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request, pk=None):
        leave_request = self.get_object()
        if leave_request.status != LeaveRequest.Status.DRAFT:
            return Response({'error': 'Only draft requests can be submitted.'}, status=status.HTTP_400_BAD_REQUEST)

        leave_request.status = LeaveRequest.Status.PENDING_MANAGER
        leave_request.save()
        return Response(self.get_serializer(leave_request).data)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        leave_request = self.get_object()
        if leave_request.status not in [LeaveRequest.Status.DRAFT, LeaveRequest.Status.PENDING_MANAGER, LeaveRequest.Status.PENDING_HR]:
            return Response({'error': 'Cannot cancel a request that has already been approved or rejected.'}, status=status.HTTP_400_BAD_REQUEST)
        
        leave_request.status = LeaveRequest.Status.CANCELLED
        leave_request.save()
        return Response(self.get_serializer(leave_request).data)

class ApprovalViewSet(viewsets.ViewSet):
    """
    A viewset for approvers to view and act on leave requests.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ApprovalStep.objects.filter(
            approver=self.request.user,
            decision=ApprovalStep.Decision.PENDING
        ).select_related('request__employee', 'request__leave_type').order_by('request__created_at')

    def list(self, request):
        queryset = self.get_queryset()
        leave_requests = [step.request for step in queryset]
        serializer = LeaveRequestSerializer(leave_requests, many=True, context={'request': request})
        return Response(serializer.data)

    def make_decision(self, request, request_id, decision):
        try:
            approval_step = ApprovalStep.objects.get(
                request_id=request_id,
                approver=request.user,
                decision=ApprovalStep.Decision.PENDING
            )
        except ApprovalStep.DoesNotExist:
            return Response({'error': 'No pending approval found for you for this request.'}, status=status.HTTP_404_NOT_FOUND)

        leave_request = approval_step.request
        
        approval_step.decision = decision
        approval_step.comment = request.data.get('comment', '')
        approval_step.decided_at = timezone.now()
        approval_step.save()

        if decision == ApprovalStep.Decision.REJECTED:
            leave_request.status = LeaveRequest.Status.REJECTED
        elif approval_step.role == ApprovalStep.Role.MANAGER:
            hr_step_exists = leave_request.approval_steps.filter(role=ApprovalStep.Role.HR).exists()
            if hr_step_exists and leave_request.approval_steps.filter(role=ApprovalStep.Role.HR, decision=ApprovalStep.Decision.PENDING).exists():
                leave_request.status = LeaveRequest.Status.PENDING_HR
            else:
                leave_request.status = LeaveRequest.Status.APPROVED
        elif approval_step.role == ApprovalStep.Role.HR:
            leave_request.status = LeaveRequest.Status.APPROVED
        
        leave_request.save()

        serializer = LeaveRequestSerializer(leave_request, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='(?P<request_id>[^/.]+)/approve')
    def approve(self, request, request_id=None):
        return self.make_decision(request, request_id, ApprovalStep.Decision.APPROVED)

    @action(detail=False, methods=['post'], url_path='(?P<request_id>[^/.]+)/reject')
    def reject(self, request, request_id=None):
        return self.make_decision(request, request_id, ApprovalStep.Decision.REJECTED)
