"""MOD-05: Notification Management URL Routes"""
from django.urls import path
from apps.notifications.views import (
    NotificationListView, MarkNotificationReadView, MarkAllReadView, UnreadCountView
)
urlpatterns = [
    path('', NotificationListView.as_view(), name='notification_list'),
    path('unread-count/', UnreadCountView.as_view(), name='unread_count'),
    path('mark-all-read/', MarkAllReadView.as_view(), name='mark_all_read'),
    path('<int:pk>/read/', MarkNotificationReadView.as_view(), name='mark_read'),
]
