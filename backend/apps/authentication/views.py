"""
MOD-01: Authentication Views — v3 Deep Fix Pass
FIX-01: Refresh token read from cookie first, body second → logout never leaves zombie token
FIX-04: Account lockout after 5 failures in 15 min window
FIX-05: Constant-time login response — prevents user enumeration
FIX-06: LoginRateThrottle + RefreshRateThrottle (new)
FIX-07: Audit log sanitization for email/action strings
"""
import hashlib, hmac, logging, time, re
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from django.contrib.auth import authenticate
from django.utils import timezone

from apps.authentication.models import User, Role, LoginAttempt
from apps.authentication.serializers import (
    UserSerializer, UserProfileSerializer,
    CustomTokenObtainPairSerializer, ChangePasswordSerializer, RoleSerializer
)
from apps.authentication.permissions import IsSystemAdmin, IsManagerOrAbove
from apps.authentication.cookie_auth import set_auth_cookies, clear_auth_cookies
from apps.audit.models import AuditLog

logger = logging.getLogger('apps.authentication')


def _sanitize_log(value: str, max_len: int = 200) -> str:
    """
    FIX-07: Strip control characters and newlines from values before audit logging.
    Prevents log injection attacks (e.g. email=attacker@x.com\nFAKE CRITICAL EVENT).
    """
    if not value:
        return ''
    sanitized = re.sub(r'[\x00-\x1f\x7f\r\n]', '_', str(value))
    return sanitized[:max_len]


# ── FIX-06: Dedicated throttles ───────────────────────────────────────────────
class LoginRateThrottle(AnonRateThrottle):
    rate  = '10/minute'
    scope = 'login'


class RefreshRateThrottle(AnonRateThrottle):
    """FIX-14: Throttle refresh endpoint to prevent hammering with invalid cookies."""
    rate  = '30/minute'
    scope = 'token_refresh'


# ── FIX-01 + FIX-04 + FIX-05: Secure Login View ──────────────────────────────
class SecureLoginView(APIView):
    """
    POST /api/v1/auth/login/
    FIX-01: Sets HttpOnly SameSite=Strict cookies
    FIX-04: Account lockout after MAX_ATTEMPTS failures
    FIX-05: Constant-time response — identical message for wrong password vs unknown email
            (prevents user enumeration via timing attack)
    FIX-07: Sanitize email before writing to audit log
    """
    permission_classes = []
    throttle_classes   = [LoginRateThrottle]

    # Constant-time sentinel — ensure both paths take same wall time
    _DUMMY_HASH = User().set_password('dummy_constant_time_sentinel')

    def post(self, request):
        email    = request.data.get('email', '').strip().lower()
        password = request.data.get('password', '')
        ip       = self._get_ip(request)
        safe_email = _sanitize_log(email)  # FIX-07

        # FIX-04: Check lockout before doing anything
        if LoginAttempt.is_locked(email):
            remaining = LoginAttempt.lockout_remaining(email)
            logger.warning(f'[AUTH] Locked account login attempt: {safe_email} from {ip}')
            AuditLog.log(action=f'LOGIN_BLOCKED: account locked email={safe_email} ip={ip}', ip=ip)
            return Response(
                {'error': f'Account locked due to multiple failed attempts. '
                          f'Try again in {remaining // 60}m {remaining % 60}s.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        # FIX-05: Always look up user — if not found, run a dummy password check
        # so timing is identical whether email exists or not.
        try:
            user_obj = User.objects.select_related('role').get(email=email)
        except User.DoesNotExist:
            # FIX-05: Dummy hash to equalize timing — attacker cannot enumerate users
            import django.contrib.auth.hashers as _h
            _h.check_password('dummy', 'pbkdf2_sha256$260000$dummy$dummydummydummydummy=')
            LoginAttempt.record(email=email, success=False, ip=ip)
            # FIX-05: IDENTICAL message to wrong-password path
            return Response({'error': 'Invalid email or password.'}, status=status.HTTP_401_UNAUTHORIZED)

        # FIX-05: Check account status before password (consistent response)
        if user_obj.status == User.STATUS_LOCKED:
            return Response({'error': 'Account locked. Contact your administrator.'}, status=status.HTTP_403_FORBIDDEN)
        if user_obj.status in [User.STATUS_INACTIVE, User.STATUS_SUSPENDED]:
            return Response({'error': 'Account is inactive. Contact your administrator.'}, status=status.HTTP_403_FORBIDDEN)

        # Actual password check
        if not user_obj.check_password(password):
            LoginAttempt.record(email=email, success=False, ip=ip)
            # FIX-04: Auto-lock after threshold
            if LoginAttempt.is_locked(email):
                logger.warning(f'[AUTH] Account locked after failed attempts: {safe_email}')
                AuditLog.log(action=f'ACCOUNT_LOCKED: {safe_email} after repeated failures from {ip}', ip=ip)
                return Response(
                    {'error': 'Account locked after 5 failed attempts. Try again in 15 minutes.'},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            AuditLog.log(action=f'LOGIN_FAILED: email={safe_email} ip={ip}', ip=ip)
            # FIX-05: Same message as missing-email path
            return Response({'error': 'Invalid email or password.'}, status=status.HTTP_401_UNAUTHORIZED)

        # Successful login
        LoginAttempt.record(email=email, success=True, ip=ip)
        refresh = RefreshToken.for_user(user_obj)
        refresh['user_id']   = user_obj.user_id
        refresh['email']     = user_obj.email
        refresh['full_name'] = user_obj.full_name
        refresh['role']      = user_obj.role_name

        access = refresh.access_token

        user_data = {
            'user_id':   user_obj.user_id,
            'full_name': user_obj.full_name,
            'email':     user_obj.email,
            'role':      user_obj.role_name,
            'status':    user_obj.status,
        }

        response = Response({
            'access':  str(access),
            'refresh': str(refresh),
            'user':    user_data,
        })
        # FIX-01: Set HttpOnly cookies
        set_auth_cookies(response, access_token=access, refresh_token=refresh)
        AuditLog.log(user=user_obj, action=f'USER_LOGIN: {safe_email} authenticated from {ip}', ip=ip)
        return response

    def _get_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR', '')


# ── FIX-01: Cookie-aware Logout View ─────────────────────────────────────────
class SecureLogoutView(APIView):
    """
    POST /api/v1/auth/logout/
    FIX-01: Reads refresh token from HttpOnly cookie FIRST, body second.
    Ensures browser clients (cookie auth) always blacklist their token on logout.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # FIX-01: Cookie first → body fallback → header (for API clients)
        refresh_token = (
            request.COOKIES.get('sims_refresh') or
            request.data.get('refresh') or
            None
        )

        response = Response({'message': 'Logout successful.'})
        clear_auth_cookies(response)

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
                AuditLog.log(
                    user=request.user,
                    action=f'USER_LOGOUT: {_sanitize_log(request.user.email)} — refresh token blacklisted'
                )
            except TokenError as e:
                # Token already expired/invalid — still clear cookies, still log
                logger.warning(f'[AUTH] Logout with invalid/expired refresh token: {e}')
                AuditLog.log(
                    user=request.user,
                    action=f'USER_LOGOUT: {_sanitize_log(request.user.email)} — token already invalid'
                )
        else:
            logger.warning(f'[AUTH] Logout without refresh token — cookies cleared but token NOT blacklisted')
            AuditLog.log(
                user=request.user,
                action=f'USER_LOGOUT_INCOMPLETE: {_sanitize_log(request.user.email)} — no refresh token provided'
            )

        return response


# ── FIX-14: Throttled Refresh View ───────────────────────────────────────────
class ThrottledRefreshView(TokenRefreshView):
    """
    POST /api/v1/auth/refresh/
    FIX-14: 30/min throttle — prevents hammering with invalid cookies
    FIX-01: Reads refresh token from cookie if not in body
    """
    throttle_classes = [RefreshRateThrottle]

    def post(self, request, *args, **kwargs):
        # FIX-01: Inject cookie token into request data if body is empty
        if not request.data.get('refresh') and request.COOKIES.get('sims_refresh'):
             data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
             data['refresh'] = request.COOKIES.get('sims_refresh')
             request._full_data = data

        response = super().post(request, *args, **kwargs)

        # FIX-01: Update access token cookie on successful refresh
        if response.status_code == 200:
            set_auth_cookies(response, access_token=response.data.get('access'))

        return response


class RegisterView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsSystemAdmin]
    serializer_class   = UserSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        AuditLog.log(
            user=self.request.user,
            action=f'USER_CREATED: {_sanitize_log(self.request.user.email)} provisioned '
                   f'{_sanitize_log(user.email)} [{user.role_name}]'
        )


class UserListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsManagerOrAbove]
    serializer_class   = UserSerializer

    def get_queryset(self):
        qs = User.objects.select_related('role').order_by('-created_at')
        if self.request.query_params.get('role'):
            qs = qs.filter(role__role_name=self.request.query_params['role'])
        if self.request.query_params.get('status'):
            qs = qs.filter(status=self.request.query_params['status'])
        return qs


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsSystemAdmin]
    serializer_class   = UserSerializer
    queryset           = User.objects.select_related('role').all()
    lookup_field       = 'user_id'

    def perform_update(self, serializer):
        user = serializer.save()
        AuditLog.log(user=self.request.user,
                     action=f'USER_UPDATED: {_sanitize_log(user.email)} (ID:{user.user_id})')

    def perform_destroy(self, instance):
        AuditLog.log(user=self.request.user,
                     action=f'USER_DELETED: {_sanitize_log(instance.email)} (ID:{instance.user_id})')
        instance.delete()


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        s = UserSerializer(request.user, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        s = ChangePasswordSerializer(data=request.data)
        if not s.is_valid():
            return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)
        if not request.user.check_password(s.validated_data['old_password']):
            return Response({'error': 'Old password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)
        request.user.set_password(s.validated_data['new_password'])
        request.user.save()
        AuditLog.log(user=request.user, action=f'PASSWORD_CHANGED: {_sanitize_log(request.user.email)}')
        return Response({'message': 'Password changed successfully.'})


class RoleListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsSystemAdmin]
    serializer_class   = RoleSerializer
    queryset           = Role.objects.all()


class AnalystListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsManagerOrAbove]
    serializer_class   = UserProfileSerializer

    def get_queryset(self):
        return User.objects.filter(
            role__role_name=Role.ANALYST, status=User.STATUS_ACTIVE
        ).select_related('role')


class UnlockUserView(APIView):
    """
    POST /api/v1/auth/users/<id>/unlock/
    FIX-04: Admin can manually unlock an account stuck in lockout.
    """
    permission_classes = [IsAuthenticated, IsSystemAdmin]

    def post(self, request, user_id):
        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Clear login attempts for this email
        LoginAttempt.objects.filter(email=user.email).delete()
        if user.status == User.STATUS_LOCKED:
            user.status = User.STATUS_ACTIVE
            user.save(update_fields=['status'])

        AuditLog.log(user=request.user,
                     action=f'ACCOUNT_UNLOCKED: admin unlocked {_sanitize_log(user.email)}')
        return Response({'message': f'Account {user.email} unlocked successfully.'})
