"""MOD-03: ML Engine URL Routes"""
from django.urls import path
from apps.ml_engine.views import (
    ClassifyTextView, ReclassifyIncidentView,
    ModelStatusView, TrainModelView
)
urlpatterns = [
    path('classify/',                ClassifyTextView.as_view(),       name='ml_classify'),
    path('reclassify/<int:incident_id>/', ReclassifyIncidentView.as_view(), name='ml_reclassify'),
    path('status/',                  ModelStatusView.as_view(),        name='ml_status'),
    path('train/',                   TrainModelView.as_view(),         name='ml_train'),
]
