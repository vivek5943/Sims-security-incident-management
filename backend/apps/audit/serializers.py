"""MOD-06: Audit Log Serializers"""
from rest_framework import serializers
from apps.audit.models import AuditLog
from apps.authentication.serializers import UserProfileSerializer

class AuditLogSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    class Meta:
        model = AuditLog
        fields = ['log_id', 'user', 'action', 'ip_address', 'timestamp']
        read_only_fields = fields
