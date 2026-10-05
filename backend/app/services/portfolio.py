from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings
from app.models.project import Project
from app.models.user import User
from app.schemas.portfolio import MyPortfolio, PortfolioVisibilityRequest, PublicPortfolio
from app.schemas.projects import ProjectPublic
from app.services.certificates import CertificateService
from app.services.projects import ProjectService


class PortfolioService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.certificates = CertificateService(db)
        self.projects = ProjectService(db)

    def my_portfolio(self, user: User) -> MyPortfolio:
        projects = list(
            self.db.scalars(
                select(Project)
                .options(selectinload(Project.reviewer))
                .where(Project.user_id == user.id)
                .order_by(Project.created_at.desc())
            ).all()
        )
        public_url = f"{self.settings.frontend_url.rstrip('/')}/portfolio/{user.id}"
        return MyPortfolio(
            email=user.email,
            full_name=user.full_name,
            country_of_residence=user.country_of_residence,
            github_url=user.github_url,
            x_url=user.x_url,
            linkedin_url=user.linkedin_url,
            portfolio_url=user.portfolio_url,
            portfolio_public=user.portfolio_public,
            public_url=public_url if user.portfolio_public else None,
            projects=[self.projects._project_public(p) for p in projects],
            certificates=self.certificates.eligibility_for_user(user),
        )

    def set_visibility(self, user: User, payload: PortfolioVisibilityRequest) -> MyPortfolio:
        user.portfolio_public = payload.portfolio_public
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return self.my_portfolio(user)

    def public_portfolio(self, user_id: UUID) -> PublicPortfolio:
        user = self.db.get(User, user_id)
        if not user or not user.is_active or not user.portfolio_public:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
        projects = list(
            self.db.scalars(
                select(Project)
                .options(selectinload(Project.reviewer))
                .where(Project.user_id == user.id, Project.is_public.is_(True))
                .order_by(Project.created_at.desc())
            ).all()
        )
        return PublicPortfolio(
            user_id=user.id,
            full_name=user.full_name,
            country_of_residence=user.country_of_residence,
            github_url=user.github_url,
            x_url=user.x_url,
            linkedin_url=user.linkedin_url,
            portfolio_url=user.portfolio_url,
            projects=[self.projects._project_public(p) for p in projects],
        )
