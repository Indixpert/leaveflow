from rest_framework import viewsets, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from .models import LeaveRequest, LeaveType, PublicHoliday, ApprovalStep
from .serializers import (
    LeaveRequestSerializer, 
    LeaveTypeSerializer, 
    PublicHolidaySerializer, 
    ApprovalStepSerializer,
    LeaveRequestCreateSerializer
)

class LeaveTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LeaveType.objects.all()
    serializer_class = LeaveTypeSerializer
    permission_classes = [permissions.IsAuthenticated]

class PublicHolidayViewSet(viewsets.ModelViewSet):
    queryset = PublicHoliday.objects.all()
    serializer_class = PublicHolidaySerializer
    permission_classes = [permissions.IsAdminUser]

class LeaveRequestViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_class(self):
        if self.action == 'create':
            return LeaveRequestCreateSerializer
        return LeaveRequestSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return LeaveRequest.objects.select_related('employee', 'leave_type').prefetch_related('approval_steps__approver').all()
        
        # In a real app, you might also return requests for employees managed by the user.
        return LeaveRequest.objects.filter(employee=user).select_related('employee', 'leave_type').prefetch_related('approval_steps__approver')

    def perform_create(self, serializer):
        serializer.save(employee=self.request.user)

class ApprovalViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ApprovalStepSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ApprovalStep.objects.filter(approver=self.request.user).select_related('request__employee', 'request__leave_type')

    # Add custom actions for 'approve' and 'reject' in a real implementation
