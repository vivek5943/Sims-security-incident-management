from django.contrib import admin
from apps.ml_engine.models import MLPrediction

@admin.register(MLPrediction)
class MLPredictionAdmin(admin.ModelAdmin):
    list_display = ['prediction_id', 'incident', 'predicted_category', 'predicted_severity', 'confidence_score', 'created_at']
    list_filter = ['predicted_category', 'predicted_severity']
