"""MOD-07: Reporting Core URL Routes"""
from django.urls import path
from apps.reports.views import IncidentReportPDFView, IncidentReportCSVView, AuditReportCSVView
urlpatterns = [
    path('incidents/pdf/', IncidentReportPDFView.as_view(), name='report_incidents_pdf'),
    path('incidents/csv/', IncidentReportCSVView.as_view(), name='report_incidents_csv'),
    path('audit/csv/', AuditReportCSVView.as_view(), name='report_audit_csv'),
]
