"""
MOD-05: Notification Management
Model — NOTIFICATIONS table (Schema Section 12)

TABLE: NOTIFICATIONS
notification_id PK | user_id FK CASCADE | message TEXT |
status DEFAULT 'Unread' | timestamp TIMESTAMP
"""
from django.db import models
from django.utils import timezone


class Notification(models.Model):
    STATUS_UNREAD = 'Unread'
    STATUS_READ = 'Read'
    STATUS_CHOICES = [
        (STATUS_UNREAD, 'Unread'),
        (STATUS_READ, 'Read'),
    ]

    notification_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        'authentication.User',
        on_delete=models.CASCADE,
        related_name='notifications',
        db_column='user_id'
    )
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_UNREAD)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-timestamp']

    def __str__(self):
        return f"Notification #{self.notification_id} → {self.user.email}: {self.message[:60]}"
