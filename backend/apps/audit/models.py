"""
MOD-06: Audit Logging Ledger
FIX-10: Added DB indexes for high-volume query performance + AuditLog.log() class method
"""
from django.db import models
from django.utils import timezone
import logging

logger = logging.getLogger('sims')


class AuditLog(models.Model):
    log_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='audit_logs', db_column='user_id'
    )
    action = models.CharField(max_length=500)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    # FIX-10: Composite index — timestamp + user for filtered queries on large tables
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = 'audit_logs'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']
        default_permissions = ('add', 'view')
        indexes = [
            models.Index(fields=['-timestamp'], name='idx_audit_timestamp'),
            models.Index(fields=['user', '-timestamp'], name='idx_audit_user_ts'),
            models.Index(fields=['action'], name='idx_audit_action'),
        ]

    def __str__(self):
        u = self.user.email if self.user else 'System'
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {u}: {self.action}"

    @classmethod
    def log(cls, *, user=None, action: str, ip: str = None):
        """
        FIX-03 / FIX-10: Central audit log writer.
        Never raises — audit failures must not break business logic.
        Logs to structured logger so ops can monitor even if DB is down.
        """
        try:
            entry = cls.objects.create(user=user, action=action, ip_address=ip)
            logger.info(f'[AUDIT] {action}')
            return entry
        except Exception as exc:
            # Audit write failure — log to file but do NOT crash the request
            logger.error(f'[AUDIT WRITE FAILED] {action} | reason={exc}')
            return None
