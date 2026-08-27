"""
MOD-07: Reporting Core
PDF and CSV export using ReportLab (Section 8.2 — MOD-07 Functional Capacity).
Generates on-demand executive summaries for Manager+ roles.
"""
import csv
import io
import json
from datetime import datetime

from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.incidents.models import Incident
from apps.ml_engine.models import MLPrediction
from apps.audit.models import AuditLog
from apps.authentication.permissions import IsManagerOrAbove


def generate_pdf_report(title, incidents, summary_stats):
    """
    Generates a professional PDF report using ReportLab.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=25 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    elements = []

    # ── Header ──────────────────────────────────────────────────────────────
    header_style = ParagraphStyle(
        'SIMSHeader',
        fontSize=18, fontName='Helvetica-Bold',
        textColor=colors.HexColor('#1e3a5f'), alignment=TA_CENTER,
        spaceAfter=4
    )
    sub_style = ParagraphStyle(
        'SIMSSub',
        fontSize=10, fontName='Helvetica',
        textColor=colors.HexColor('#64748b'), alignment=TA_CENTER,
        spaceAfter=2
    )
    body_style = ParagraphStyle(
        'SIMSBody', fontSize=9, fontName='Helvetica',
        textColor=colors.HexColor('#374151'), spaceAfter=6
    )
    section_style = ParagraphStyle(
        'SIMSSection', fontSize=11, fontName='Helvetica-Bold',
        textColor=colors.HexColor('#1e3a5f'), spaceBefore=12, spaceAfter=6
    )

    elements.append(Paragraph('SIMS — AI-Powered Security Incident Management System', header_style))
    elements.append(Paragraph('Indira Gandhi National Open University | MCSP-232 Project', sub_style))
    elements.append(Paragraph(title, ParagraphStyle(
        'ReportTitle', fontSize=13, fontName='Helvetica-Bold',
        textColor=colors.HexColor('#dc2626'), alignment=TA_CENTER, spaceBefore=4
    )))
    elements.append(Paragraph(
        f'Generated: {datetime.now().strftime("%d %B %Y, %H:%M UTC")} | '
        f'Classification: CONFIDENTIAL',
        sub_style
    ))
    elements.append(HRFlowable(width='100%', thickness=2, color=colors.HexColor('#1e3a5f')))
    elements.append(Spacer(1, 8))

    # ── Executive Summary ────────────────────────────────────────────────────
    elements.append(Paragraph('1. Executive Summary', section_style))
    summary_data = [
        ['Metric', 'Value'],
        ['Total Incidents', str(summary_stats.get('total', 0))],
        ['Critical Severity', str(summary_stats.get('critical', 0))],
        ['High Severity', str(summary_stats.get('high', 0))],
        ['Open (Unresolved)', str(summary_stats.get('open', 0))],
        ['Resolved', str(summary_stats.get('resolved', 0))],
        ['Closed', str(summary_stats.get('closed', 0))],
        ['ML Predictions Generated', str(summary_stats.get('predictions', 0))],
    ]

    summary_table = Table(summary_data, colWidths=[90 * mm, 60 * mm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 10))

    # ── Incident Log ────────────────────────────────────────────────────────
    elements.append(Paragraph('2. Incident Register', section_style))

    inc_headers = ['ID', 'Title', 'Category', 'Severity', 'Status', 'Assigned To', 'Created']
    inc_data = [inc_headers]

    for inc in incidents[:100]:  # Cap at 100 rows per page limits
        inc_data.append([
            f'#{inc.incident_id}',
            (inc.title[:35] + '...') if len(inc.title) > 35 else inc.title,
            inc.category or 'Pending ML',
            inc.severity or '—',
            inc.status,
            inc.assigned_to.full_name if inc.assigned_to else 'Unassigned',
            inc.created_at.strftime('%d/%m/%Y'),
        ])

    col_widths = [18 * mm, 52 * mm, 28 * mm, 22 * mm, 28 * mm, 28 * mm, 22 * mm]
    inc_table = Table(inc_data, colWidths=col_widths, repeatRows=1)
    inc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#e2e8f0')),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        # Severity color coding
        ('TEXTCOLOR', (3, 1), (3, -1), colors.HexColor('#dc2626')),
    ]))
    elements.append(inc_table)
    elements.append(Spacer(1, 10))

    # ── Footer note ─────────────────────────────────────────────────────────
    elements.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#e2e8f0')))
    elements.append(Paragraph(
        'This report is auto-generated by SIMS (MCSP-232 | MOD-07: Reporting Core). '
        'All data is sourced from the SIMS PostgreSQL database. '
        'Distribution restricted to authorized security personnel only.',
        ParagraphStyle('Footer', fontSize=7, textColor=colors.HexColor('#94a3b8'))
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer


class IncidentReportPDFView(APIView):
    """
    GET /api/v1/reports/incidents/pdf/
    Generates and streams a professional PDF incident report (Manager+ only).
    """
    permission_classes = [IsAuthenticated, IsManagerOrAbove]

    def get(self, request):
        # Apply filters from query params
        qs = Incident.objects.select_related('created_by', 'assigned_to')
        if request.query_params.get('status'):
            qs = qs.filter(status=request.query_params['status'])
        if request.query_params.get('severity'):
            qs = qs.filter(severity=request.query_params['severity'])
        if request.query_params.get('category'):
            qs = qs.filter(category=request.query_params['category'])

        incidents = list(qs.order_by('-created_at'))

        summary_stats = {
            'total': len(incidents),
            'critical': sum(1 for i in incidents if i.severity == Incident.SEVERITY_CRITICAL),
            'high': sum(1 for i in incidents if i.severity == Incident.SEVERITY_HIGH),
            'open': sum(1 for i in incidents if i.status == Incident.STATUS_OPEN),
            'resolved': sum(1 for i in incidents if i.status == Incident.STATUS_RESOLVED),
            'closed': sum(1 for i in incidents if i.status == Incident.STATUS_CLOSED),
            'predictions': MLPrediction.objects.count(),
        }

        pdf_buffer = generate_pdf_report(
            title='Security Incident Management Report',
            incidents=incidents,
            summary_stats=summary_stats
        )

        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        filename = f'SIMS_Incident_Report_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class IncidentReportCSVView(APIView):
    """
    GET /api/v1/reports/incidents/csv/
    Streams a CSV export of the incident register (Manager+ only).
    """
    permission_classes = [IsAuthenticated, IsManagerOrAbove]

    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        filename = f'SIMS_Incidents_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        writer.writerow([
            'Incident ID', 'Title', 'Description', 'Category', 'Severity',
            'Status', 'Created By', 'Assigned To', 'Created At', 'Updated At',
            'ML Predicted Category', 'ML Predicted Severity', 'ML Confidence Score'
        ])

        qs = Incident.objects.select_related(
            'created_by', 'assigned_to'
        ).prefetch_related('ml_predictions').order_by('-created_at')

        for inc in qs:
            pred = inc.ml_predictions.first()
            writer.writerow([
                inc.incident_id,
                inc.title,
                inc.description[:200],
                inc.category or '',
                inc.severity or '',
                inc.status,
                inc.created_by.full_name if inc.created_by else '',
                inc.assigned_to.full_name if inc.assigned_to else '',
                inc.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                inc.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                pred.predicted_category if pred else '',
                pred.predicted_severity if pred else '',
                str(pred.confidence_score) if pred else '',
            ])

        return response


class AuditReportCSVView(APIView):
    """
    GET /api/v1/reports/audit/csv/
    Exports audit log as CSV for compliance reporting (Admin only).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_system_admin():
            from rest_framework.response import Response
            from rest_framework import status
            return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)

        response = HttpResponse(content_type='text/csv')
        filename = f'SIMS_AuditLog_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        writer.writerow(['Log ID', 'User Email', 'User Role', 'Action', 'IP Address', 'Timestamp'])

        for log in AuditLog.objects.select_related('user', 'user__role').order_by('-timestamp'):
            writer.writerow([
                log.log_id,
                log.user.email if log.user else 'System',
                log.user.role_name if log.user else '',
                log.action,
                log.ip_address or '',
                log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            ])

        return response
