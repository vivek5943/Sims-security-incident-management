"""
MOD-06: Audit Log Middleware
FIX-06: Logs auth failures using AuditLog.log() (never crashes request)
"""
import logging

logger = logging.getLogger('sims')

AUDITABLE_PATHS = ['/api/v1/auth/', '/api/v1/incidents/', '/api/v1/ml/', '/api/v1/reports/']
SKIP_METHODS = ['GET', 'HEAD', 'OPTIONS']


class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.method in SKIP_METHODS:
            return response

        is_auditable = any(request.path.startswith(p) for p in AUDITABLE_PATHS)
        if not is_auditable:
            return response

        if response.status_code in [401, 403]:
            from apps.audit.models import AuditLog
            user = request.user if hasattr(request, 'user') and request.user.is_authenticated else None
            ip = self._get_ip(request)
            AuditLog.log(
                user=user,
                action=f'AUTH_FAILURE: {response.status_code} {request.method} {request.path} from {ip}',
                ip=ip
            )
        return response

    def _get_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR')
