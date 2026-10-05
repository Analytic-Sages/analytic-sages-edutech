from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import (
    CurrentUser,
    get_certificate_service,
    get_notification_service,
    get_portfolio_service,
    get_project_service,
)
from app.schemas.certificates import CertificateEligibilityPublic
from app.schemas.notifications import NotificationPublic, UnreadCount
from app.schemas.portfolio import MyPortfolio, PortfolioVisibilityRequest, PublicPortfolio
from app.schemas.projects import ShowcaseProject
from app.services.certificates import CertificateService
from app.services.notifications import NotificationService
from app.services.portfolio import PortfolioService
from app.services.projects import ProjectService

router = APIRouter(tags=["experience"])


@router.get("/showcase/projects", response_model=list[ShowcaseProject])
def showcase_projects(
    projects: ProjectService = Depends(get_project_service),
) -> list[ShowcaseProject]:
    return projects.list_showcase_projects()


@router.get("/portfolio/{user_id}", response_model=PublicPortfolio)
def public_portfolio(
    user_id: UUID,
    portfolio: PortfolioService = Depends(get_portfolio_service),
) -> PublicPortfolio:
    return portfolio.public_portfolio(user_id)


@router.get("/me/portfolio", response_model=MyPortfolio)
def my_portfolio(
    current_user: CurrentUser,
    portfolio: PortfolioService = Depends(get_portfolio_service),
) -> MyPortfolio:
    return portfolio.my_portfolio(current_user)


@router.patch("/me/portfolio", response_model=MyPortfolio)
def update_portfolio_visibility(
    payload: PortfolioVisibilityRequest,
    current_user: CurrentUser,
    portfolio: PortfolioService = Depends(get_portfolio_service),
) -> MyPortfolio:
    return portfolio.set_visibility(current_user, payload)


@router.get("/me/certificate-eligibility", response_model=list[CertificateEligibilityPublic])
def my_certificate_eligibility(
    current_user: CurrentUser,
    certificates: CertificateService = Depends(get_certificate_service),
) -> list[CertificateEligibilityPublic]:
    return certificates.eligibility_for_user(current_user)


@router.get("/me/notifications", response_model=list[NotificationPublic])
def my_notifications(
    current_user: CurrentUser,
    notifications: NotificationService = Depends(get_notification_service),
) -> list[NotificationPublic]:
    return notifications.list_for_user(current_user)


@router.get("/me/notifications/unread", response_model=UnreadCount)
def unread_notifications(
    current_user: CurrentUser,
    notifications: NotificationService = Depends(get_notification_service),
) -> UnreadCount:
    return UnreadCount(unread=notifications.unread_count(current_user))


@router.post("/me/notifications/read-all", response_model=UnreadCount)
def mark_notifications_read(
    current_user: CurrentUser,
    notifications: NotificationService = Depends(get_notification_service),
) -> UnreadCount:
    notifications.mark_all_read(current_user)
    return UnreadCount(unread=0)
