"""MOD-05: Notification Management Views"""
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer

class NotificationListView(generics.ListAPIView):
    """GET /api/v1/notifications/ — User's notification feed"""
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        qs = Notification.objects.filter(user=self.request.user)
        if self.request.query_params.get('unread_only') == 'true':
            qs = qs.filter(status=Notification.STATUS_UNREAD)
        return qs

class MarkNotificationReadView(APIView):
    """PATCH /api/v1/notifications/<id>/read/ — Mark single notification as read"""
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            notif = Notification.objects.get(pk=pk, user=request.user)
            notif.status = Notification.STATUS_READ
            notif.save(update_fields=['status'])
            return Response({'message': 'Marked as read.'})
        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)

class MarkAllReadView(APIView):
    """PATCH /api/v1/notifications/mark-all-read/ — Bulk mark all read"""
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        count = Notification.objects.filter(
            user=request.user,
            status=Notification.STATUS_UNREAD
        ).update(status=Notification.STATUS_READ)
        return Response({'message': f'{count} notifications marked as read.'})

class UnreadCountView(APIView):
    """GET /api/v1/notifications/unread-count/ — Badge counter for UI"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(
            user=request.user,
            status=Notification.STATUS_UNREAD
        ).count()
        return Response({'unread_count': count})
