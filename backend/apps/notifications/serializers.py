"""MOD-05: Notification Serializers"""
from rest_framework import serializers
from apps.notifications.models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['notification_id', 'message', 'status', 'timestamp']
        read_only_fields = ['notification_id', 'message', 'timestamp']
