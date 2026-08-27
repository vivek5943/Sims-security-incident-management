"""
SIMS Root URL Configuration
All API routes namespaced under /api/v1/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # MOD-01 Authentication & Authorization
    path('api/v1/auth/', include('apps.authentication.urls')),

    # MOD-02 Incident Management System
    path('api/v1/incidents/', include('apps.incidents.urls')),

    # MOD-03 ML Classification Engine
    path('api/v1/ml/', include('apps.ml_engine.urls')),

    # MOD-04 Dashboard & Analytics
    path('api/v1/analytics/', include('apps.analytics.urls')),

    # MOD-05 Notification Management
    path('api/v1/notifications/', include('apps.notifications.urls')),

    # MOD-06 Audit Logging Ledger
    path('api/v1/audit/', include('apps.audit.urls')),

    # MOD-07 Reporting Core
    path('api/v1/reports/', include('apps.reports.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = 'SIMS — Security Incident Management System'
admin.site.site_title = 'SIMS Admin'
admin.site.index_title = 'SIMS Administration Panel'
