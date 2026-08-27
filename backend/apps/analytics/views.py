"""
MOD-04: Dashboard & Analytics
Views — Aggregated metrics for Pie, Bar, and Line chart components.
Section 8.2 (MOD-04): counts, distributions, trends via chart components.
All endpoints require Manager-level access minimum.
"""
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta

from apps.incidents.models import Incident
from apps.authentication.models import User, Role
from apps.ml_engine.models import MLPrediction
from apps.audit.models import AuditLog
from apps.authentication.permissions import IsManagerOrAbove


class DashboardSummaryView(APIView):
    """
    GET /api/v1/analytics/dashboard/
    Top-level KPI cards for the SOC operations dashboard.
    Accessible to: Analysts (own data), Managers+, Admins (full org view).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role_name == Role.ANALYST:
            base_qs = Incident.objects.filter(
                Q(created_by=user) | Q(assigned_to=user)
            )
        else:
            base_qs = Incident.objects.all()

        now = timezone.now()
        last_30 = now - timedelta(days=30)
        last_7 = now - timedelta(days=7)

        # Status distribution
        status_counts = {
            item['status']: item['count']
            for item in base_qs.values('status').annotate(count=Count('incident_id'))
        }

        # Severity distribution
        severity_counts = {
            item['severity']: item['count']
            for item in base_qs.exclude(severity=None)
                              .values('severity')
                              .annotate(count=Count('incident_id'))
        }

        # Category distribution
        category_counts = {
            item['category']: item['count']
            for item in base_qs.exclude(category=None)
                              .values('category')
                              .annotate(count=Count('incident_id'))
        }

        total = base_qs.count()
        open_count = base_qs.filter(status=Incident.STATUS_OPEN).count()
        critical = base_qs.filter(severity=Incident.SEVERITY_CRITICAL).count()
        new_30 = base_qs.filter(created_at__gte=last_30).count()
        new_7 = base_qs.filter(created_at__gte=last_7).count()
        resolved = base_qs.filter(status=Incident.STATUS_RESOLVED).count()
        closed = base_qs.filter(status=Incident.STATUS_CLOSED).count()

        # Average confidence of ML predictions
        avg_confidence = None
        if user.role_name != Role.ANALYST:
            from django.db.models import Avg
            result = MLPrediction.objects.aggregate(avg=Avg('confidence_score'))
            avg_confidence = round(float(result['avg'] or 0), 2)

        return Response({
            'summary': {
                'total_incidents': total,
                'open': open_count,
                'critical': critical,
                'new_last_30_days': new_30,
                'new_last_7_days': new_7,
                'resolved': resolved,
                'closed': closed,
                'ml_avg_confidence': avg_confidence,
            },
            'status_distribution': status_counts,
            'severity_distribution': severity_counts,
            'category_distribution': category_counts,
        })


class IncidentTrendView(APIView):
    """
    GET /api/v1/analytics/trend/?days=30
    Daily incident creation trend — powers Line chart (Section MOD-04).
    """
    permission_classes = [IsAuthenticated, IsManagerOrAbove]

    def get(self, request):
        days = int(request.query_params.get('days', 30))
        since = timezone.now() - timedelta(days=days)

        daily_trend = (
            Incident.objects.filter(created_at__gte=since)
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(count=Count('incident_id'))
            .order_by('date')
        )

        return Response({
            'period_days': days,
            'trend': [
                {'date': str(item['date']), 'count': item['count']}
                for item in daily_trend
            ],
        })


class CategoryBreakdownView(APIView):
    """
    GET /api/v1/analytics/categories/
    Category breakdown with severity cross-tabulation — Pie + Bar chart data.
    """
    permission_classes = [IsAuthenticated, IsManagerOrAbove]

    def get(self, request):
        # Category totals
        category_totals = list(
            Incident.objects.exclude(category=None)
            .values('category')
            .annotate(total=Count('incident_id'))
            .order_by('-total')
        )

        # Category × Severity matrix
        matrix = list(
            Incident.objects.exclude(category=None).exclude(severity=None)
            .values('category', 'severity')
            .annotate(count=Count('incident_id'))
        )

        return Response({
            'category_totals': category_totals,
            'category_severity_matrix': matrix,
        })


class AnalystPerformanceView(APIView):
    """
    GET /api/v1/analytics/performance/
    Per-analyst incident resolution metrics — Manager+ only.
    """
    permission_classes = [IsAuthenticated, IsManagerOrAbove]

    def get(self, request):
        analysts = User.objects.filter(role__role_name=Role.ANALYST).prefetch_related(
            'assigned_incidents'
        )

        performance = []
        for analyst in analysts:
            assigned = analyst.assigned_incidents.count()
            resolved = analyst.assigned_incidents.filter(
                status__in=[Incident.STATUS_RESOLVED, Incident.STATUS_CLOSED]
            ).count()
            performance.append({
                'analyst_id': analyst.user_id,
                'full_name': analyst.full_name,
                'email': analyst.email,
                'assigned': assigned,
                'resolved': resolved,
                'resolution_rate': round((resolved / assigned * 100), 1) if assigned > 0 else 0,
            })

        return Response({'analyst_performance': performance})


class MLAccuracyStatsView(APIView):
    """
    GET /api/v1/analytics/ml-stats/
    ML prediction confidence distribution and category breakdown — Manager+.
    """
    permission_classes = [IsAuthenticated, IsManagerOrAbove]

    def get(self, request):
        from django.db.models import Avg, Min, Max, Count

        stats = MLPrediction.objects.aggregate(
            avg_confidence=Avg('confidence_score'),
            min_confidence=Min('confidence_score'),
            max_confidence=Max('confidence_score'),
            total_predictions=Count('prediction_id'),
        )

        by_category = list(
            MLPrediction.objects.values('predicted_category')
            .annotate(
                count=Count('prediction_id'),
                avg_confidence=Avg('confidence_score')
            )
            .order_by('-count')
        )

        return Response({
            'aggregate_stats': stats,
            'by_category': by_category,
        })
