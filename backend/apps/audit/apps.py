from django.apps import AppConfig
class AuditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.audit'
    label = 'audit'
    verbose_name = 'MOD-06: Audit Logging Ledger'
