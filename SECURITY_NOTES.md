# SIMS Security Notes
## MCSP-232 | IGNOU MCA-2

### ClamAV Antivirus Integration (Future — Fix #09)

Current mitigations for uploaded files:
- Extension whitelist (.pdf, .png, .jpg, .jpeg, .txt, .csv, .log, .pcap)
- 5MB file size limit
- Magic bytes validation (file header inspection)
- Double-extension attack prevention (invoice.pdf.exe rejected)
- Files served with Content-Disposition: attachment

Future ClamAV integration path:
```bash
# Install ClamAV
sudo apt-get install clamav clamav-daemon
sudo freshclam

# Python dependency
pip install python-clamd
```

```python
# In IncidentAttachmentView.post():
import clamd
cd = clamd.ClamdUnixSocket('/var/run/clamav/clamd.ctl')
result = cd.instream(uploaded_file)
if result['stream'][0] == 'FOUND':
    return Response(
        {'error': f'Security scan failed: {result["stream"][1]}. File rejected.'},
        status=400
    )
```

### Production Deployment Checklist

- [ ] SECRET_KEY: 50+ random characters, never committed to git
- [ ] DEBUG=False in production
- [ ] ALLOWED_HOSTS: explicit domain list, no wildcards
- [ ] HTTPS enforced (SECURE_SSL_REDIRECT=True)
- [ ] HSTS enabled (SECURE_HSTS_SECONDS=31536000)
- [ ] All default demo passwords changed
- [ ] PostgreSQL password changed from 'postgres'
- [ ] Email SMTP configured for notification alerts
- [ ] NLTK data pre-downloaded (manage.py download_nltk_data)
- [ ] ML models trained (manage.py train_ml_model)
- [ ] Audit log archiving scheduled (cron: manage.py archive_audit_logs)
- [ ] Gunicorn/uWSGI configured (not Django dev server)
- [ ] Nginx reverse proxy with rate limiting
- [ ] SSL certificate installed
- [ ] Firewall: only ports 80, 443 exposed
- [ ] Regular database backups configured

### Celery Migration Path (Fix #02)

When moving to production with multiple workers:

```bash
pip install celery redis django-celery-results
```

```python
# celery.py
from celery import Celery
app = Celery('sims')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# settings.py additions:
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'django-db'
```

```python
# Replace threading.Thread with:
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def classify_incident_task(self, incident_id):
    try:
        incident = Incident.objects.get(pk=incident_id)
        # ... classification logic
    except Exception as exc:
        raise self.retry(exc=exc)

# In views.py:
classify_incident_task.delay(incident.pk)  # non-blocking
```
