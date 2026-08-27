"""MOD-04: Analytics URL Routes"""
from django.urls import path
from apps.analytics.views import (
    DashboardSummaryView, IncidentTrendView,
    CategoryBreakdownView, AnalystPerformanceView, MLAccuracyStatsView
)
urlpatterns = [
    path('dashboard/', DashboardSummaryView.as_view(), name='dashboard_summary'),
    path('trend/', IncidentTrendView.as_view(), name='incident_trend'),
    path('categories/', CategoryBreakdownView.as_view(), name='category_breakdown'),
    path('performance/', AnalystPerformanceView.as_view(), name='analyst_performance'),
    path('ml-stats/', MLAccuracyStatsView.as_view(), name='ml_stats'),
]
