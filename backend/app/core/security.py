import hashlib
import logging
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Response

from app.core.config import Settings

logger = logging.getLogger(__name__)

password_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
)


class SecurityService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def hash_password(self, password: str) -> str:
        return password_hasher.hash(password)

    def verify_password(self, password: str, password_hash: str) -> bool:
        try:
            return password_hasher.verify(password_hash, password)
        except VerifyMismatchError:
            return False

    def create_access_token(self, *, user_id: str, role: str) -> str:
        expires = datetime.now(UTC) + timedelta(minutes=self.settings.access_token_expire_minutes)
        payload = {
            "sub": user_id,
            "role": role,
            "type": "access",
            "exp": expires,
            "iat": datetime.now(UTC),
        }
        return jwt.encode(payload, self.settings.secret_key, algorithm="HS256")

    def decode_access_token(self, token: str) -> dict:
        return jwt.decode(token, self.settings.secret_key, algorithms=["HS256"])

    @staticmethod
    def generate_opaque_token() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def set_refresh_cookie(self, response: Response, refresh_token: str) -> None:
        max_age = self.settings.refresh_token_expire_days * 24 * 60 * 60
        cookie_kwargs = {
            "key": self.settings.refresh_cookie_name,
            "httponly": True,
            "secure": self.settings.cookie_secure,
            "samesite": self.settings.refresh_cookie_samesite,
            "domain": self.settings.cookie_domain,
        }
        # Drop the legacy path-scoped cookie from the cross-origin setup.
        response.delete_cookie(**cookie_kwargs, path="/api/v1/auth")
        response.set_cookie(
            **cookie_kwargs,
            value=refresh_token,
            max_age=max_age,
            path=self.settings.refresh_cookie_path,
        )

    def clear_refresh_cookie(self, response: Response) -> None:
        cookie_kwargs = {
            "key": self.settings.refresh_cookie_name,
            "path": self.settings.refresh_cookie_path,
            "domain": self.settings.cookie_domain,
            "secure": self.settings.cookie_secure,
            "httponly": True,
            "samesite": self.settings.refresh_cookie_samesite,
        }
        response.delete_cookie(**cookie_kwargs)
        response.delete_cookie(**{**cookie_kwargs, "path": "/api/v1/auth"})

    def refresh_token_expires_at(self) -> datetime:
        return datetime.now(UTC) + timedelta(days=self.settings.refresh_token_expire_days)

    def email_verification_expires_at(self) -> datetime:
        return datetime.now(UTC) + timedelta(hours=self.settings.email_verification_expire_hours)

    def password_reset_expires_at(self) -> datetime:
        return datetime.now(UTC) + timedelta(hours=self.settings.password_reset_expire_hours)

    def invite_token_expires_at(self) -> datetime:
        return datetime.now(UTC) + timedelta(hours=self.settings.invite_expire_hours)
