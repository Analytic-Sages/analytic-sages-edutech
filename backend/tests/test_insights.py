from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.roles import UserRole
from app.core.security import SecurityService
from app.db.session import SessionLocal
from app.main import app
from app.models.article import Article, ArticleStatus, AuthorProfile
from app.models.user import User
from app.services.email import EmailService
from app.services.seed_insights import seed_insights_articles

client = TestClient(app)


def _token_for(user: User) -> str:
    return SecurityService(get_settings()).create_access_token(
        user_id=str(user.id), role=user.role.value
    )


def _auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token_for(user)}"}


def _make_user(email: str, role: UserRole) -> User:
    db = SessionLocal()
    try:
        user = User(email=email, full_name=email.split("@")[0], role=role, email_verified=True, is_active=True)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def _cleanup_user(email: str) -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return
        profile = db.query(AuthorProfile).filter(AuthorProfile.user_id == user.id).first()
        if profile:
            db.query(Article).filter(Article.author_id == profile.id).delete()
            db.delete(profile)
        db.delete(user)
        db.commit()
    finally:
        db.close()


def test_public_insights_include_seeded_slug():
    db = SessionLocal()
    try:
        seed_insights_articles(db)
        db.commit()
    finally:
        db.close()
    response = client.get("/api/v1/insights")
    assert response.status_code == 200
    slugs = {item["slug"] for item in response.json()}
    assert "what-is-on-chain-analysis-beginners-guide" in slugs
    detail = client.get("/api/v1/insights/what-is-on-chain-analysis-beginners-guide")
    assert detail.status_code == 200
    assert detail.json()["body"]["blocks"][0]["type"] == "paragraph"


def test_author_cannot_publish_editor_can():
    author_email = f"author-{uuid.uuid4()}@example.com"
    editor_email = f"editor-{uuid.uuid4()}@example.com"
    instructor_email = f"instructor-{uuid.uuid4()}@example.com"
    _cleanup_user(author_email)
    _cleanup_user(editor_email)
    _cleanup_user(instructor_email)
    author = _make_user(author_email, UserRole.AUTHOR)
    editor = _make_user(editor_email, UserRole.EDITOR)
    instructor = _make_user(instructor_email, UserRole.INSTRUCTOR)
    try:
        created = client.post(
            "/api/v1/studio/articles",
            headers=_auth(author),
            json={
                "title": "How On-Chain Activity Can Reveal DeFi Market Trends",
                "excerpt": "A research note.",
                "category": "Research",
                "body": {
                    "version": 1,
                    "blocks": [
                        {"type": "paragraph", "text": "On-chain activity often leads price."},
                        {"type": "heading", "level": 2, "text": "What to watch"},
                        {
                            "type": "code",
                            "language": "sql",
                            "code": "SELECT blockchain, COUNT(*) FROM trades GROUP BY 1;",
                        },
                        {"type": "youtube", "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
                        {
                            "type": "table",
                            "headers": ["Metric", "Q1"],
                            "rows": [["Users", "120"]],
                        },
                        {
                            "type": "chart",
                            "chartType": "bar",
                            "title": "Active addresses",
                            "labels": ["Jan", "Feb"],
                            "values": [10, 20],
                            "source": "Author compilation",
                            "caption": "Figure 1 — Monthly active addresses",
                        },
                        {"type": "takeaways", "items": ["Volume is not the same as users."]},
                    ],
                },
            },
        )
        assert created.status_code == 201, created.text
        article_id = created.json()["id"]
        assert created.json()["status"] == "draft"
        assert created.json()["can_publish"] is False

        forbidden = client.post(
            f"/api/v1/studio/articles/{article_id}/publish",
            headers=_auth(author),
        )
        assert forbidden.status_code == 403

        instructor_list = client.get("/api/v1/studio/articles", headers=_auth(instructor))
        assert instructor_list.status_code == 403

        submitted = client.post(
            f"/api/v1/studio/articles/{article_id}/submit",
            headers=_auth(author),
        )
        assert submitted.status_code == 200
        assert submitted.json()["status"] == "pending_review"

        published = client.post(
            f"/api/v1/studio/articles/{article_id}/publish",
            headers=_auth(editor),
        )
        assert published.status_code == 200, published.text
        assert published.json()["status"] == "published"

        public = client.get("/api/v1/insights/how-on-chain-activity-can-reveal-defi-market-trends")
        assert public.status_code == 200
        types = [block["type"] for block in public.json()["body"]["blocks"]]
        assert "youtube" in types
        assert "chart" in types
        assert public.json()["body"]["blocks"][3]["videoId"] == "dQw4w9WgXcQ"
    finally:
        db = SessionLocal()
        try:
            db.query(Article).filter(Article.slug.like("how-on-chain-activity%")).delete()
            db.commit()
        finally:
            db.close()
        _cleanup_user(author_email)
        _cleanup_user(editor_email)
        _cleanup_user(instructor_email)


def test_rejects_script_and_unknown_embed():
    email = f"author-bad-{uuid.uuid4()}@example.com"
    _cleanup_user(email)
    author = _make_user(email, UserRole.AUTHOR)
    try:
        response = client.post(
            "/api/v1/studio/articles",
            headers=_auth(author),
            json={
                "title": "Unsafe",
                "body": {"version": 1, "blocks": [{"type": "paragraph", "text": "<script>alert(1)</script>"}]},
            },
        )
        assert response.status_code == 400
        iframe = client.post(
            "/api/v1/studio/articles",
            headers=_auth(author),
            json={
                "title": "Unsafe iframe",
                "body": {"version": 1, "blocks": [{"type": "embed", "html": "<iframe src='https://evil'></iframe>"}]},
            },
        )
        assert iframe.status_code == 400
    finally:
        _cleanup_user(email)


def test_guest_can_subscribe_without_signin(monkeypatch):
    monkeypatch.setattr(EmailService, "add_subscriber", lambda self, email: True)
    response = client.post("/api/v1/insights/subscribe", json={"email": "reader@example.com"})
    assert response.status_code == 200
    assert "list" in response.json()["message"].lower()


def test_subscribe_unavailable_when_provider_fails(monkeypatch):
    monkeypatch.setattr(EmailService, "add_subscriber", lambda self, email: False)
    response = client.post("/api/v1/insights/subscribe", json={"email": "reader@example.com"})
    assert response.status_code == 503


def test_subscribe_rejects_invalid_email():
    response = client.post("/api/v1/insights/subscribe", json={"email": "not-an-email"})
    assert response.status_code == 422


def test_first_publish_emails_list_once(monkeypatch):
    calls: list[dict] = []

    def _send(self, **kwargs):
        calls.append(kwargs)
        return True

    monkeypatch.setattr(EmailService, "send_insight_newsletter", _send)
    editor_email = f"editor-nl-{uuid.uuid4()}@example.com"
    _cleanup_user(editor_email)
    editor = _make_user(editor_email, UserRole.EDITOR)
    slug_prefix = f"newsletter-send-{uuid.uuid4().hex[:8]}"
    try:
        created = client.post(
            "/api/v1/studio/articles",
            headers=_auth(editor),
            json={
                "title": slug_prefix.replace("-", " ").title(),
                "excerpt": "A first issue for the list.",
                "category": "Research",
                "body": {"version": 1, "blocks": [{"type": "paragraph", "text": "First issue."}]},
            },
        )
        assert created.status_code == 201, created.text
        article_id = created.json()["id"]
        slug = created.json()["slug"]
        published = client.post(
            f"/api/v1/studio/articles/{article_id}/publish",
            headers=_auth(editor),
        )
        assert published.status_code == 200, published.text
        assert len(calls) == 1
        assert calls[0]["slug"] == slug
        assert calls[0]["title"]
        again = client.post(
            f"/api/v1/studio/articles/{article_id}/publish",
            headers=_auth(editor),
        )
        assert again.status_code == 200
        unpublished = client.post(
            f"/api/v1/studio/articles/{article_id}/unpublish",
            headers=_auth(editor),
        )
        assert unpublished.status_code == 200
        republished = client.post(
            f"/api/v1/studio/articles/{article_id}/publish",
            headers=_auth(editor),
        )
        assert republished.status_code == 200
        assert len(calls) == 1
        db = SessionLocal()
        try:
            article = db.query(Article).filter(Article.id == article_id).one()
            assert article.newsletter_sent_at is not None
        finally:
            db.close()
    finally:
        db = SessionLocal()
        try:
            db.query(Article).filter(Article.slug.like(f"{slug_prefix}%")).delete()
            db.commit()
        finally:
            db.close()
        _cleanup_user(editor_email)


def test_seeded_articles_are_marked_already_sent():
    db = SessionLocal()
    try:
        seed_insights_articles(db)
        db.commit()
        article = (
            db.query(Article)
            .filter(Article.slug == "what-is-on-chain-analysis-beginners-guide")
            .one()
        )
        assert article.status == ArticleStatus.PUBLISHED
        assert article.newsletter_sent_at is not None
    finally:
        db.close()
