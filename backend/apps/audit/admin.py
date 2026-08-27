from django.contrib import admin
from apps.audit.models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['log_id', 'user', 'action', 'ip_address', 'timestamp']
    list_filter = ['timestamp']
    search_fields = ['action', 'user__email']
    readonly_fields = ['log_id', 'user', 'action', 'ip_address', 'timestamp']
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
