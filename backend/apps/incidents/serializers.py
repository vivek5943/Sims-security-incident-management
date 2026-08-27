"""MOD-02: Incident Serializers — updated for new model fields"""
from rest_framework import serializers
from apps.incidents.models import Incident, InvestigationNote, IncidentAttachment
from apps.authentication.serializers import UserProfileSerializer


class InvestigationNoteSerializer(serializers.ModelSerializer):
    analyst = UserProfileSerializer(read_only=True)

    class Meta:
        model = InvestigationNote
        fields = ['note_id', 'incident', 'analyst', 'notes', 'timestamp']
        read_only_fields = ['note_id', 'analyst', 'timestamp']

    def create(self, validated_data):
        validated_data['analyst'] = self.context['request'].user
        return super().create(validated_data)


class IncidentAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by = UserProfileSerializer(read_only=True)

    class Meta:
        model = IncidentAttachment
        fields = ['attachment_id', 'original_filename', 'file_size_bytes', 'mime_type',
                  'uploaded_by', 'uploaded_at']
        read_only_fields = fields


class IncidentSerializer(serializers.ModelSerializer):
    created_by = UserProfileSerializer(read_only=True)
    assigned_to = UserProfileSerializer(read_only=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=__import__('apps.authentication.models', fromlist=['User']).User.objects.all(),
        source='assigned_to', write_only=True, required=False, allow_null=True
    )
    notes = InvestigationNoteSerializer(many=True, read_only=True)
    attachments = IncidentAttachmentSerializer(many=True, read_only=True)
    ml_prediction = serializers.SerializerMethodField()
    note_count = serializers.SerializerMethodField()

    class Meta:
        model = Incident
        fields = [
            'incident_id', 'title', 'description', 'indicators_of_compromise', 'category', 'severity',
            'status', 'ml_classification_status', 'ml_classification_error',
            'created_by', 'assigned_to', 'assigned_to_id',
            'created_at', 'updated_at', 'notes', 'attachments', 'ml_prediction', 'note_count'
        ]
        read_only_fields = [
            'incident_id', 'created_by', 'created_at', 'updated_at',
            'category', 'severity', 'ml_classification_status', 'ml_classification_error'
        ]

    def get_ml_prediction(self, obj):
        pred = getattr(obj, 'ml_predictions', None)
        if pred:
            from apps.ml_engine.serializers import MLPredictionSerializer
            return MLPredictionSerializer(pred).data
        return None

    def get_note_count(self, obj):
        return obj.notes.count()

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class IncidentListSerializer(serializers.ModelSerializer):
    created_by = UserProfileSerializer(read_only=True)
    assigned_to = UserProfileSerializer(read_only=True)
    note_count = serializers.SerializerMethodField()
    has_prediction = serializers.SerializerMethodField()

    class Meta:
        model = Incident
        fields = [
            'incident_id', 'title', 'category', 'severity', 'status',
            'ml_classification_status', 'created_by', 'assigned_to',
            'created_at', 'updated_at', 'note_count', 'has_prediction'
        ]

    def get_note_count(self, obj): return obj.notes.count()
    def get_has_prediction(self, obj):return hasattr(obj, 'ml_predictions') and obj.ml_predictions is not None
