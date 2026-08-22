import logging
import re
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.roles import UserRole
from app.models.article import Article, ArticleStatus, AuthorProfile
from app.models.user import User
from app.schemas.articles import (
    ArticleCardPublic,
    ArticlePublic,
    ArticleStudio,
    ArticleStudioRow,
    ArticleWrite,
    AuthorPublic,
)
from app.services.article_content import empty_body, reading_minutes, validate_body
from app.services.email import EmailService

logger = logging.getLogger(__name__)

SLUG_RE = re.compile(r"[^a-z0-9]+")
PUBLISHERS = {UserRole.ADMIN, UserRole.EDITOR}
WRITERS = {UserRole.ADMIN, UserRole.EDITOR, UserRole.AUTHOR}


def slugify(value: str) -> str:
    slug = SLUG_RE.sub("-", value.lower()).strip("-")
    return slug[:180] or "article"


class InsightService:
    def __init__(self, db: Session, email_service: EmailService | None = None) -> None:
        self.db = db
        self.email_service = email_service

    def is_publisher(self, user: User) -> bool:
        return user.role in PUBLISHERS

    def is_writer(self, user: User) -> bool:
        return user.role in WRITERS

    def ensure_profile(self, user: User) -> AuthorProfile:
        profile = self.db.scalar(select(AuthorProfile).where(AuthorProfile.user_id == user.id))
        if profile:
            return profile
        if user.role not in WRITERS:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not an Insights author")
        profile = AuthorProfile(
            user_id=user.id,
            display_name=user.full_name or user.email.split("@")[0],
            title="Editor" if user.role == UserRole.EDITOR else "Author" if user.role == UserRole.AUTHOR else "Analytic Sages",
        )
        self.db.add(profile)
        self.db.flush()
        return profile

    def _author_public(self, article: Article) -> AuthorPublic:
        if article.author:
            return AuthorPublic(
                name=article.author.display_name,
                title=article.author.title,
                bio=article.author.bio,
                photo_url=article.author.photo_url,
            )
        return AuthorPublic(name=article.byline_name or "Analytic Sages", title=article.byline_title)

    def _card(self, article: Article) -> ArticleCardPublic:
        return ArticleCardPublic(
            slug=article.slug,
            title=article.title,
            excerpt=article.excerpt,
            category=article.category,
            cover_image_url=article.cover_image_url,
            featured=article.featured,
            read_time_minutes=article.read_time_minutes,
            published_at=article.published_at,
            author=self._author_public(article),
        )

    def _studio(self, article: Article, user: User) -> ArticleStudio:
        return ArticleStudio(
            id=article.id,
            slug=article.slug,
            title=article.title,
            excerpt=article.excerpt,
            cover_image_url=article.cover_image_url,
            category=article.category,
            tags=list(article.tags or []),
            body=article.body,
            status=article.status.value,
            featured=article.featured,
            seo_title=article.seo_title,
            seo_description=article.seo_description,
            og_image_url=article.og_image_url,
            read_time_minutes=article.read_time_minutes,
            published_at=article.published_at,
            created_at=article.created_at,
            updated_at=article.updated_at,
            author=self._author_public(article),
            can_publish=self.is_publisher(user),
            can_submit=user.role == UserRole.AUTHOR and article.status in {
                ArticleStatus.DRAFT,
                ArticleStatus.PENDING_REVIEW,
            },
        )

    def _unique_slug(self, title: str, *, exclude_id: UUID | None = None) -> str:
        base = slugify(title)
        slug = base
        n = 2
        while True:
            existing = self.db.scalar(select(Article).where(Article.slug == slug))
            if not existing or existing.id == exclude_id:
                return slug
            slug = f"{base}-{n}"[:180]
            n += 1

    def list_published(self) -> list[ArticleCardPublic]:
        rows = self.db.scalars(
            select(Article)
            .options(selectinload(Article.author))
            .where(Article.status == ArticleStatus.PUBLISHED)
            .order_by(Article.published_at.desc().nullslast(), Article.created_at.desc())
        ).all()
        return [self._card(row) for row in rows]

    def get_published(self, slug: str) -> ArticlePublic:
        article = self.db.scalar(
            select(Article)
            .options(selectinload(Article.author))
            .where(Article.slug == slug, Article.status == ArticleStatus.PUBLISHED)
        )
        if not article:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
        related_rows = self.db.scalars(
            select(Article)
            .options(selectinload(Article.author))
            .where(
                Article.status == ArticleStatus.PUBLISHED,
                Article.id != article.id,
                Article.category == article.category,
            )
            .order_by(Article.published_at.desc().nullslast())
            .limit(3)
        ).all()
        return ArticlePublic(
            **self._card(article).model_dump(),
            body=article.body,
            tags=list(article.tags or []),
            seo_title=article.seo_title,
            seo_description=article.seo_description,
            og_image_url=article.og_image_url,
            related=[self._card(row) for row in related_rows],
        )

    def list_studio(self, user: User) -> list[ArticleStudioRow]:
        query = select(Article).options(selectinload(Article.author)).order_by(Article.updated_at.desc())
        if user.role == UserRole.AUTHOR:
            profile = self.ensure_profile(user)
            query = query.where(Article.author_id == profile.id)
        elif not self.is_publisher(user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        rows = self.db.scalars(query).all()
        return [
            ArticleStudioRow(
                id=row.id,
                slug=row.slug,
                title=row.title,
                status=row.status.value,
                category=row.category,
                updated_at=row.updated_at,
                published_at=row.published_at,
                author_name=self._author_public(row).name,
            )
            for row in rows
        ]

    def get_studio(self, user: User, article_id: UUID) -> ArticleStudio:
        article = self._get_for_user(user, article_id)
        return self._studio(article, user)

    def create(self, user: User, payload: ArticleWrite) -> ArticleStudio:
        if not self.is_writer(user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        profile = self.ensure_profile(user)
        body = validate_body(payload.body or empty_body())
        article = Article(
            slug=self._unique_slug(payload.slug or payload.title),
            title=payload.title.strip(),
            excerpt=payload.excerpt.strip(),
            cover_image_url=payload.cover_image_url,
            category=payload.category.strip() or "Education",
            tags=[tag.strip() for tag in payload.tags if tag.strip()][:12],
            body=body,
            status=ArticleStatus.DRAFT,
            author_id=profile.id,
            byline_name=profile.display_name,
            byline_title=profile.title,
            seo_title=payload.seo_title,
            seo_description=payload.seo_description,
            og_image_url=payload.og_image_url,
            featured=bool(payload.featured) if self.is_publisher(user) else False,
            read_time_minutes=reading_minutes(body),
        )
        self.db.add(article)
        self.db.commit()
        self.db.refresh(article)
        return self._studio(article, user)

    def update(self, user: User, article_id: UUID, payload: ArticleWrite) -> ArticleStudio:
        article = self._get_for_user(user, article_id, for_edit=True)
        body = validate_body(payload.body or article.body)
        article.title = payload.title.strip()
        article.excerpt = payload.excerpt.strip()
        if payload.slug and payload.slug != article.slug:
            article.slug = self._unique_slug(payload.slug, exclude_id=article.id)
        article.cover_image_url = payload.cover_image_url
        article.category = payload.category.strip() or article.category
        article.tags = [tag.strip() for tag in payload.tags if tag.strip()][:12]
        article.body = body
        article.seo_title = payload.seo_title
        article.seo_description = payload.seo_description
        article.og_image_url = payload.og_image_url
        if payload.featured is not None and self.is_publisher(user):
            article.featured = payload.featured
        article.read_time_minutes = reading_minutes(body)
        if article.author:
            article.byline_name = article.author.display_name
            article.byline_title = article.author.title
        self.db.commit()
        self.db.refresh(article)
        return self._studio(article, user)

    def submit(self, user: User, article_id: UUID) -> ArticleStudio:
        article = self._get_for_user(user, article_id, for_edit=True)
        if user.role != UserRole.AUTHOR:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only authors submit for review. Editors can publish directly.",
            )
        if article.status not in {ArticleStatus.DRAFT, ArticleStatus.PENDING_REVIEW}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This article cannot be submitted")
        article.status = ArticleStatus.PENDING_REVIEW
        self.db.commit()
        self.db.refresh(article)
        return self._studio(article, user)

    def publish(self, user: User, article_id: UUID) -> ArticleStudio:
        if not self.is_publisher(user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Authors cannot publish. An editor reviews and publishes.",
            )
        article = self._get_for_user(user, article_id)
        if article.status == ArticleStatus.ARCHIVED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unarchive before publishing")
        should_notify = article.newsletter_sent_at is None
        article.status = ArticleStatus.PUBLISHED
        article.published_at = article.published_at or datetime.now(UTC)
        if should_notify and self.email_service:
            sent = self.email_service.send_insight_newsletter(
                title=article.title,
                excerpt=article.excerpt,
                byline=article.byline_name,
                slug=article.slug,
            )
            if sent:
                article.newsletter_sent_at = datetime.now(UTC)
            else:
                logger.warning(
                    "Published %s but the Insights list email did not send; retry by publishing again",
                    article.slug,
                )
        self.db.commit()
        self.db.refresh(article)
        return self._studio(article, user)

    def unpublish(self, user: User, article_id: UUID) -> ArticleStudio:
        if not self.is_publisher(user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Authors cannot unpublish")
        article = self._get_for_user(user, article_id)
        article.status = ArticleStatus.DRAFT
        self.db.commit()
        self.db.refresh(article)
        return self._studio(article, user)

    def return_to_draft(self, user: User, article_id: UUID) -> ArticleStudio:
        if not self.is_publisher(user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Authors cannot change review status")
        article = self._get_for_user(user, article_id)
        article.status = ArticleStatus.DRAFT
        self.db.commit()
        self.db.refresh(article)
        return self._studio(article, user)

    def archive(self, user: User, article_id: UUID) -> ArticleStudio:
        if not self.is_publisher(user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Authors cannot archive")
        article = self._get_for_user(user, article_id)
        article.status = ArticleStatus.ARCHIVED
        self.db.commit()
        self.db.refresh(article)
        return self._studio(article, user)

    def _get_for_user(self, user: User, article_id: UUID, *, for_edit: bool = False) -> Article:
        article = self.db.scalar(
            select(Article).options(selectinload(Article.author)).where(Article.id == article_id)
        )
        if not article:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
        if self.is_publisher(user):
            return article
        if user.role != UserRole.AUTHOR:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        profile = self.ensure_profile(user)
        if article.author_id != profile.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only open your own articles")
        if for_edit and article.status not in {ArticleStatus.DRAFT, ArticleStatus.PENDING_REVIEW}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Published articles can only be edited by an editor",
            )
        return article
