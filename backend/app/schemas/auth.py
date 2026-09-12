from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.core.roles import UserRole
from app.services.phone import normalize_iso2, normalize_phone


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str | None
    role: UserRole
    email_verified: bool
    is_active: bool
    phone_number: str | None = None
    phone_country_code: str | None = None
    phone_verified: bool = False
    country_of_residence: str | None = None
    created_at: datetime


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)
    phone_number: str | None = Field(default=None, max_length=32)
    phone_country_code: str | None = Field(default=None, max_length=2)
    country_of_residence: str | None = Field(default=None, max_length=2)
    next: str | None = Field(default=None, max_length=512)

    @model_validator(mode="after")
    def normalize_contact_fields(self) -> "RegisterRequest":
        phone, phone_cc = normalize_phone(
            self.phone_number,
            phone_country_code=self.phone_country_code,
        )
        residence = normalize_iso2(self.country_of_residence, field="country_of_residence")
        self.phone_number = phone
        self.phone_country_code = phone_cc
        self.country_of_residence = residence
        return self


class UpdateProfileRequest(BaseModel):
    """Partial profile update. Omitted fields are left unchanged; empty clears phone/residence."""

    full_name: str | None = Field(default=None, max_length=255)
    phone_number: str | None = Field(default=None, max_length=32)
    phone_country_code: str | None = Field(default=None, max_length=2)
    country_of_residence: str | None = Field(default=None, max_length=2)
    clear_phone: bool = False
    clear_country_of_residence: bool = False

    @model_validator(mode="after")
    def normalize_contact_fields(self) -> "UpdateProfileRequest":
        if self.clear_phone or (
            self.phone_number is not None and not str(self.phone_number).strip()
        ):
            self.phone_number = None
            self.phone_country_code = None
            self.clear_phone = True
        elif self.phone_number is not None or self.phone_country_code is not None:
            phone, phone_cc = normalize_phone(
                self.phone_number,
                phone_country_code=self.phone_country_code,
            )
            self.phone_number = phone
            self.phone_country_code = phone_cc

        if self.clear_country_of_residence or (
            self.country_of_residence is not None and not str(self.country_of_residence).strip()
        ):
            self.country_of_residence = None
            self.clear_country_of_residence = True
        elif self.country_of_residence is not None:
            self.country_of_residence = normalize_iso2(
                self.country_of_residence,
                field="country_of_residence",
            )
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class MessageResponse(BaseModel):
    message: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=10, max_length=512)
    new_password: str = Field(min_length=8, max_length=128)


class AcceptInviteRequest(BaseModel):
    token: str = Field(min_length=10, max_length=512)
    password: str = Field(min_length=8, max_length=128)


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=10, max_length=512)


class ResendVerificationRequest(BaseModel):
    email: EmailStr
    next: str | None = Field(default=None, max_length=512)


class GoogleMockLoginRequest(BaseModel):
    email: EmailStr
    full_name: str | None = Field(default="Google User", max_length=255)
    next: str | None = Field(default="/dashboard", max_length=512)


class AuthProvidersResponse(BaseModel):
    google: dict
    email_password: bool = True
