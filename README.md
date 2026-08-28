# SIMS — AI-Powered Security Incident Management System
### MCSP-232 Project | IGNOU MCA-2

> **Domain:** Cybersecurity + Artificial Intelligence + Web Application  
> **Architecture:** Multi-tier (React SPA ↔ Django REST API ↔ PostgreSQL ↔ Scikit-Learn ML Engine)

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend (Presentation) | React.js 18 + Vite + Tailwind CSS + Recharts |
| Backend (Application) | Python 3.10 + Django 4.2 + Django REST Framework 3.14 |
| Database (Persistence) | PostgreSQL 14+ |
| Authentication | JWT (SimpleJWT) + PBKDF2-SHA256 password hashing |
| ML Engine | Scikit-Learn + NLTK + Pandas + NumPy |
| Report Generation | ReportLab (PDF) + Python CSV |

---

## Module Map (MCSP-232 Section 8.2)

| Module | Code | Description |
|--------|------|-------------|
| Authentication & Authorization | MOD-01 | JWT, RBAC, Registration, Password |
| Incident Management System | MOD-02 | Full CRUD, 6-state lifecycle |
| ML Classification Engine | MOD-03 | NLP → TF-IDF → 3 Classifiers → Best Model |
| Dashboard & Analytics | MOD-04 | Pie / Bar / Line charts via Recharts |
| Notification Management | MOD-05 | In-platform + SMTP email alerts |
| Audit Logging Ledger | MOD-06 | Immutable audit trail |
| Reporting Core | MOD-07 | PDF (ReportLab) + CSV exports |

---

## Project Structure

```
sims/
├── backend/                        # Django REST API
│   ├── sims_backend/               # Core Django config (settings, urls)
│   ├── apps/
│   │   ├── authentication/         # MOD-01: User model, JWT, RBAC
│   │   ├── incidents/              # MOD-02: Incident + Notes models
│   │   ├── ml_engine/              # MOD-03: Pipeline, Trainer, Predictor
│   │   ├── analytics/              # MOD-04: Dashboard aggregations
│   │   ├── notifications/          # MOD-05: Notification model + views
│   │   ├── audit/                  # MOD-06: AuditLog + middleware
│   │   └── reports/                # MOD-07: PDF + CSV generators
│   ├── ml_models/                  # Serialized .joblib model files
│   ├── requirements.txt
│   └── manage.py
│
└── frontend/                       # React SPA
    ├── src/
    │   ├── contexts/AuthContext.jsx # JWT state + RBAC helpers
    │   ├── services/api.js          # All API calls (MOD-01 to MOD-07)
    │   ├── components/
    │   │   ├── Layout/Sidebar.jsx   # Navigation + Layout shell
    │   │   └── Common/index.jsx     # Badges, cards, spinner, etc.
    │   ├── pages/
    │   │   ├── Login.jsx            # JWT login form
    │   │   ├── Dashboard.jsx        # MOD-04 KPI + charts
    │   │   ├── Incidents/           # MOD-02 list + create + detail
    │   │   └── OtherPages.jsx       # ML, Analytics, Reports, Audit, Users
    │   ├── utils/helpers.js         # Badge colors, formatters
    │   └── App.jsx                  # Router + RBAC guards
    ├── package.json
    └── vite.config.js
```

---

## Setup & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+ LTS
- PostgreSQL 14+
- Git

---

### Step 1 — Database Setup

```sql
-- Connect to PostgreSQL as superuser
CREATE DATABASE sims_db;
CREATE USER sims_user WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE sims_db TO sims_user;
```

---

### Step 2 — Backend Setup

```bash
# 1. Navigate to backend
cd sims/backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate          # Linux/macOS
# OR: venv\Scripts\activate       # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. NLTK data (required for NLP preprocessing)
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('omw-1.4')"

# 5. Configure environment
cp .env.example .env
# Edit .env — set DB_NAME, DB_USER, DB_PASSWORD

# 6. Run database migrations
python manage.py makemigrations authentication incidents ml_engine notifications audit
python manage.py migrate

# 7. Seed initial roles and demo users
python manage.py seed_data

# 8. Train ML Classification Engine (Section 13)
python manage.py train_ml_model

# 9. Start development server
python manage.py runserver 0.0.0.0:8000
```

Backend running at: **http://localhost:8000**  
Django Admin: **http://localhost:8000/admin/**

---

### Step 3 — Frontend Setup

```bash
# 1. Navigate to frontend
cd sims/frontend

# 2. Install Node dependencies
npm install

# 3. Start Vite dev server
npm run dev
```

Frontend running at: **http://localhost:5173**

---

### Demo Login Credentials (seeded by seed_data) -Not used in production

| Email | Password | Role |
|-------|----------|------|
| admin@sims.local | Admin@1234 | System Administrator |
| manager@sims.local | Manager@1234 | Security Manager |
| analyst1@sims.local | Analyst@1234 | Security Analyst |
| analyst2@sims.local | Analyst@1234 | Security Analyst |

---

## API Reference

### Authentication (MOD-01)
```
POST   /api/v1/auth/login/           JWT login
POST   /api/v1/auth/refresh/         Refresh access token
POST   /api/v1/auth/logout/          Blacklist refresh token
POST   /api/v1/auth/register/        Admin: create user
GET    /api/v1/auth/profile/         Current user profile
GET    /api/v1/auth/users/           List all users (Manager+)
GET    /api/v1/auth/analysts/        Analyst list for assignment
```

### Incidents (MOD-02)
```
GET    /api/v1/incidents/            List incidents (filtered)
POST   /api/v1/incidents/            Create + auto ML classify
GET    /api/v1/incidents/<id>/       Full incident + notes + ML
PATCH  /api/v1/incidents/<id>/       Update status/assignment
DELETE /api/v1/incidents/<id>/       Admin delete
POST   /api/v1/incidents/<id>/escalate/     Escalate severity
GET    /api/v1/incidents/<id>/notes/ Investigation notes
POST   /api/v1/incidents/<id>/notes/ Add note
```

### ML Engine (MOD-03)
```
POST   /api/v1/ml/classify/          Classify text description
POST   /api/v1/ml/reclassify/<id>/   Force reclassify incident
GET    /api/v1/ml/status/            Model metadata
POST   /api/v1/ml/train/             Train model (Admin)
```

### Analytics (MOD-04)
```
GET    /api/v1/analytics/dashboard/  KPI summary
GET    /api/v1/analytics/trend/      Daily trend (30d)
GET    /api/v1/analytics/categories/ Category breakdown
GET    /api/v1/analytics/performance/ Analyst resolution rates
```

### Reports (MOD-07)
```
GET    /api/v1/reports/incidents/pdf/  Download PDF report
GET    /api/v1/reports/incidents/csv/  Download CSV export
GET    /api/v1/reports/audit/csv/      Download audit log CSV
```

---

## ML Pipeline (Section 13)

```
Raw Text
  → [1] Regex Cleaning (HTML, numbers, punctuation stripped)
  → [2] Tokenization (split to token arrays)
  → [3] Stopword Removal (filter domain-irrelevant terms)
  → [4] Lemmatization (attacks → attack)
  → [5] TF-IDF Vectorization (text → numerical feature matrices)
         TF-IDF(t,d,D) = TF(t,d) × IDF(t,D)
  → [6] Model Inference (3 classifiers evaluated by macro F1)
         ◆ Multinomial Naive Bayes  — ultra-fast baseline
         ◆ Logistic Regression      — reliable TF-IDF boundary
         ◆ Random Forest            — ensemble, overfitting-resistant
  → [7] Best model serialized via joblib
  → Output: category + severity + confidence + remediation playbook
```

**Validation Metrics (Section 13.4):**
- Accuracy = (TP + TN) / (TP + TN + FP + FN)
- Precision = TP / (TP + FP)
- Recall = TP / (TP + FN)
- F1 Score = 2 × (Precision × Recall) / (Precision + Recall)

---

## RBAC Role Matrix (Section 8.1)

| Capability | Analyst | Manager | Admin |
|-----------|---------|---------|-------|
| Create incident | ✅ | ✅ | ✅ |
| View own incidents | ✅ | ✅ | ✅ |
| View all incidents | ❌ | ✅ | ✅ |
| Assign incidents | ❌ | ✅ | ✅ |
| Escalate severity | ❌ | ✅ | ✅ |
| Analytics dashboard | ❌ | ✅ | ✅ |
| Download reports | ❌ | ✅ | ✅ |
| Audit log viewer | ❌ | ✅ | ✅ |
| User management | ❌ | ❌ | ✅ |
| Train ML model | ❌ | ❌ | ✅ |

---

## Security Architecture (Section 14)

- **Password Hashing:** PBKDF2 with SHA-256 — plaintext never stored
- **JWT Authentication:** Stateless access + refresh token pair
- **Token Blacklisting:** Refresh tokens invalidated on logout
- **RBAC Middleware:** Django middleware intercepts all API requests
- **SQL Injection Protection:** Django ORM parameterized queries
- **XSS Prevention:** React automatic output encoding
- **CSRF Protection:** Stateless JWT (no cookies) eliminates CSRF surface
- **Audit Trail:** Immutable PostgreSQL ledger — all mutations logged

---

## Project Timeline (Section 17)

```
Week 01–02  Requirements Analysis & Architecture Design
Week 03–04  Authentication Matrix & PostgreSQL Schema Build
Week 05–07  Core Incident CRUD API Development
Week 08–10  ML Engine Pipeline (NLP → TF-IDF → Classifiers)
Week 11–12  React UI, Tailwind Styling, Recharts Dashboards
Week 13–14  Integration Testing, RBAC Verification, Bug Fixes
Week 15–16  Documentation & Deployment Preparation
```

---

## References (Section 21)

1. NIST SP 800-61 Rev. 2 — Computer Security Incident Handling Guide
2. Pedregosa et al. — Scikit-learn: Machine Learning in Python (JMLR 2011)
3. McKinney — Data Structures for Statistical Computing in Python (2010)
4. Chou — Machine Learning Techniques for Cybersecurity (IJACSA 2018)
5. Spasić & Janković — Using Django Framework for Data-Driven Web Apps (2021)
6. Banks & Porcello — Learning React, 2nd ed. (O'Reilly 2020)

---

*IGNOU MCSP-232 | MCA-2 | Submitted under guidance as per IGNOU project guidelines*
