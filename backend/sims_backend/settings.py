"""
SIMS Django Settings — v3 (All 15 second-pass fixes applied)
"""
from pathlib import Path
from datetime import timedelta
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY    = config('SECRET_KEY')
DEBUG         = config('DEBUG', default=False, cast=bool)
_HOSTS        = config('ALLOWED_HOSTS', default='localhost,127.0.0.1')
ALLOWED_HOSTS = [h.strip() for h in _HOSTS.split(',') if h.strip()]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'apps.authentication',
    'apps.incidents',
    'apps.ml_engine',
    'apps.analytics',
    'apps.notifications',
    'apps.audit',
    'apps.reports',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # FIX-08 (CSRF): CSRF middleware active — CookieJWTAuthentication + SameSite=Strict
    # provides defense-in-depth for cookie-based browser clients
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.audit.middleware.AuditLogMiddleware',
]

ROOT_URLCONF      = 'sims_backend.urls'
WSGI_APPLICATION  = 'sims_backend.wsgi.application'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]

# ── PostgreSQL ────────────────────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.postgresql',
        'NAME':     config('DB_NAME',     default='sims_db'),
        'USER':     config('DB_USER',     default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres'),
        'HOST':     config('DB_HOST',     default='localhost'),
        'PORT':     config('DB_PORT',     default='5432'),
        'OPTIONS':  {'connect_timeout': 10},
        'CONN_MAX_AGE': 60,
    }
}

AUTH_USER_MODEL = 'authentication.User'

# ── DRF + Throttling ──────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'apps.authentication.cookie_auth.CookieJWTAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
    'DEFAULT_PAGINATION_CLASS':   'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'sims_backend.utils.custom_exception_handler',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon':          '20/hour',
        'user':          '500/hour',
        'login':         '10/minute',    # FIX-06 v2
        'token_refresh': '30/minute',    # FIX-14
        'ml_classify':   '60/minute',    # FIX-06 v2
    },
}

# ── JWT ───────────────────────────────────────────────────────────────────────
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':  timedelta(hours=2),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS':  True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN':      True,
    'ALGORITHM':              'HS256',
    'SIGNING_KEY':            config('SECRET_KEY'),
    'AUTH_HEADER_TYPES':      ('Bearer',),
    'USER_ID_FIELD':          'user_id',
    'USER_ID_CLAIM':          'user_id',
}

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── CORS ──────────────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS', default='http://localhost:5173,http://localhost:3000'
).split(',')
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept','accept-encoding','authorization','content-type',
    'dnt','origin','user-agent','x-csrftoken','x-requested-with',
]

# FIX-08 (CSRF): API endpoints use JWT/cookie auth. CSRF_TRUSTED_ORIGINS must
# match CORS origins so Django CSRF middleware accepts preflight-validated requests.
CSRF_TRUSTED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS', default='http://localhost:5173,http://localhost:3000'
).split(',')
# JWT-only API endpoints are exempt from CSRF via @csrf_exempt decorator applied
# in cookie_auth.py for DRF views (DRF enforces session vs JWT separately).
CSRF_COOKIE_HTTPONLY = False   # Frontend needs to read CSRF token for form POSTs
CSRF_COOKIE_SAMESITE = 'Strict'

# ── Email / SMTP ──────────────────────────────────────────────────────────────
EMAIL_BACKEND      = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST         = config('EMAIL_HOST',    default='smtp.gmail.com')
EMAIL_PORT         = config('EMAIL_PORT',    default=587, cast=int)
EMAIL_USE_TLS      = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER    = config('EMAIL_HOST_USER',     default='')
EMAIL_HOST_PASSWORD= config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='SIMS <noreply@sims.com>')

# ── Logging ───────────────────────────────────────────────────────────────────
(BASE_DIR / 'logs').mkdir(exist_ok=True)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'sims': {'format': '[{asctime}] [{levelname}] [{name}] {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'sims'},
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'sims.log',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'sims',
        },
    },
    'loggers': {
        'sims':                {'handlers': ['console','file'], 'level': 'INFO',    'propagate': False},
        'apps.ml_engine':      {'handlers': ['console','file'], 'level': 'INFO',    'propagate': False},
        'apps.authentication': {'handlers': ['console','file'], 'level': 'WARNING', 'propagate': False},
        'apps.incidents':      {'handlers': ['console','file'], 'level': 'WARNING', 'propagate': False},
        'apps.notifications':  {'handlers': ['console','file'], 'level': 'WARNING', 'propagate': False},
        'django':              {'handlers': ['console'],        'level': 'WARNING'},
    },
}

# ── Static / Media ────────────────────────────────────────────────────────────
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL   = '/media/'
MEDIA_ROOT  = BASE_DIR / 'media'

# FIX-09: Upload constraints
FILE_UPLOAD_MAX_MEMORY_SIZE  = 5 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE  = 5 * 1024 * 1024

# ── ML Engine ─────────────────────────────────────────────────────────────────
ML_MODEL_PATH = BASE_DIR / 'ml_models'
ML_MODEL_PATH.mkdir(exist_ok=True)

# ── Audit archiving ───────────────────────────────────────────────────────────
AUDIT_LOG_ARCHIVE_DAYS = 90

# ── Production security headers ───────────────────────────────────────────────
if not DEBUG:
    SECURE_HSTS_SECONDS            = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD            = True
    SECURE_SSL_REDIRECT            = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
    SESSION_COOKIE_SECURE          = True
    CSRF_COOKIE_SECURE             = True
    SECURE_BROWSER_XSS_FILTER      = True
    SECURE_CONTENT_TYPE_NOSNIFF    = True
    X_FRAME_OPTIONS                = 'DENY'

LANGUAGE_CODE      = 'en-us'
TIME_ZONE          = 'UTC'
USE_I18N           = True
USE_TZ             = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
