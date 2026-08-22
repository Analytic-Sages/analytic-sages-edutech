from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse

from app.api.deps import (
    CurrentUser,
    get_email_service,
    get_insight_service,
    get_rate_limiter,
    get_storage_service,
    require_publisher,
    require_writer,
)
from app.core.rate_limit import enforce_rate_limit
from app.models.user import User
from app.schemas.articles import (
    ArticleCardPublic,
    ArticlePublic,
    ArticleStudio,
    ArticleStudioRow,
    ArticleWrite,
    SubscribeRequest,
    UploadResponse,
)
from app.schemas.auth import MessageResponse
from app.services.email import EmailService
from app.services.insights import InsightService
from app.services.storage import StorageService

router = APIRouter(tags=["insights"])


@router.get("/insights", response_model=list[ArticleCardPublic])
def list_insights(insights: InsightService = Depends(get_insight_service)) -> list[ArticleCardPublic]:
    return insights.list_published()


@router.get("/insights/{slug}", response_model=ArticlePublic)
def get_insight(slug: str, insights: InsightService = Depends(get_insight_service)) -> ArticlePublic:
    return insights.get_published(slug)


@router.post("/insights/subscribe", response_model=MessageResponse)
def subscribe_insights(
    request: Request,
    payload: SubscribeRequest,
    email_service: EmailService = Depends(get_email_service),
    rate_limiter=Depends(get_rate_limiter),
) -> MessageResponse:
    enforce_rate_limit(rate_limiter, request, scope="insights-subscribe")
    added = email_service.add_subscriber(str(payload.email))
    if not added:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="We could not add you to the list right now. Please try again shortly.",
        )
    return MessageResponse(
        message="You're on the list. New Insights will be emailed when they are published."
    )


@router.get("/media/{filename}")
def get_media(filename: str, storage: StorageService = Depends(get_storage_service)) -> FileResponse:
    path = storage.resolve_file(filename)
    return FileResponse(path)


@router.post("/insights/uploads", response_model=UploadResponse)
async def upload_insight_image(
    _: User = Depends(require_writer),
    storage: StorageService = Depends(get_storage_service),
    file: UploadFile = File(...),
) -> UploadResponse:
    url = await storage.save_image(file)
    return UploadResponse(url=url)


@router.get("/studio/articles", response_model=list[ArticleStudioRow])
def list_studio_articles(
    current_user: CurrentUser,
    insights: InsightService = Depends(get_insight_service),
) -> list[ArticleStudioRow]:
    return insights.list_studio(current_user)


@router.post("/studio/articles", response_model=ArticleStudio, status_code=status.HTTP_201_CREATED)
def create_article(
    payload: ArticleWrite,
    current_user: CurrentUser,
    insights: InsightService = Depends(get_insight_service),
) -> ArticleStudio:
    return insights.create(current_user, payload)


@router.get("/studio/articles/{article_id}", response_model=ArticleStudio)
def get_studio_article(
    article_id: UUID,
    current_user: CurrentUser,
    insights: InsightService = Depends(get_insight_service),
) -> ArticleStudio:
    return insights.get_studio(current_user, article_id)


@router.patch("/studio/articles/{article_id}", response_model=ArticleStudio)
def update_article(
    article_id: UUID,
    payload: ArticleWrite,
    current_user: CurrentUser,
    insights: InsightService = Depends(get_insight_service),
) -> ArticleStudio:
    return insights.update(current_user, article_id, payload)


@router.post("/studio/articles/{article_id}/submit", response_model=ArticleStudio)
def submit_article(
    article_id: UUID,
    current_user: CurrentUser,
    insights: InsightService = Depends(get_insight_service),
) -> ArticleStudio:
    return insights.submit(current_user, article_id)


@router.post("/studio/articles/{article_id}/publish", response_model=ArticleStudio)
def publish_article(
    article_id: UUID,
    current_user: User = Depends(require_publisher),
    insights: InsightService = Depends(get_insight_service),
) -> ArticleStudio:
    return insights.publish(current_user, article_id)


@router.post("/studio/articles/{article_id}/unpublish", response_model=ArticleStudio)
def unpublish_article(
    article_id: UUID,
    current_user: User = Depends(require_publisher),
    insights: InsightService = Depends(get_insight_service),
) -> ArticleStudio:
    return insights.unpublish(current_user, article_id)


@router.post("/studio/articles/{article_id}/return", response_model=ArticleStudio)
def return_article(
    article_id: UUID,
    current_user: User = Depends(require_publisher),
    insights: InsightService = Depends(get_insight_service),
) -> ArticleStudio:
    return insights.return_to_draft(current_user, article_id)


@router.post("/studio/articles/{article_id}/archive", response_model=ArticleStudio)
def archive_article(
    article_id: UUID,
    current_user: User = Depends(require_publisher),
    insights: InsightService = Depends(get_insight_service),
) -> ArticleStudio:
    return insights.archive(current_user, article_id)
