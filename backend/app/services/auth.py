from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.roles import UserRole
from app.core.security import SecurityService
from app.models.user import EmailVerificationToken, PasswordResetToken, RefreshToken, User
from app.schemas.auth import AuthResponse, RegisterRequest, UserPublic
from app.services.email import EmailService


class AuthService:
    INVALID_CREDENTIALS = "Invalid email or password"

    def __init__(
        self,
        db: Session,
        security: SecurityService,
        email_service: EmailService,
    ) -> None:
        self.db = db
        self.security = security
        self.email_service = email_service

    def register(self, payload: RegisterRequest) -> tuple[User, str]:
        existing = self.db.scalar(select(User).where(User.email == payload.email.lower()))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists",
            )

        user = User(
            email=payload.email.lower(),
            password_hash=self.security.hash_password(payload.password),
            full_name=payload.full_name,
            role=UserRole.STUDENT,
            email_verified=False,
        )
        self.db.add(user)
        self.db.flush()

        raw_token = self._issue_email_verification_token(user.id)
        self.db.commit()
        self.db.refresh(user)
        return user, raw_token

    def login(self, *, email: str, password: str) -> tuple[User, str, str]:
        user = self.db.scalar(select(User).where(User.email == email.lower()))
        if not user or not user.password_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=self.INVALID_CREDENTIALS,
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled",
            )
        if not self.security.verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=self.INVALID_CREDENTIALS,
            )
        if not user.email_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Please verify your email before signing in. "
                    "Check your inbox or request a new verification link."
                ),
            )

        access_token, refresh_token = self.issue_session(user)
        return user, access_token, refresh_token

    def refresh_session(self, refresh_token: str) -> tuple[User, str, str]:
        token_hash = self.security.hash_token(refresh_token)
        record = self.db.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        now = datetime.now(UTC)

        if (
            not record
            or record.revoked_at is not None
            or record.expires_at <= now
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session",
            )

        user = self.db.get(User, record.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session",
            )

        record.revoked_at = now
        access_token = self.security.create_access_token(
            user_id=str(user.id),
            role=user.role.value,
        )
        new_refresh_token = self._issue_refresh_token(user.id)
        self.db.commit()
        return user, access_token, new_refresh_token

    def logout(self, refresh_token: str | None) -> None:
        if not refresh_token:
            return

        token_hash = self.security.hash_token(refresh_token)
        record = self.db.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        if record and record.revoked_at is None:
            record.revoked_at = datetime.now(UTC)
            self.db.commit()

    def verify_email(self, token: str) -> User:
        token_hash = self.security.hash_token(token)
        record = self.db.scalar(
            select(EmailVerificationToken).where(
                EmailVerificationToken.token_hash == token_hash
            )
        )
        now = datetime.now(UTC)

        if not record or record.expires_at <= now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token",
            )

        user = self.db.get(User, record.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token",
            )

        if record.verified_at is None:
            user.email_verified = True
            record.verified_at = now
            self.db.commit()
            self.db.refresh(user)
        return user

    def resend_verification(self, email: str, next_path: str | None = None) -> None:
        user = self.db.scalar(select(User).where(User.email == email.lower()))
        if not user or user.email_verified:
            # Generic response prevents email enumeration.
            return

        raw_token = self._issue_email_verification_token(user.id)
        self.db.commit()
        self.email_service.send_verification_email(
            email=user.email,
            token=raw_token,
            next_path=next_path,
        )

    def forgot_password(self, email: str) -> None:
        user = self.db.scalar(select(User).where(User.email == email.lower()))
        if not user or not user.password_hash:
            return

        raw_token = self._issue_password_reset_token(user.id)
        self.db.commit()
        self.email_service.send_password_reset_email(email=user.email, token=raw_token)

    def reset_password(self, *, token: str, new_password: str) -> None:
        token_hash = self.security.hash_token(token)
        record = self.db.scalar(
            select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
        )
        now = datetime.now(UTC)

        if not record or record.used_at is not None or record.expires_at <= now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        user = self.db.get(User, record.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        user.password_hash = self.security.hash_password(new_password)
        record.used_at = now
        self._revoke_all_refresh_tokens(user.id)
        self.db.commit()

    def invite_instructor(self, *, email: str, full_name: str | None) -> tuple[User, bool]:
        return self.invite_staff(email=email, full_name=full_name, role=UserRole.INSTRUCTOR)

    def invite_operations(self, *, email: str, full_name: str | None) -> tuple[User, bool]:
        return self.invite_staff(email=email, full_name=full_name, role=UserRole.OPERATIONS)

    def invite_staff(
        self,
        *,
        email: str,
        full_name: str | None,
        role: UserRole,
    ) -> tuple[User, bool]:
        if role not in {UserRole.INSTRUCTOR, UserRole.OPERATIONS}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="That staff role cannot be invited",
            )
        email_normalized = email.lower()
        user = self.db.scalar(select(User).where(User.email == email_normalized))
        role_label = "operations manager" if role == UserRole.OPERATIONS else "instructor"

        if user:
            if user.role == UserRole.STUDENT:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This email already has a learner account. Use a different staff email.",
                )
            if user.role == UserRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This email is already an admin account.",
                )
            if user.role != role:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This email already has a different staff role.",
                )
            if user.password_hash:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"This {role_label} already has an account. They can sign in.",
                )
            if full_name and not user.full_name:
                user.full_name = full_name
            raw_token = self._issue_invite_token(user.id)
            self.db.commit()
            self.email_service.send_staff_invite_email(
                email=user.email,
                token=raw_token,
                full_name=user.full_name,
                role=role.value,
            )
            return user, True

        user = User(
            email=email_normalized,
            password_hash=None,
            full_name=full_name,
            role=role,
            email_verified=False,
        )
        self.db.add(user)
        self.db.flush()
        raw_token = self._issue_invite_token(user.id)
        self.db.commit()
        self.db.refresh(user)
        self.email_service.send_staff_invite_email(
            email=user.email,
            token=raw_token,
            full_name=user.full_name,
            role=role.value,
        )
        return user, False

    def accept_invite(self, *, token: str, password: str) -> tuple[User, str, str]:
        token_hash = self.security.hash_token(token)
        record = self.db.scalar(
            select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
        )
        now = datetime.now(UTC)

        if not record or record.used_at is not None or record.expires_at <= now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired invite link. Ask an admin to send a new invite.",
            )

        user = self.db.get(User, record.user_id)
        if not user or user.role not in {UserRole.INSTRUCTOR, UserRole.OPERATIONS}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired invite link. Ask an admin to send a new invite.",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled",
            )

        user.password_hash = self.security.hash_password(password)
        user.email_verified = True
        record.used_at = now
        self._revoke_all_refresh_tokens(user.id)
        access_token = self.security.create_access_token(
            user_id=str(user.id),
            role=user.role.value,
        )
        refresh_token = self._issue_refresh_token(user.id)
        self.db.commit()
        self.db.refresh(user)
        return user, access_token, refresh_token

    def login_with_google(
        self,
        *,
        google_id: str,
        email: str,
        full_name: str | None,
    ) -> tuple[User, str, str]:
        email_normalized = email.lower()
        user = self.db.scalar(select(User).where(User.google_id == google_id))

        if not user:
            user = self.db.scalar(select(User).where(User.email == email_normalized))
            if user:
                if user.google_id and user.google_id != google_id:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="This email is linked to a different Google account",
                    )
                user.google_id = google_id
                if full_name and not user.full_name:
                    user.full_name = full_name
                user.email_verified = True
            else:
                user = User(
                    email=email_normalized,
                    password_hash=None,
                    full_name=full_name,
                    role=UserRole.STUDENT,
                    email_verified=True,
                    google_id=google_id,
                )
                self.db.add(user)
                self.db.flush()

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled",
            )

        access_token = self.security.create_access_token(
            user_id=str(user.id),
            role=user.role.value,
        )
        refresh_token = self._issue_refresh_token(user.id)
        self.db.commit()
        self.db.refresh(user)
        return user, access_token, refresh_token

    def issue_session(self, user: User) -> tuple[str, str]:
        access_token = self.security.create_access_token(
            user_id=str(user.id),
            role=user.role.value,
        )
        refresh_token = self._issue_refresh_token(user.id)
        self.db.commit()
        return access_token, refresh_token

    def build_auth_response(self, user: User, access_token: str) -> AuthResponse:
        return AuthResponse(
            access_token=access_token,
            user=UserPublic.model_validate(user),
        )

    def _issue_refresh_token(self, user_id: UUID) -> str:
        raw_token = self.security.generate_opaque_token()
        self.db.add(
            RefreshToken(
                user_id=user_id,
                token_hash=self.security.hash_token(raw_token),
                expires_at=self.security.refresh_token_expires_at(),
            )
        )
        return raw_token

    def _issue_email_verification_token(self, user_id: UUID) -> str:
        raw_token = self.security.generate_opaque_token()
        self.db.add(
            EmailVerificationToken(
                user_id=user_id,
                token_hash=self.security.hash_token(raw_token),
                expires_at=self.security.email_verification_expires_at(),
            )
        )
        return raw_token

    def _issue_password_reset_token(self, user_id: UUID) -> str:
        raw_token = self.security.generate_opaque_token()
        self.db.add(
            PasswordResetToken(
                user_id=user_id,
                token_hash=self.security.hash_token(raw_token),
                expires_at=self.security.password_reset_expires_at(),
            )
        )
        return raw_token

    def _issue_invite_token(self, user_id: UUID) -> str:
        raw_token = self.security.generate_opaque_token()
        self.db.add(
            PasswordResetToken(
                user_id=user_id,
                token_hash=self.security.hash_token(raw_token),
                expires_at=self.security.invite_token_expires_at(),
            )
        )
        return raw_token

    def _revoke_all_refresh_tokens(self, user_id: UUID) -> None:
        now = datetime.now(UTC)
        tokens = self.db.scalars(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
        ).all()
        for token in tokens:
            token.revoked_at = now
