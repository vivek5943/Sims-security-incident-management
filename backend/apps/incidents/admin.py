from django.contrib import admin
from apps.incidents.models import Incident, InvestigationNote

@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ['incident_id', 'title', 'category', 'severity', 'status', 'created_by', 'created_at']
    list_filter = ['status', 'severity', 'category']
    search_fields = ['title', 'description']

@admin.register(InvestigationNote)
class InvestigationNoteAdmin(admin.ModelAdmin):
    list_display = ['note_id', 'incident', 'analyst', 'timestamp']
