from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import LeaveType, LeaveRequest, ApprovalStep

User = get_user_model()

class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = '__all__'

class ApprovalStepSerializer(serializers.ModelSerializer):
    approver = serializers.StringRelatedField()

    class Meta:
        model = ApprovalStep
        fields = ['approver', 'role', 'decision', 'comment', 'decided_at']

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']

class LeaveRequestSerializer(serializers.ModelSerializer):
    employee = EmployeeSerializer(read_only=True)
    leave_type = serializers.StringRelatedField(read_only=True)
    leave_type_id = serializers.PrimaryKeyRelatedField(
        queryset=LeaveType.objects.all(), source='leave_type', write_only=True
    )
    approval_steps = ApprovalStepSerializer(many=True, read_only=True)

    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'employee', 'leave_type', 'leave_type_id', 'start_date', 'end_date',
            'total_days', 'reason', 'document', 'status', 'created_at',
            'updated_at', 'approval_steps'
        ]
        read_only_fields = ['id', 'employee', 'total_days', 'status', 'created_at', 'updated_at', 'approval_steps']

    def create(self, validated_data):
        request = self.context['request']
        validated_data['employee'] = request.user
        
        # This is a simplified workflow. A real app would have more complex logic
        # to determine the approvers (e.g., from an employee-manager hierarchy).
        validated_data['status'] = LeaveRequest.Status.PENDING_MANAGER
        
        leave_request = super().create(validated_data)

        # Placeholder: Find manager and HR approver and create ApprovalStep objects.
        # In a real system, you'd look up the user's manager.
        # For now, we assume this is handled by a separate process or signal.

        return leave_request
