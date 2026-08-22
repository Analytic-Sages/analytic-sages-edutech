from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.enums import pg_enum
from app.db.session import Base

if TYPE_CHECKING:
    from app.models.user import User


class ArticleStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class AuthorProfile(Base):
    """Byline for Insights authors and editors. Not an instructor profile."""

    __tablename__ = "author_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    bio: Mapped[str] = mapped_column(Text, nullable=False, default="")
    photo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship()
    articles: Mapped[list[Article]] = relationship(back_populates="author")


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(180), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    cover_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    category: Mapped[str] = mapped_column(String(40), nullable=False, default="Education")
    tags: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    body: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{\"version\":1,\"blocks\":[]}'::jsonb")
    )
    status: Mapped[ArticleStatus] = mapped_column(
        pg_enum(ArticleStatus, name="article_status"),
        nullable=False,
        default=ArticleStatus.DRAFT,
    )
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("author_profiles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    byline_name: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    byline_title: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    seo_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    seo_description: Mapped[str | None] = mapped_column(String(320), nullable=True)
    og_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    read_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    newsletter_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    author: Mapped[AuthorProfile | None] = relationship(back_populates="articles")
