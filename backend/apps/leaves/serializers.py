from rest_framework import serializers
from .models import LeaveRequest, LeaveType, ApprovalStep
from ..accounts.serializers import UserSerializer

class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = '__all__'

class ApprovalStepSerializer(serializers.ModelSerializer):
    approver = UserSerializer(read_only=True)

    class Meta:
        model = ApprovalStep
        fields = ['approver', 'role', 'decision', 'comment', 'decided_at']

class LeaveRequestSerializer(serializers.ModelSerializer):
    employee = UserSerializer(read_only=True)
    leave_type = serializers.StringRelatedField()
    approval_steps = ApprovalStepSerializer(many=True, read_only=True)

    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'employee', 'leave_type', 'start_date', 'end_date',
            'total_days', 'reason', 'document', 'status', 'created_at',
            'updated_at', 'approval_steps'
        ]

class LeaveRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'reason', 'document']

    def create(self, validated_data):
        request = self.context['request']
        validated_data['employee'] = request.user
        return super().create(validated_data)
