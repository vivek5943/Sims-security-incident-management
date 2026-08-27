"""MOD-06: Audit Log Views"""
from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
from apps.audit.models import AuditLog
from apps.audit.serializers import AuditLogSerializer
from apps.authentication.permissions import IsManagerOrAbove

class AuditLogListView(generics.ListAPIView):
    """GET /api/v1/audit/ — Paginated audit log viewer (Manager+)"""
    permission_classes = [IsAuthenticated, IsManagerOrAbove]
    serializer_class = AuditLogSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['action', 'user__email', 'user__full_name']
    ordering_fields = ['timestamp', 'log_id']
    ordering = ['-timestamp']

    def get_queryset(self):
        qs = AuditLog.objects.select_related('user', 'user__role')
        params = self.request.query_params
        if params.get('user_id'):
            qs = qs.filter(user__user_id=params['user_id'])
        if params.get('date_from'):
            qs = qs.filter(timestamp__date__gte=params['date_from'])
        if params.get('date_to'):
            qs = qs.filter(timestamp__date__lte=params['date_to'])
        return qs
