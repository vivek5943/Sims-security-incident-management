"""
MOD-01: Authentication & Authorization Models
FIX-04: LoginAttempt model for account lockout tracking
FIX-15: Role + User models
"""
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from datetime import timedelta


class Role(models.Model):
    ANALYST = 'Security Analyst'
    MANAGER = 'Security Manager'
    ADMIN   = 'System Administrator'
    ROLE_CHOICES = [
        (ANALYST, 'Security Analyst'),
        (MANAGER, 'Security Manager'),
        (ADMIN,   'System Administrator'),
    ]
    role_id   = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = 'roles'

    def __str__(self): return self.role_name


# ── FIX-04: Account lockout tracking ─────────────────────────────────────────
class LoginAttempt(models.Model):
    """
    Tracks failed login attempts per email.
    After MAX_ATTEMPTS failures within LOCKOUT_WINDOW, account locks for LOCKOUT_DURATION.
    Throttling (FIX-06 from v2) limits rate; lockout (FIX-04) prevents brute-force after rate resets.
    """
    MAX_ATTEMPTS     = 5
    LOCKOUT_WINDOW   = timedelta(minutes=15)
    LOCKOUT_DURATION = timedelta(minutes=15)

    email        = models.EmailField(db_index=True)
    ip_address   = models.GenericIPAddressField(null=True, blank=True)
    attempted_at = models.DateTimeField(default=timezone.now)
    success      = models.BooleanField(default=False)

    class Meta:
        db_table = 'login_attempts'
        indexes  = [models.Index(fields=['email', 'attempted_at'])]

    @classmethod
    def is_locked(cls, email: str) -> bool:
        window_start = timezone.now() - cls.LOCKOUT_WINDOW
        failed = cls.objects.filter(
            email=email, success=False, attempted_at__gte=window_start
        ).count()
        return failed >= cls.MAX_ATTEMPTS

    @classmethod
    def record(cls, email: str, success: bool, ip: str = None):
        cls.objects.create(email=email, success=success, ip_address=ip)
        # Prune entries older than 1 day to prevent unbounded growth
        cls.objects.filter(attempted_at__lt=timezone.now() - timedelta(days=1)).delete()

    @classmethod
    def lockout_remaining(cls, email: str) -> int:
        """Returns seconds until lockout expires, or 0 if not locked."""
        window_start = timezone.now() - cls.LOCKOUT_WINDOW
        first_recent_fail = (
            cls.objects.filter(email=email, success=False, attempted_at__gte=window_start)
            .order_by('attempted_at').first()
        )
        if not first_recent_fail:
            return 0
        unlock_at = first_recent_fail.attempted_at + cls.LOCKOUT_DURATION
        remaining = (unlock_at - timezone.now()).total_seconds()
        return max(0, int(remaining))


class UserManager(BaseUserManager):
    def create_user(self, email, full_name, password=None, role=None, **extra):
        if not email: raise ValueError('Email required')
        email = self.normalize_email(email)
        user  = self.model(email=email, full_name=full_name, role=role, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        admin_role, _ = Role.objects.get_or_create(role_name=Role.ADMIN)
        return self.create_user(email, full_name, password, role=admin_role, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    STATUS_ACTIVE    = 'Active'
    STATUS_INACTIVE  = 'Inactive'
    STATUS_SUSPENDED = 'Suspended'
    STATUS_LOCKED    = 'Locked'       # FIX-04: lockout state
    STATUS_CHOICES   = [
        (STATUS_ACTIVE,    'Active'),
        (STATUS_INACTIVE,  'Inactive'),
        (STATUS_SUSPENDED, 'Suspended'),
        (STATUS_LOCKED,    'Locked'),
    ]

    user_id    = models.AutoField(primary_key=True)
    full_name  = models.CharField(max_length=100)
    email      = models.EmailField(max_length=150, unique=True)
    role       = models.ForeignKey(Role, on_delete=models.PROTECT, related_name='users',
                                   db_column='role_id', null=True, blank=True)
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    created_at = models.DateTimeField(default=timezone.now)
    is_staff   = models.BooleanField(default=False)
    is_active  = models.BooleanField(default=True)

    objects        = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        db_table = 'users'

    def __str__(self): return f"{self.full_name} ({self.email})"

    @property
    def role_name(self): return self.role.role_name if self.role else None
    def is_analyst(self):    return self.role_name == Role.ANALYST
    def is_manager(self):    return self.role_name == Role.MANAGER
    def is_system_admin(self): return self.role_name == Role.ADMIN
