"""
FIX-02: HttpOnly Cookie-Based JWT Authentication
Replaces localStorage storage — XSS cannot access HttpOnly cookies.
Tokens set as SameSite=Strict + Secure (HTTPS) cookies by the server.
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from django.conf import settings


class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that reads access token from HttpOnly cookie
    instead of Authorization header. Falls back to header for API clients.
    """
    COOKIE_NAME = 'sims_access'

    def authenticate(self, request):
        # Try HttpOnly cookie first (browser clients)
        raw_token = request.COOKIES.get(self.COOKIE_NAME)

        # Fall back to Authorization header (Postman / API clients / mobile)
        if raw_token is None:
            header = self.get_header(request)
            if header is not None:
                raw_token = self.get_raw_token(header)

        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except InvalidToken:
            return None


def set_auth_cookies(response, access_token, refresh_token=None):
    """
    FIX-02: Set JWT tokens as HttpOnly + Secure + SameSite=Strict cookies.
    Called after successful login/refresh.
    """
    is_secure = not settings.DEBUG  # HTTPS only in production

    # Access token — short-lived, HttpOnly
    response.set_cookie(
        key='sims_access',
        value=str(access_token),
        max_age=7200,           # 2 hours — matches SIMPLE_JWT ACCESS_TOKEN_LIFETIME
        httponly=True,          # XSS cannot read this
        secure=is_secure,       # HTTPS only in production
        samesite='Strict',      # CSRF protection
        path='/',
    )

    # Refresh token — longer-lived, scoped to refresh endpoint only
    if refresh_token:
        response.set_cookie(
            key='sims_refresh',
            value=str(refresh_token),
            max_age=604800,         # 7 days — matches REFRESH_TOKEN_LIFETIME
            httponly=True,
            secure=is_secure,
            samesite='Strict',
            path='/api/v1/auth/refresh/',  # Scoped — only sent to refresh endpoint
        )

    return response


def clear_auth_cookies(response):
    """Clear auth cookies on logout."""
    response.delete_cookie('sims_access',  path='/')
    response.delete_cookie('sims_refresh', path='/api/v1/auth/refresh/')
    return response
