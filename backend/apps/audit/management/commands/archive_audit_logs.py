"""
FIX-10: Audit Log Archiving Management Command
Moves old audit entries to a compressed archive file before deletion.
Run via cron: 0 2 * * 0 python manage.py archive_audit_logs
"""
import csv
import gzip
from datetime import timedelta
from pathlib import Path
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings


class Command(BaseCommand):
    help = 'Archive audit log entries older than AUDIT_LOG_ARCHIVE_DAYS to compressed CSV, then delete'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Show what would be archived without deleting')
        parser.add_argument('--days', type=int, default=None,
                            help='Override AUDIT_LOG_ARCHIVE_DAYS setting')

    def handle(self, *args, **options):
        from apps.audit.models import AuditLog

        archive_days = options['days'] or getattr(settings, 'AUDIT_LOG_ARCHIVE_DAYS', 90)
        cutoff = timezone.now() - timedelta(days=archive_days)

        old_logs = AuditLog.objects.filter(timestamp__lt=cutoff).select_related('user')
        count = old_logs.count()

        if count == 0:
            self.stdout.write(f'  ℹ  No audit logs older than {archive_days} days. Nothing to archive.')
            return

        self.stdout.write(self.style.WARNING(
            f'\n  Found {count} audit log entries older than {archive_days} days (before {cutoff.date()})'
        ))

        if options['dry_run']:
            self.stdout.write('  DRY RUN — no changes made.\n')
            return

        # Write to gzip-compressed CSV archive
        archive_dir = Path(settings.BASE_DIR) / 'audit_archives'
        archive_dir.mkdir(exist_ok=True)
        archive_file = archive_dir / f'audit_archive_{cutoff.date()}.csv.gz'

        with gzip.open(archive_file, 'wt', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['log_id', 'user_email', 'action', 'ip_address', 'timestamp'])
            for log in old_logs.iterator(chunk_size=1000):
                writer.writerow([
                    log.log_id,
                    log.user.email if log.user else 'System',
                    log.action,
                    log.ip_address or '',
                    log.timestamp.isoformat(),
                ])

        # Delete archived entries in batches to avoid locking table
        deleted_total = 0
        while True:
            batch_ids = list(
                AuditLog.objects.filter(timestamp__lt=cutoff)
                .values_list('log_id', flat=True)[:5000]
            )
            if not batch_ids:
                break
            deleted, _ = AuditLog.objects.filter(log_id__in=batch_ids).delete()
            deleted_total += deleted

        self.stdout.write(self.style.SUCCESS(
            f'  ✅ Archived {count} entries to {archive_file}\n'
            f'  ✅ Deleted {deleted_total} entries from live table.\n'
        ))
