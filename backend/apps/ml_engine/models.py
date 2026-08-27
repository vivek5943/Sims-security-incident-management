"""
MOD-03: ML Prediction Model
FIX-15: incident is OneToOneField — enforces DB-level uniqueness.
        No duplicate predictions possible even under concurrent thread execution.
FIX-12: Added calibration_note field — surfaces model confidence caveat in API.
FIX-11: Added analyst_override_note — documents when human overrides ML output.
"""
from django.db import models


class MLPrediction(models.Model):
    prediction_id = models.AutoField(primary_key=True)

    # FIX-15: OneToOneField — enforces single prediction per incident at DB level
    incident = models.OneToOneField(
        'incidents.Incident',
        on_delete=models.CASCADE,
        related_name='ml_predictions',    # kept plural for backward compat with serializers
        db_column='incident_id',
        unique=True                        # redundant with OneToOne but makes intent explicit
    )

    predicted_category    = models.CharField(max_length=50)
    predicted_severity    = models.CharField(max_length=20)
    confidence_score      = models.DecimalField(max_digits=5, decimal_places=2)
    action_recommendations = models.TextField(blank=True, default='')
    model_name            = models.CharField(max_length=100, default='')
    is_trained_model      = models.BooleanField(default=False)   # FIX-15: heuristic vs ML flag

    # FIX-12: Calibration caveat — surfaced in API so UI can display correct label
    # sklearn predict_proba is NOT calibrated by default. Score = model confidence,
    # not probability of correctness. UI should display "Model Confidence" not "Accuracy".
    CALIBRATION_NOTE = (
        'Confidence score reflects model posterior probability, not calibrated accuracy. '
        'Treat as relative ranking, not absolute correctness probability. '
        'Human analyst review is required for all Critical/High severity incidents.'
    )

    # FIX-11: When manager overrides ML category/severity, reason is stored here
    analyst_override_note = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table         = 'ml_predictions'
        verbose_name     = 'ML Prediction'
        verbose_name_plural = 'ML Predictions'
        ordering         = ['-created_at']

    def __str__(self):
        mode = 'ML' if self.is_trained_model else 'Heuristic'
        return (f"Prediction #{self.prediction_id} [{mode}] — Incident #{self.incident_id}: "
                f"{self.predicted_category} / {self.predicted_severity} @ {self.confidence_score}%")
