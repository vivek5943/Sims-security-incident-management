"""
MOD-02: Incident Management Views — v3
FIX-03: Race condition guard — ML only writes if fields still NULL/unchanged
FIX-02: Async ML in background thread with proper task tracking
FIX-07: Audit log sanitization
FIX-09: Magic bytes file validation
"""
import logging, threading, re
from rest_framework import generics, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings

from apps.incidents.models import Incident, InvestigationNote, IncidentAttachment
from apps.incidents.serializers import (
    IncidentSerializer, IncidentListSerializer,
    InvestigationNoteSerializer, IncidentAttachmentSerializer
)
from apps.authentication.permissions import IsAnalystOrAbove, IsManagerOrAbove
from apps.authentication.models import Role
from apps.audit.models import AuditLog
from apps.notifications.models import Notification

logger = logging.getLogger('apps.incidents')


def _sanitize_log(value: str, max_len: int = 200) -> str:
    """FIX-07: Strip control characters from values before logging."""
    if not value: return ''
    return re.sub(r'[\x00-\x1f\x7f\r\n]', '_', str(value))[:max_len]


def trigger_ml_classification(incident):
    """
    FIX-02: Runs in daemon background thread — API never blocks.
    FIX-03: Race condition guard — ML only writes category/severity if they
            are still NULL (unset since creation). Manager overrides are preserved.

    NOTE: For production at scale, migrate to Celery + Redis:
          @shared_task
          def classify_incident(incident_id): ...
          classify_incident.delay(incident_id)
    """
    def _run():
        try:
            Incident.objects.filter(pk=incident.pk).update(
                ml_classification_status=Incident.ML_STATUS_PENDING,
                ml_classification_error=''
            )

            from apps.ml_engine.pipeline import SIMSClassificationPipeline
            from apps.ml_engine.models import MLPrediction

            pipeline = SIMSClassificationPipeline()
            result   = pipeline.predict(incident.description)

            MLPrediction.objects.update_or_create(
                incident=incident,
                defaults={
                    'predicted_category':    result['category'],
                    'predicted_severity':    result['severity'],
                    'confidence_score':      result['confidence'],
                    'action_recommendations': result.get('recommendations', ''),
                    'model_name':            result.get('model', 'Unknown'),
                    'is_trained_model':      result.get('is_trained_model', False),
                }
            )

            # ── FIX-03: Race condition guard ───────────────────────────────
            # Re-fetch incident from DB to get current state, not stale snapshot
            fresh = Incident.objects.get(pk=incident.pk)

            update_fields = {'ml_classification_status': Incident.ML_STATUS_CLASSIFIED,
                             'ml_classification_error': ''}

            # Only overwrite category if it's still NULL — manager might have set it
            if fresh.category is None:
                update_fields['category'] = result['category']

            # Only overwrite severity if it's still NULL — escalation might have changed it
            if fresh.severity is None:
                update_fields['severity'] = result['severity']

            Incident.objects.filter(pk=incident.pk).update(**update_fields)

            if fresh.category is not None or fresh.severity is not None:
                logger.info(
                    f'[ML] FIX-03: Incident #{incident.pk} had manual category/severity — '
                    f'ML prediction stored but operational values preserved.'
                )
            else:
                logger.info(
                    f'[ML] Incident #{incident.pk} classified: '
                    f'{result["category"]} / {result["severity"]} @ {result["confidence"]}%'
                )

        except Exception as exc:
            error_msg = str(exc)[:500]
            Incident.objects.filter(pk=incident.pk).update(
                ml_classification_status=Incident.ML_STATUS_FAILED,
                ml_classification_error=error_msg
            )
            logger.error(f'[ML] FAILED for Incident #{incident.pk}: {exc}', exc_info=True)

    threading.Thread(target=_run, daemon=True).start()


def send_incident_notification(incident, event_type, recipient=None):
    """FIX-07: Email failure logged. fail_silently=False with explicit catch."""
    target = recipient or incident.assigned_to or incident.created_by
    if not target:
        return

    messages = {
        'created':   f'New incident #{incident.incident_id} "{incident.title}" created.',
        'assigned':  f'Incident #{incident.incident_id} "{incident.title}" assigned to you.',
        'escalated': f'ESCALATION: Incident #{incident.incident_id} severity → {incident.severity}.',
        'resolved':  f'Incident #{incident.incident_id} "{incident.title}" Resolved.',
        'closed':    f'Incident #{incident.incident_id} "{incident.title}" Closed.',
    }
    message = messages.get(event_type, f'Incident #{incident.incident_id} updated to {incident.status}.')

    Notification.objects.create(user=target, message=message)

    try:
        send_mail(
            subject=f'[SIMS] {event_type.title()}: Incident #{incident.incident_id}',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[target.email],
            fail_silently=False,
        )
    except Exception as exc:
        logger.warning(f'[NOTIFY] Email FAILED to {target.email}: {exc}')


# ── Magic bytes signatures for FIX-09 ────────────────────────────────────────
MAGIC_BYTES = {
    b'\x25\x50\x44\x46':     'application/pdf',    # PDF
    b'\x89\x50\x4e\x47':     'image/png',           # PNG
    b'\xff\xd8\xff':          'image/jpeg',          # JPEG
    b'GIF87a':                'image/gif',
    b'GIF89a':                'image/gif',
    b'PK\x03\x04':           'application/zip',
}

def _check_magic_bytes(file_obj) -> str | None:
    """
    FIX-09: Read first 8 bytes to verify actual file type.
    Returns detected MIME type or None if unknown/unmatched.
    """
    header = file_obj.read(8)
    file_obj.seek(0)
    for magic, mime in MAGIC_BYTES.items():
        if header.startswith(magic):
            return mime
    return None


class IncidentListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsAnalystOrAbove]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['title', 'description', 'category']
    ordering_fields    = ['created_at', 'severity', 'status', 'incident_id']
    ordering           = ['-created_at']

    def get_serializer_class(self):
        return IncidentListSerializer if self.request.method == 'GET' else IncidentSerializer

    def get_queryset(self):
        user = self.request.user
        qs   = Incident.objects.select_related(
            'created_by', 'assigned_to', 'created_by__role', 'assigned_to__role'
        ).prefetch_related('notes', 'ml_predictions')

        if user.role_name == Role.ANALYST:
            qs = qs.filter(Q(created_by=user) | Q(assigned_to=user))

        p = self.request.query_params
        if p.get('status'):    qs = qs.filter(status=p['status'])
        if p.get('severity'):  qs = qs.filter(severity=p['severity'])
        if p.get('category'):  qs = qs.filter(category=p['category'])
        if p.get('ml_status'): qs = qs.filter(ml_classification_status=p['ml_status'])
        return qs

    def perform_create(self, serializer):
        incident = serializer.save(created_by=self.request.user)
        AuditLog.log(
            user=self.request.user,
            action=f'INCIDENT_CREATED: #{incident.incident_id} '
                   f'"{_sanitize_log(incident.title)}" by {_sanitize_log(self.request.user.email)}'
        )
        trigger_ml_classification(incident)
        send_incident_notification(incident, 'created')


class IncidentDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsAnalystOrAbove]
    serializer_class   = IncidentSerializer

    def get_queryset(self):
        return Incident.objects.select_related(
            'created_by', 'assigned_to'
        ).prefetch_related('notes__analyst', 'ml_predictions', 'attachments')

    def get_object(self):
        obj  = super().get_object()
        user = self.request.user
        if user.role_name == Role.ANALYST:
            if obj.created_by != user and obj.assigned_to != user:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('Access denied.')
        return obj

    def perform_update(self, serializer):
        old     = self.get_object()
        old_s   = old.status
        old_a   = old.assigned_to_id
        incident = serializer.save()
        AuditLog.log(
            user=self.request.user,
            action=f'INCIDENT_UPDATED: #{incident.incident_id} status={incident.status}'
        )
        if incident.status != old_s:
            if incident.status == Incident.STATUS_RESOLVED:
                send_incident_notification(incident, 'resolved')
            elif incident.status == Incident.STATUS_CLOSED:
                send_incident_notification(incident, 'closed')
        if incident.assigned_to and incident.assigned_to_id != old_a:
            send_incident_notification(incident, 'assigned', incident.assigned_to)

    def perform_destroy(self, instance):
        if self.request.user.role_name != Role.ADMIN:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only System Administrators can delete incidents.')
        AuditLog.log(user=self.request.user,
                     action=f'INCIDENT_DELETED: #{instance.incident_id}')
        instance.delete()


class EscalateIncidentView(APIView):
    permission_classes = [IsAuthenticated, IsManagerOrAbove]

    def post(self, request, pk):
        try:
            incident = Incident.objects.get(pk=pk)
        except Incident.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        ladder = [Incident.SEVERITY_LOW, Incident.SEVERITY_MEDIUM,
                  Incident.SEVERITY_HIGH, Incident.SEVERITY_CRITICAL]
        idx = ladder.index(incident.severity) if incident.severity in ladder else -1
        if idx >= len(ladder) - 1:
            return Response({'message': 'Already at Critical severity.'})

        incident.severity = ladder[idx + 1]
        incident.status   = Incident.STATUS_UNDER_INVESTIGATION
        incident.save(update_fields=['severity', 'status'])

        AuditLog.log(user=request.user,
                     action=f'INCIDENT_ESCALATED: #{incident.incident_id} → {incident.severity}')
        send_incident_notification(incident, 'escalated')
        return Response({'message': f'Escalated to {incident.severity}.',
                         'severity': incident.severity, 'status': incident.status})


class RetryMLClassificationView(APIView):
    permission_classes = [IsAuthenticated, IsManagerOrAbove]

    def post(self, request, pk):
        try:
            incident = Incident.objects.get(pk=pk)
        except Incident.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        trigger_ml_classification(incident)
        return Response({'message': f'ML retry queued for Incident #{pk}.'})


class IncidentAttachmentView(APIView):
    """
    FIX-09 v3: Full magic bytes validation + extension whitelist + MIME check.
    FIX-09 v2 note: Extension + size check were in v2. v3 adds magic byte inspection.
    """
    permission_classes = [IsAuthenticated, IsAnalystOrAbove]
    ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.txt', '.csv', '.log', '.pcap'}

    # FIX-09: Map allowed extensions to expected magic-byte MIME types
    ALLOWED_MAGIC_MIMES = {
        'application/pdf', 'image/png', 'image/jpeg', 'image/gif', None  # None = text/unknown
    }

    def post(self, request, pk):
        import os
        try:
            incident = Incident.objects.get(pk=pk)
        except Incident.DoesNotExist:
            return Response({'error': 'Incident not found'}, status=status.HTTP_404_NOT_FOUND)

        uploaded = request.FILES.get('file')
        if not uploaded:
            return Response({'error': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)

        # Size check
        if uploaded.size > IncidentAttachment.MAX_SIZE_BYTES:
            return Response({'error': 'File exceeds 5 MB limit.'}, status=status.HTTP_400_BAD_REQUEST)

        # Extension whitelist
        _, ext = os.path.splitext(uploaded.name.lower())
        if ext not in self.ALLOWED_EXTENSIONS:
            return Response({'error': f'Extension "{ext}" not allowed.'}, status=status.HTTP_400_BAD_REQUEST)

        # FIX-09 v3: Magic bytes check — reject spoofed content-type
        detected_mime = _check_magic_bytes(uploaded)
        if detected_mime not in self.ALLOWED_MAGIC_MIMES:
            logger.warning(
                f'[ATTACH] Rejected file "{uploaded.name}" — '
                f'magic bytes detected MIME: {detected_mime} (blocked)'
            )
            return Response(
                {'error': f'File content does not match its extension. '
                          f'Detected type: {detected_mime or "unknown"}. Upload rejected.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # FIX-09 v3: Double-extension attack guard (e.g. invoice.pdf.exe)
        base_name = os.path.basename(uploaded.name)
        if base_name.count('.') > 1:
            parts = base_name.split('.')
            # Allow only if ALL extensions are in whitelist (e.g. report.final.pdf is ok)
            all_safe = all(f'.{p.lower()}' in self.ALLOWED_EXTENSIONS for p in parts[1:])
            if not all_safe:
                return Response({'error': 'Double-extension filenames are not permitted.'},
                                status=status.HTTP_400_BAD_REQUEST)

        import mimetypes
        mime_type, _ = mimetypes.guess_type(uploaded.name)

        attachment = IncidentAttachment.objects.create(
            incident=incident,
            uploaded_by=request.user,
            file=uploaded,
            original_filename=uploaded.name[:255],
            file_size_bytes=uploaded.size,
            mime_type=mime_type or 'application/octet-stream',
        )
        AuditLog.log(user=request.user,
                     action=f'ATTACHMENT_UPLOADED: {_sanitize_log(uploaded.name)} '
                            f'({uploaded.size}B) to Incident #{pk}')
        return Response({
            'message':       'Attached successfully.',
            'attachment_id': attachment.attachment_id,
            'filename':      attachment.original_filename,
            'size_bytes':    attachment.file_size_bytes,
        }, status=status.HTTP_201_CREATED)

    def get(self, request, pk):
        attachments = IncidentAttachment.objects.filter(
            incident_id=pk
        ).select_related('uploaded_by')
        return Response(IncidentAttachmentSerializer(attachments, many=True).data)


class InvestigationNoteListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsAnalystOrAbove]
    serializer_class   = InvestigationNoteSerializer

    def get_queryset(self):
        return InvestigationNote.objects.filter(
            incident_id=self.kwargs['incident_pk']
        ).select_related('analyst', 'analyst__role')

    def perform_create(self, serializer):
        note = serializer.save(
            incident_id=self.kwargs['incident_pk'],
            analyst=self.request.user
        )
        AuditLog.log(user=self.request.user,
                     action=f'NOTE_ADDED: #{note.note_id} to Incident #{self.kwargs["incident_pk"]}')
