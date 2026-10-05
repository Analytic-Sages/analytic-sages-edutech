from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.certificates import CertificateEligibilityPublic
from app.schemas.projects import ProjectPublic


class PublicPortfolio(BaseModel):
    user_id: UUID
    full_name: str | None = None
    country_of_residence: str | None = None
    github_url: str | None = None
    x_url: str | None = None
    linkedin_url: str | None = None
    portfolio_url: str | None = None
    projects: list[ProjectPublic] = Field(default_factory=list)


class MyPortfolio(BaseModel):
    email: str
    full_name: str | None = None
    country_of_residence: str | None = None
    github_url: str | None = None
    x_url: str | None = None
    linkedin_url: str | None = None
    portfolio_url: str | None = None
    portfolio_public: bool = False
    public_url: str | None = None
    projects: list[ProjectPublic] = Field(default_factory=list)
    certificates: list[CertificateEligibilityPublic] = Field(default_factory=list)


class PortfolioVisibilityRequest(BaseModel):
    portfolio_public: bool
