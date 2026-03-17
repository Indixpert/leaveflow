from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import LeaveRequest, LeaveType, ApprovalStep
from .serializers import LeaveRequestSerializer, LeaveTypeSerializer, ApprovalStepSerializer

class LeaveTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows leave types to be viewed.
    """
    queryset = LeaveType.objects.all()
    serializer_class = LeaveTypeSerializer
    permission_classes = [IsAuthenticated]

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
