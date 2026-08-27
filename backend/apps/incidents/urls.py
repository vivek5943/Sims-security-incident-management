"""MOD-02: Incident URL Routes — FIX-03 retry-ml + FIX-09 attachments"""
from django.urls import path
from apps.incidents.views import (
    IncidentListCreateView, IncidentDetailView, EscalateIncidentView,
    InvestigationNoteListCreateView, RetryMLClassificationView, IncidentAttachmentView
)
urlpatterns = [
    path('', IncidentListCreateView.as_view(), name='incident_list_create'),
    path('<int:pk>/', IncidentDetailView.as_view(), name='incident_detail'),
    path('<int:pk>/escalate/', EscalateIncidentView.as_view(), name='incident_escalate'),
    path('<int:pk>/retry-ml/', RetryMLClassificationView.as_view(), name='incident_retry_ml'),
    path('<int:pk>/attachments/', IncidentAttachmentView.as_view(), name='incident_attachments'),
    path('<int:incident_pk>/notes/', InvestigationNoteListCreateView.as_view(), name='incident_notes'),
]
