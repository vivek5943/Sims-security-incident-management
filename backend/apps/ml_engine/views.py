"""
MOD-03: ML Classification Engine Views
FIX-15: Status endpoint clearly reports whether output is trained ML or heuristic
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.throttling import UserRateThrottle
from django.conf import settings
from pathlib import Path
import json, logging

from apps.ml_engine.pipeline import SIMSClassificationPipeline
from apps.ml_engine.models import MLPrediction
from apps.ml_engine.serializers import MLPredictionSerializer
from apps.authentication.permissions import IsManagerOrAbove

logger = logging.getLogger('apps.ml_engine')


class MLClassifyThrottle(UserRateThrottle):
    """FIX-06: Dedicated ML classify throttle — 60/min"""
    scope = 'ml_classify'


class ClassifyTextView(APIView):
    """
    POST /api/v1/ml/classify/
    FIX-15: Response includes is_trained_model flag so frontend can warn users
            when heuristic baseline is active (before train_ml_model is run)
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [MLClassifyThrottle]

    def post(self, request):
        description = request.data.get('description', '').strip()
        if not description or len(description) < 10:
            return Response(
                {'error': 'Description must be at least 10 characters.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            pipeline = SIMSClassificationPipeline()
            result = pipeline.predict(description)
            return Response({
                'success': True,
                'classification': result,
                'is_trained_model': result.get('is_trained_model', False),
                'warning': None if result.get('is_trained_model') else
                           'Using heuristic baseline. Run: python manage.py train_ml_model for real ML inference.',
            })
        except RuntimeError as e:
            # FIX-04: NLTK not downloaded
            return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            logger.error(f'[ML] classify error: {e}', exc_info=True)
            return Response({'error': 'Classification service error.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReclassifyIncidentView(APIView):
    """POST /api/v1/ml/reclassify/<incident_id>/"""
    permission_classes = [IsAuthenticated, IsManagerOrAbove]

    def post(self, request, incident_id):
        from apps.incidents.models import Incident
        from apps.incidents.views import trigger_ml_classification
        try:
            incident = Incident.objects.get(pk=incident_id)
        except Incident.DoesNotExist:
            return Response({'error': 'Incident not found'}, status=status.HTTP_404_NOT_FOUND)

        trigger_ml_classification(incident)
        return Response({
            'success': True,
            'message': f'ML classification queued for Incident #{incident_id}.',
            'note': 'Check ml_classification_status field for result.',
        })


class ModelStatusView(APIView):
    """
    GET /api/v1/ml/status/
    FIX-15: Clearly reports which models are loaded and whether outputs are ML or heuristic
    """
    permission_classes = [IsAuthenticated, IsManagerOrAbove]

    def get(self, request):
        model_path = Path(settings.ML_MODEL_PATH)
        category_file = model_path / 'sims_category_classifier.joblib'
        severity_file  = model_path / 'sims_severity_classifier.joblib'
        vectorizer_file = model_path / 'sims_tfidf_vectorizer.joblib'
        metadata_file  = model_path / 'model_metadata.json'

        models_trained = (
            category_file.exists() and
            severity_file.exists() and
            vectorizer_file.exists()
        )

        metadata = {}
        if metadata_file.exists():
            with open(metadata_file) as f:
                metadata = json.load(f)

        return Response({
            'models_trained': models_trained,
            'inference_mode': 'Scikit-Learn ML Classifiers' if models_trained else 'Heuristic Baseline (keyword rules)',
            'category_model_loaded': category_file.exists(),
            'severity_model_loaded': severity_file.exists(),
            'message': (
                'Both Category and Severity ML classifiers active. All predictions are ML-generated.'
                if models_trained else
                'Models not trained. Run: python manage.py train_ml_model'
                ' then python manage.py download_nltk_data first.'
            ),
            'metadata': metadata,
            'prediction_count': MLPrediction.objects.count(),
        })


class TrainModelView(APIView):
    """POST /api/v1/ml/train/ — Admin only"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_system_admin():
            return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
        try:
            from apps.ml_engine.trainer import train_and_save_model
            metadata = train_and_save_model()
            return Response({
                'success': True,
                'message': 'ML models (category + severity) trained and serialized.',
                'metadata': metadata,
            })
        except Exception as e:
            logger.error(f'[ML] Training error: {e}', exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
