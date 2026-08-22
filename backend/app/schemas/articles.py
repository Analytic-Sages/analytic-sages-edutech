from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

ArticleStatusValue = Literal["draft", "pending_review", "published", "archived"]
ChartType = Literal["line", "bar", "pie", "scatter"]


class AuthorPublic(BaseModel):
    name: str
    title: str = ""
    bio: str = ""
    photo_url: str | None = None


class ArticleCardPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    title: str
    excerpt: str
    category: str
    cover_image_url: str | None = None
    featured: bool = False
    read_time_minutes: int
    published_at: datetime | None = None
    author: AuthorPublic


class ArticlePublic(ArticleCardPublic):
    body: dict[str, Any]
    tags: list[str] = Field(default_factory=list)
    seo_title: str | None = None
    seo_description: str | None = None
    og_image_url: str | None = None
    related: list[ArticleCardPublic] = Field(default_factory=list)


class ArticleWrite(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    excerpt: str = Field(default="", max_length=500)
    slug: str | None = Field(default=None, max_length=180)
    cover_image_url: str | None = Field(default=None, max_length=512)
    category: str = Field(default="Education", max_length=40)
    tags: list[str] = Field(default_factory=list)
    body: dict[str, Any] | None = None
    seo_title: str | None = Field(default=None, max_length=200)
    seo_description: str | None = Field(default=None, max_length=320)
    og_image_url: str | None = Field(default=None, max_length=512)
    featured: bool | None = None


class ArticleStudio(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    title: str
    excerpt: str
    cover_image_url: str | None
    category: str
    tags: list[str]
    body: dict[str, Any]
    status: ArticleStatusValue
    featured: bool
    seo_title: str | None
    seo_description: str | None
    og_image_url: str | None
    read_time_minutes: int
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime
    author: AuthorPublic
    can_publish: bool = False
    can_submit: bool = False


class ArticleStudioRow(BaseModel):
    id: UUID
    slug: str
    title: str
    status: ArticleStatusValue
    category: str
    updated_at: datetime
    published_at: datetime | None = None
    author_name: str


class UploadResponse(BaseModel):
    url: str
    alt_suggestion: str = ""


class SubscribeRequest(BaseModel):
    email: EmailStr
