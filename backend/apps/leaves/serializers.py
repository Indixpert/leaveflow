from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import LeaveType, LeaveRequest, ApprovalStep

User = get_user_model()

class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = '__all__'

class ApprovalStepSerializer(serializers.ModelSerializer):
    approver_name = serializers.CharField(source='approver.get_full_name', read_only=True)

    class Meta:
        model = ApprovalStep
        fields = ['id', 'approver', 'approver_name', 'role', 'decision', 'comment', 'decided_at']
        read_only_fields = ['approver_name', 'decided_at']

class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approval_steps = ApprovalStepSerializer(many=True, read_only=True)

    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'employee', 'employee_name', 'leave_type', 'leave_type_name',
            'start_date', 'end_date', 'total_days', 'reason', 'document',
            'status', 'status_display', 'created_at', 'updated_at', 'approval_steps'
        ]
        read_only_fields = ['total_days', 'employee', 'status', 'created_at', 'updated_at', 'approval_steps']

    def create(self, validated_data):
        request = self.context['request']
        validated_data['employee'] = request.user
        validated_data['status'] = LeaveRequest.Status.DRAFT
        
        leave_request = LeaveRequest.objects.create(**validated_data)
        
        # This is a simplified logic for creating approval steps.
        # A real implementation would look up the user's manager and the company's HR.
        # For now, we'll assume a user with is_staff=True is a manager and is_superuser=True is HR.
        manager = User.objects.filter(is_staff=True, is_superuser=False).first()
        if manager:
            ApprovalStep.objects.create(request=leave_request, approver=manager, role=ApprovalStep.Role.MANAGER)

        hr_user = User.objects.filter(is_superuser=True).first()
        if hr_user:
            ApprovalStep.objects.create(request=leave_request, approver=hr_user, role=ApprovalStep.Role.HR)

        return leave_request

    def validate(self, data):
        """
        Check that the start is before the end.
        """
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError("End date must occur after start date.")
        return data
