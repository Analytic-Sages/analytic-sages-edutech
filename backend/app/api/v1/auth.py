from urllib.parse import urlencode

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse

from app.api.deps import (
    CurrentUser,
    get_auth_service,
    get_google_oauth_service,
    get_rate_limiter,
    get_security_service,
    get_settings,
)
from app.core.config import Settings
from app.core.rate_limit import enforce_rate_limit
from app.core.roles import UserRole
from app.core.security import SecurityService
from app.schemas.auth import (
    AcceptInviteRequest,
    AuthProvidersResponse,
    AuthResponse,
    ForgotPasswordRequest,
    GoogleMockLoginRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    UserPublic,
    VerifyEmailRequest,
)
from app.services.auth import AuthService
from app.services.google_oauth import GoogleOAuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _optional_next_path(next_path: str | None) -> str | None:
    if not next_path or not next_path.startswith("/") or next_path.startswith("//"):
        return None
    if next_path == "/dashboard":
        return None
    return next_path


def _safe_next_path(next_path: str | None) -> str:
    return _optional_next_path(next_path) or "/dashboard"


def _post_login_path(role: UserRole, next_path: str) -> str:
    if next_path != "/dashboard":
        return next_path
    if role == UserRole.ADMIN:
        return "/admin"
    if role == UserRole.INSTRUCTOR:
        return "/staff"
    if role == UserRole.OPERATIONS:
        return "/admin/events"
    return next_path


@router.post("/register", response_model=MessageResponse, status_code=201)
def register(
    request: Request,
    payload: RegisterRequest,
    background_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service),
    rate_limiter=Depends(get_rate_limiter),
) -> MessageResponse:
    enforce_rate_limit(rate_limiter, request, scope="auth-register")
    user, raw_token = auth_service.register(payload)
    background_tasks.add_task(
        auth_service.email_service.send_verification_email,
        email=user.email,
        token=raw_token,
        next_path=payload.next,
    )
    return MessageResponse(
        message="Account created. Check your email to verify your address before signing in."
    )


@router.post("/login", response_model=AuthResponse)
def login(
    request: Request,
    payload: LoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    security: SecurityService = Depends(get_security_service),
    settings: Settings = Depends(get_settings),
    rate_limiter=Depends(get_rate_limiter),
) -> AuthResponse:
    enforce_rate_limit(rate_limiter, request, scope="auth-login")
    user, access_token, refresh_token = auth_service.login(
        email=payload.email,
        password=payload.password,
    )
    security.set_refresh_cookie(response, refresh_token)
    return auth_service.build_auth_response(user, access_token)


@router.post("/session", response_model=AuthResponse)
def persist_session(
    response: Response,
    current_user: CurrentUser,
    auth_service: AuthService = Depends(get_auth_service),
    security: SecurityService = Depends(get_security_service),
) -> AuthResponse:
    """Mint a first-party refresh cookie from a valid access token (Google callback, etc.)."""
    access_token, refresh_token = auth_service.issue_session(current_user)
    security.set_refresh_cookie(response, refresh_token)
    return auth_service.build_auth_response(current_user, access_token)


@router.post("/refresh", response_model=AuthResponse)
def refresh_session(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    security: SecurityService = Depends(get_security_service),
    settings: Settings = Depends(get_settings),
    rate_limiter=Depends(get_rate_limiter),
) -> AuthResponse:
    enforce_rate_limit(rate_limiter, request, scope="auth-refresh")
    refresh_token = request.cookies.get(settings.refresh_cookie_name)
    if not refresh_token:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    user, access_token, new_refresh_token = auth_service.refresh_session(refresh_token)
    security.set_refresh_cookie(response, new_refresh_token)
    return auth_service.build_auth_response(user, access_token)


@router.post("/logout", response_model=MessageResponse)
def logout(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    security: SecurityService = Depends(get_security_service),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    refresh_token = request.cookies.get(settings.refresh_cookie_name)
    auth_service.logout(refresh_token)
    security.clear_refresh_cookie(response)
    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=UserPublic)
def get_me(current_user: CurrentUser) -> UserPublic:
    return UserPublic.model_validate(current_user)


@router.post("/verify-email", response_model=AuthResponse)
def verify_email(
    request: Request,
    payload: VerifyEmailRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    security: SecurityService = Depends(get_security_service),
    rate_limiter=Depends(get_rate_limiter),
) -> AuthResponse:
    enforce_rate_limit(rate_limiter, request, scope="auth-verify")
    user = auth_service.verify_email(payload.token)
    access_token, refresh_token = auth_service.issue_session(user)
    security.set_refresh_cookie(response, refresh_token)
    return auth_service.build_auth_response(user, access_token)


@router.post("/resend-verification", response_model=MessageResponse)
def resend_verification(
    request: Request,
    payload: ResendVerificationRequest,
    auth_service: AuthService = Depends(get_auth_service),
    rate_limiter=Depends(get_rate_limiter),
) -> MessageResponse:
    enforce_rate_limit(rate_limiter, request, scope="auth-resend")
    auth_service.resend_verification(payload.email, next_path=_optional_next_path(payload.next))
    return MessageResponse(
        message="If an unverified account exists for that email, a verification link has been sent."
    )


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
    rate_limiter=Depends(get_rate_limiter),
) -> MessageResponse:
    enforce_rate_limit(rate_limiter, request, scope="auth-forgot")
    auth_service.forgot_password(payload.email)
    return MessageResponse(
        message="If an account exists for that email, password reset instructions have been sent."
    )


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(
    request: Request,
    payload: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
    rate_limiter=Depends(get_rate_limiter),
) -> MessageResponse:
    enforce_rate_limit(rate_limiter, request, scope="auth-reset")
    auth_service.reset_password(token=payload.token, new_password=payload.new_password)
    return MessageResponse(message="Password updated successfully")


@router.post("/accept-invite", response_model=AuthResponse)
def accept_invite(
    request: Request,
    payload: AcceptInviteRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    security: SecurityService = Depends(get_security_service),
    rate_limiter=Depends(get_rate_limiter),
) -> AuthResponse:
    enforce_rate_limit(rate_limiter, request, scope="auth-invite")
    user, access_token, refresh_token = auth_service.accept_invite(
        token=payload.token,
        password=payload.password,
    )
    security.set_refresh_cookie(response, refresh_token)
    return auth_service.build_auth_response(user, access_token)


@router.get("/providers", response_model=AuthProvidersResponse)
def auth_providers(settings: Settings = Depends(get_settings)) -> AuthProvidersResponse:
    mode = settings.google_auth_mode
    return AuthProvidersResponse(
        google={
            "enabled": mode != "disabled",
            "mode": mode,
            "start_url": "/api/v1/auth/google",
        },
        email_password=True,
    )


@router.get("/google")
def google_login_start(
    next: str = "/dashboard",
    settings: Settings = Depends(get_settings),
    google_oauth: GoogleOAuthService = Depends(get_google_oauth_service),
):
    next_path = _safe_next_path(next)
    mode = settings.google_auth_mode

    if mode == "disabled":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google login is not configured in production",
        )

    if mode == "mock":
        query = urlencode({"next": next_path})
        return RedirectResponse(
            url=f"{settings.frontend_url}/auth/google-mock?{query}",
            status_code=status.HTTP_302_FOUND,
        )

    state = google_oauth.create_state(next_path=next_path)
    return RedirectResponse(
        url=google_oauth.authorization_url(state=state),
        status_code=status.HTTP_302_FOUND,
    )


@router.get("/google/callback")
def google_login_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    auth_service: AuthService = Depends(get_auth_service),
    security: SecurityService = Depends(get_security_service),
    settings: Settings = Depends(get_settings),
    google_oauth: GoogleOAuthService = Depends(get_google_oauth_service),
):
    if error:
        query = urlencode({"error": error})
        return RedirectResponse(
            url=f"{settings.frontend_url}/login?{query}",
            status_code=status.HTTP_302_FOUND,
        )
    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Google OAuth code or state",
        )

    state_payload = google_oauth.parse_state(state)
    next_path = _safe_next_path(state_payload.get("next"))
    profile = google_oauth.exchange_code(code)

    google_id = profile.get("sub")
    email = profile.get("email")
    if not google_id or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google profile did not include email",
        )
    if not profile.get("email_verified", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google email is not verified",
        )

    user, access_token, refresh_token = auth_service.login_with_google(
        google_id=str(google_id),
        email=str(email),
        full_name=profile.get("name"),
    )
    next_path = _post_login_path(user.role, next_path)

    query = urlencode(
        {
            "access_token": access_token,
            "next": next_path,
            "method": "google",
        }
    )
    redirect = RedirectResponse(
        url=f"{settings.frontend_url}/auth/callback?{query}",
        status_code=status.HTTP_302_FOUND,
    )
    security.set_refresh_cookie(redirect, refresh_token)
    return redirect


@router.post("/google/mock", response_model=AuthResponse)
def google_mock_login(
    request: Request,
    payload: GoogleMockLoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    security: SecurityService = Depends(get_security_service),
    settings: Settings = Depends(get_settings),
    rate_limiter=Depends(get_rate_limiter),
) -> AuthResponse:
    """Dev-only Google login when GOOGLE_CLIENT_ID/SECRET are unset."""
    if settings.is_production or settings.google_oauth_configured:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mock Google login is only available in development without live Google keys",
        )

    enforce_rate_limit(rate_limiter, request, scope="auth-google-mock")
    google_id = f"mock-google-{payload.email.lower()}"
    user, access_token, refresh_token = auth_service.login_with_google(
        google_id=google_id,
        email=payload.email,
        full_name=payload.full_name,
    )
    security.set_refresh_cookie(response, refresh_token)
    return auth_service.build_auth_response(user, access_token)
