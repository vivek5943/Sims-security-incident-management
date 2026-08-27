from django.contrib import admin
from apps.notifications.models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['notification_id', 'user', 'status', 'timestamp']
    list_filter = ['status']
