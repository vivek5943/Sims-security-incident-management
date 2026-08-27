"""
MOD-02: Incident Management System
FIX-05: Added ALL 8 categories from synopsis (was missing Data Breach,
        Unauthorized Access, Social Engineering)
FIX-03: Added ml_classification_status field — tracks ML job state
FIX-11/12: ml_classification_status + source-of-truth comment for severity/category
"""
from django.db import models
from django.utils import timezone


class Incident(models.Model):
    STATUS_OPEN = 'Open'
    STATUS_ASSIGNED = 'Assigned'
    STATUS_IN_PROGRESS = 'In Progress'
    STATUS_UNDER_INVESTIGATION = 'Under Investigation'
    STATUS_RESOLVED = 'Resolved'
    STATUS_CLOSED = 'Closed'

    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_ASSIGNED, 'Assigned'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_UNDER_INVESTIGATION, 'Under Investigation'),
        (STATUS_RESOLVED, 'Resolved'),
        (STATUS_CLOSED, 'Closed'),
    ]

    # FIX-05: Full 8-category taxonomy matching synopsis exactly
    CATEGORY_PHISHING = 'Phishing'
    CATEGORY_MALWARE = 'Malware'
    CATEGORY_RANSOMWARE = 'Ransomware'
    CATEGORY_DDOS = 'DDoS'
    CATEGORY_INSIDER = 'Insider Threat'
    CATEGORY_DATA_BREACH = 'Data Breach'          # ADDED — was missing
    CATEGORY_UNAUTHORIZED = 'Unauthorized Access'  # ADDED — was missing
    CATEGORY_SOCIAL = 'Social Engineering'         # ADDED — was missing

    CATEGORY_CHOICES = [
        (CATEGORY_PHISHING, 'Phishing'),
        (CATEGORY_MALWARE, 'Malware'),
        (CATEGORY_RANSOMWARE, 'Ransomware'),
        (CATEGORY_DDOS, 'DDoS'),
        (CATEGORY_INSIDER, 'Insider Threat'),
        (CATEGORY_DATA_BREACH, 'Data Breach'),
        (CATEGORY_UNAUTHORIZED, 'Unauthorized Access'),
        (CATEGORY_SOCIAL, 'Social Engineering'),
    ]

    SEVERITY_LOW = 'Low'
    SEVERITY_MEDIUM = 'Medium'
    SEVERITY_HIGH = 'High'
    SEVERITY_CRITICAL = 'Critical'

    SEVERITY_CHOICES = [
        (SEVERITY_LOW, 'Low'),
        (SEVERITY_MEDIUM, 'Medium'),
        (SEVERITY_HIGH, 'High'),
        (SEVERITY_CRITICAL, 'Critical'),
    ]

    # FIX-03: ML classification job status — tracks whether ML ran, failed, or is pending
    ML_STATUS_PENDING = 'pending'
    ML_STATUS_CLASSIFIED = 'classified'
    ML_STATUS_FAILED = 'failed'
    ML_STATUS_CHOICES = [
        (ML_STATUS_PENDING, 'Pending Classification'),
        (ML_STATUS_CLASSIFIED, 'Classified'),
        (ML_STATUS_FAILED, 'Classification Failed'),
    ]

    incident_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    indicators_of_compromise = models.TextField(blank=True, default='')

    # ── FIX-11/12: Source of truth for category and severity ─────────────────
    # category and severity on this model are the OPERATIONAL values.
    # They are initially populated by the ML engine on incident creation.
    # Managers may override them manually (e.g., escalation changes severity).
    # MLPrediction.predicted_category/severity are the raw ML outputs — kept for
    # audit and accuracy analysis, but the Incident fields are the system-of-record.
    # ─────────────────────────────────────────────────────────────────────────
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, null=True, blank=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, null=True, blank=True)

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_OPEN)

    # FIX-03: ML job state — incident is always created, ML status tracked separately
    ml_classification_status = models.CharField(
        max_length=20, choices=ML_STATUS_CHOICES, default=ML_STATUS_PENDING,
        db_index=True
    )
    ml_classification_error = models.TextField(blank=True, default='')

    assigned_to = models.ForeignKey(
        'authentication.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_incidents', db_column='assigned_to'
    )
    created_by = models.ForeignKey(
        'authentication.User', on_delete=models.PROTECT,
        related_name='created_incidents', db_column='created_by'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'incidents'
        verbose_name = 'Incident'
        verbose_name_plural = 'Incidents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status'], name='idx_incident_status'),
            models.Index(fields=['severity'], name='idx_incident_severity'),
            models.Index(fields=['category'], name='idx_incident_category'),
            models.Index(fields=['-created_at'], name='idx_incident_created'),
            models.Index(fields=['ml_classification_status'], name='idx_incident_ml_status'),
        ]

    def __str__(self):
        return f"[{self.incident_id}] {self.title} — {self.status}"


class InvestigationNote(models.Model):
    note_id = models.AutoField(primary_key=True)
    incident = models.ForeignKey(
        Incident, on_delete=models.CASCADE,
        related_name='notes', db_column='incident_id'
    )
    analyst = models.ForeignKey(
        'authentication.User', on_delete=models.PROTECT,
        related_name='investigation_notes', db_column='analyst_id'
    )
    notes = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'investigation_notes'
        verbose_name = 'Investigation Note'
        verbose_name_plural = 'Investigation Notes'
        ordering = ['-timestamp']

    def __str__(self):
        return f"Note #{self.note_id} — Incident #{self.incident_id}"


# FIX-09: Incident evidence file attachments with strict validation
class IncidentAttachment(models.Model):
    ALLOWED_EXTENSIONS = ['.pdf', '.png', '.jpg', '.jpeg', '.txt', '.csv', '.log', '.pcap']
    MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

    attachment_id = models.AutoField(primary_key=True)
    incident = models.ForeignKey(
        Incident, on_delete=models.CASCADE,
        related_name='attachments', db_column='incident_id'
    )
    uploaded_by = models.ForeignKey(
        'authentication.User', on_delete=models.PROTECT,
        related_name='uploaded_attachments', db_column='uploaded_by'
    )
    file = models.FileField(upload_to='incident_attachments/%Y/%m/')
    original_filename = models.CharField(max_length=255)
    file_size_bytes = models.PositiveIntegerField()
    mime_type = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'incident_attachments'
        verbose_name = 'Incident Attachment'
        verbose_name_plural = 'Incident Attachments'

    def __str__(self):
        return f"Attachment #{self.attachment_id} — {self.original_filename}"
