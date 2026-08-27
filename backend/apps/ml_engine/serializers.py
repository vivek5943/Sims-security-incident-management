"""
MOD-03: ML Prediction Serializer
FIX-12: confidence_score labelled as 'model_confidence' not 'accuracy'
FIX-15: is_trained_model flag exposed
"""
from rest_framework import serializers
from apps.ml_engine.models import MLPrediction


class MLPredictionSerializer(serializers.ModelSerializer):
    # FIX-12: Explicit label — prevents UI from showing this as "probability of correctness"
    model_confidence = serializers.DecimalField(
        source='confidence_score', max_digits=5, decimal_places=2, read_only=True
    )
    calibration_note = serializers.SerializerMethodField()

    class Meta:
        model  = MLPrediction
        fields = [
            'prediction_id', 'incident',
            'predicted_category', 'predicted_severity',
            'model_confidence',        # FIX-12: renamed from confidence_score
            'confidence_score',        # kept for backward compat
            'action_recommendations',
            'model_name', 'is_trained_model',
            'analyst_override_note',
            'calibration_note',        # FIX-12
            'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_calibration_note(self, obj):
        # FIX-12: Always surface calibration caveat — UI must display this near confidence
        return MLPrediction.CALIBRATION_NOTE
