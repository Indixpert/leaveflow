from rest_framework import serializers
from .models import LeaveType, LeaveRequest, ApprovalStep, PublicHoliday
from ..accounts.serializers import UserSerializer

class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = '__all__'

class PublicHolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicHoliday
        fields = '__all__'

class ApprovalStepSerializer(serializers.ModelSerializer):
    approver = UserSerializer(read_only=True)

    class Meta:
        model = ApprovalStep
        fields = ['id', 'approver', 'role', 'decision', 'comment', 'decided_at']

class LeaveRequestSerializer(serializers.ModelSerializer):
    employee = UserSerializer(read_only=True)
    leave_type = LeaveTypeSerializer(read_only=True)
    leave_type_id = serializers.PrimaryKeyRelatedField(
        queryset=LeaveType.objects.all(), source='leave_type', write_only=True
    )
    approval_steps = ApprovalStepSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'employee', 'leave_type', 'leave_type_id', 'start_date', 'end_date',
            'total_days', 'reason', 'document', 'status', 'status_display', 'approval_steps',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'employee', 'total_days', 'status', 'status_display', 'approval_steps', 'created_at', 'updated_at', 'document']

    def create(self, validated_data):
        validated_data['employee'] = self.context['request'].user
        leave_request = super().create(validated_data)
        
        # This is a simplified workflow. A real app might have a more complex hierarchy.
        manager = getattr(self.context['request'].user, 'manager', None)
        if manager:
            ApprovalStep.objects.create(
                request=leave_request,
                approver=manager,
                role=ApprovalStep.ApproverRole.MANAGER
            )
            leave_request.status = LeaveRequest.Status.PENDING_MANAGER
        else:
            # If no manager, maybe it goes straight to HR or is auto-approved depending on rules
            leave_request.status = LeaveRequest.Status.PENDING_HR
        
        leave_request.save()
        return leave_request

class LeaveRequestCreateSerializer(serializers.ModelSerializer):
    document = serializers.FileField(required=False, write_only=True)

    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'reason', 'document']

    def validate(self, data):
        leave_type = data.get('leave_type')
        document = data.get('document')
        if leave_type and leave_type.requires_document and not document:
            raise serializers.ValidationError({'document': 'A supporting document is required for this leave type.'})
        if data.get('start_date') > data.get('end_date'):
            raise serializers.ValidationError({'end_date': 'End date cannot be before start date.'})
        return data
