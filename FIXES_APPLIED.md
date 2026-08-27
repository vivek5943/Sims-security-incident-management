# SIMS v2 — Security & Quality Fixes Applied
**MCSP-232 | IGNOU MCA-2**

All 15 issues from code review are fixed. This document maps each fix to the changed files.

---

## Critical Fixes

### FIX-01: Unsafe default security settings
**Files:** `backend/sims_backend/settings.py`
- `SECRET_KEY` has **no default** — app crashes fast if not configured (intentional)
- `DEBUG` defaults to `False` — must be explicitly `True` in dev `.env`
- `ALLOWED_HOSTS` defaults to `localhost,127.0.0.1` — no wildcard `'*'`
- Production HSTS, SSL redirect, XSS filter headers activated when `DEBUG=False`

### FIX-02: JWT stored in localStorage (XSS-vulnerable)
**Files:** `backend/apps/authentication/cookie_auth.py` (new), `backend/apps/authentication/views.py`, `frontend/src/services/api.js`, `frontend/src/contexts/AuthContext.jsx`
- `CookieJWTAuthentication` class reads tokens from HttpOnly cookies
- Login sets `sims_access` + `sims_refresh` as `HttpOnly; Secure; SameSite=Strict` cookies
- Logout clears cookies server-side
- Frontend `axios` uses `withCredentials: true` — cookies sent automatically
- Only non-sensitive user profile (name, role) stored in `sessionStorage` for UI rendering
- Falls back to `Authorization: Bearer` header for API clients (Postman/mobile)

### FIX-03: ML failures silently ignored
**Files:** `backend/apps/incidents/models.py`, `backend/apps/incidents/views.py`
- `ml_classification_status` field added: `pending | classified | failed`
- `ml_classification_error` field stores the failure reason
- Dashboard can filter by `ml_status=failed` to find unclassified incidents
- New endpoint: `POST /api/v1/incidents/<id>/retry-ml/` to manually retry

### FIX-04: NLTK auto-download in production
**Files:** `backend/apps/ml_engine/pipeline.py`, `backend/apps/ml_engine/management/commands/download_nltk_data.py`
- `TextPreprocessor.__init__` calls `_verify_nltk_data()` — raises clear error if missing
- New management command: `python manage.py download_nltk_data` (run once during setup)
- `setup.sh` runs this before training
- Zero runtime internet calls after setup

### FIX-05: Incident categories mismatch with synopsis
**Files:** `backend/apps/incidents/models.py`, `backend/apps/ml_engine/trainer.py`
- Added 3 missing categories: **Data Breach**, **Unauthorized Access**, **Social Engineering**
- Full 8-category taxonomy: Phishing, Malware, Ransomware, DDoS, Insider Threat, Data Breach, Unauthorized Access, Social Engineering
- Training corpus has ~15 labelled samples per category
- Remediation playbooks added for all 8 categories

---

## Medium Severity Fixes

### FIX-06: No rate limiting on login
**Files:** `backend/sims_backend/settings.py`, `backend/apps/authentication/views.py`
- `LoginRateThrottle`: **10 requests/minute** per IP on `/auth/login/`
- `MLClassifyThrottle`: 60 requests/minute on `/ml/classify/`
- Global: `anon` 20/hour, `user` 500/hour via `DEFAULT_THROTTLE_RATES`
- Failed login attempts logged to audit trail

### FIX-07: Email failures hidden with `fail_silently=True`
**Files:** `backend/apps/incidents/views.py`, `backend/sims_backend/settings.py`
- `fail_silently=False` everywhere — exceptions are raised
- `try/except` around send — failure logged as `WARNING` with full details
- Ops can monitor `sims.log` for `[NOTIFY] Email send FAILED` entries
- In-platform DB notification always created regardless of email status

### FIX-08: Missing async ML processing (blocks API response)
**Files:** `backend/apps/incidents/views.py`
- `trigger_ml_classification()` now runs in a **background `threading.Thread`**
- API returns `201 Created` immediately — ML classifies asynchronously
- `ml_classification_status` field tracks the async job state
- Comment in code marks Celery migration path for production scaling

### FIX-09: No file upload validation
**Files:** `backend/apps/incidents/models.py` (`IncidentAttachment`), `backend/apps/incidents/views.py` (`IncidentAttachmentView`)
- Extension whitelist: `.pdf .png .jpg .jpeg .txt .csv .log .pcap`
- Size limit: **5 MB** max per file
- MIME type validation (double-checks beyond extension)
- `POST /api/v1/incidents/<id>/attachments/` endpoint with full validation

### FIX-10: Audit log explosion (unbounded table growth)
**Files:** `backend/apps/audit/models.py`, `backend/apps/audit/management/commands/archive_audit_logs.py`
- DB indexes on `timestamp`, `(user, timestamp)`, `action` for fast filtered queries
- `AuditLog.log()` classmethod — central write point, never raises
- New command: `python manage.py archive_audit_logs`
- Archives old entries to **gzip-compressed CSV** before batch-deleting
- `AUDIT_LOG_ARCHIVE_DAYS = 90` config in settings
- Cron recommendation: `0 2 * * 0 python manage.py archive_audit_logs`

---

## Database Design Fixes

### FIX-11 & FIX-12: Severity/Category stored twice (inconsistency)
**Files:** `backend/apps/incidents/models.py`, `backend/apps/incidents/views.py`
- **Source of truth defined clearly in code comment:**
  - `Incident.category` / `Incident.severity` = **operational values** (system-of-record)
  - `MLPrediction.predicted_category` / `predicted_severity` = raw ML output (kept for accuracy analysis)
- ML engine populates `Incident` fields on creation
- Managers can override `Incident` fields (escalation, correction) — that's by design
- `MLPrediction` retains original ML output for confidence auditing

---

## Frontend Fixes

### FIX-13: Infinite refresh loop risk
**Files:** `frontend/src/services/api.js`
- `NO_RETRY_ENDPOINTS` list: `/auth/login/`, `/auth/refresh/`, `/auth/logout/`
- Interceptor checks both `!original._retry` AND `!isNoRetryEndpoint` before retrying
- Refresh failure redirects to `/login` and clears session — no loop possible

### FIX-14: Hardcoded localhost URL
**Files:** `frontend/src/services/api.js`, `frontend/.env.example`, `frontend/.env.development`
- `const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'`
- Development default kept as safe fallback only
- `.env.example` documents production URL patterns
- Zero hardcoded production URLs in source code

---

## Project Evaluation Fix

### FIX-15: AI appears partially rule-based
**Files:** `backend/apps/ml_engine/trainer.py`, `backend/apps/ml_engine/pipeline.py`, `backend/apps/ml_engine/views.py`
- **Two dedicated ML classifiers trained:**
  1. `sims_category_classifier.joblib` — predicts threat category (8 classes)
  2. `sims_severity_classifier.joblib` — predicts severity level (4 classes)
- Both use identical NLP pipeline + TF-IDF feature extraction
- Both evaluated across all 3 classifiers (Naive Bayes, Logistic Regression, Random Forest)
- Best model per task selected by **cross-validated macro F1** (`StratifiedKFold n=5`)
- `is_trained_model: True/False` flag in every API response — clear distinction
- Heuristic fallback is **explicitly labelled** `"Heuristic Baseline (TRAIN MODEL: python manage.py train_ml_model)"`
- `/api/v1/ml/status/` reports `inference_mode`: `"Scikit-Learn ML Classifiers"` or `"Heuristic Baseline (keyword rules)"`

**Viva Answer:** *"The heuristic baseline is a pre-training fallback only. Once `train_ml_model` is run, both category and severity predictions come exclusively from Scikit-Learn classifiers (Multinomial Naive Bayes / Logistic Regression / Random Forest) selected by cross-validated macro F1 score. No keyword rules exist in the trained inference path — the `is_trained_model` flag in the API response confirms which mode is active."*

---

## Summary Table

| # | Issue | Severity | Fixed In |
|---|-------|----------|---------|
| 01 | Unsafe DEBUG/ALLOWED_HOSTS defaults | Critical | `settings.py` |
| 02 | JWT in localStorage (XSS risk) | Critical | `cookie_auth.py`, `api.js`, `AuthContext.jsx` |
| 03 | Silent ML failures | Critical | `incidents/models.py`, `incidents/views.py` |
| 04 | NLTK runtime download | Critical | `pipeline.py`, `download_nltk_data.py` |
| 05 | Missing categories | Critical | `incidents/models.py`, `trainer.py` |
| 06 | No login rate limiting | Medium | `settings.py`, `auth/views.py` |
| 07 | Silent email failures | Medium | `incidents/views.py`, `settings.py` |
| 08 | Blocking ML on request | Medium | `incidents/views.py` |
| 09 | No file upload validation | Medium | `incidents/models.py`, `incidents/views.py` |
| 10 | Unbounded audit log growth | Medium | `audit/models.py`, `archive_audit_logs.py` |
| 11 | Severity stored twice | DB Design | `incidents/models.py` (documented) |
| 12 | Category stored twice | DB Design | `incidents/models.py` (documented) |
| 13 | Infinite refresh loop risk | Frontend | `api.js` |
| 14 | Hardcoded localhost URL | Frontend | `api.js`, `.env.example` |
| 15 | Heuristic-not-ML severity | Evaluation | `trainer.py`, `pipeline.py`, `views.py` |
