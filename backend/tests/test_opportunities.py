from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.core.roles import UserRole
from app.core.security import SecurityService
from app.db.session import SessionLocal
from app.main import app
from app.models.opportunity import CareerPath, Opportunity, OpportunityStatus, Skill
from app.models.user import User
from app.services.seed_opportunities import seed_opportunity_taxonomy

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
        user = db.scalar(select(User).where(User.email == email))
        if user:
            db.delete(user)
            db.commit()
    finally:
        db.close()


def _cleanup_slug(slug: str) -> None:
    db = SessionLocal()
    try:
        row = db.scalar(select(Opportunity).where(Opportunity.slug == slug))
        if row:
            db.delete(row)
            db.commit()
    finally:
        db.close()


def _taxonomy():
    db = SessionLocal()
    try:
        seed_opportunity_taxonomy(db)
        db.commit()
        path = db.scalar(select(CareerPath).where(CareerPath.slug == "onchain-data-analytics"))
        skill = db.scalar(select(Skill).where(Skill.slug == "sql"))
        assert path and skill
        return str(path.id), str(skill.id)
    finally:
        db.close()


def _payload(**overrides):
    path_id, skill_id = _taxonomy()
    data = {
        "slug": f"test-opp-{uuid.uuid4().hex[:8]}",
        "title": "Onchain Data Analyst",
        "organization_name": "Analytic Sages Partners",
        "description": "Analyze public blockchain data for protocol research.",
        "requirements": "SQL and Python experience.",
        "opportunity_type": "job",
        "workplace_type": "remote",
        "experience_level": "mid",
        "location": "Remote",
        "application_url": "https://example.com/careers/onchain-analyst",
        "career_path_ids": [path_id],
        "skill_ids": [skill_id],
    }
    data.update(overrides)
    return data


def test_public_list_hides_drafts_and_returns_filters():
    slug = f"draft-hidden-{uuid.uuid4().hex[:8]}"
    _cleanup_slug(slug)
    admin_email = f"admin-opp-{uuid.uuid4()}@example.com"
    admin = _make_user(admin_email, UserRole.ADMIN)
    try:
        created = client.post("/api/v1/admin/opportunities", headers=_auth(admin), json=_payload(slug=slug))
        assert created.status_code == 201, created.text
        listed = client.get("/api/v1/opportunities")
        assert listed.status_code == 200
        assert all(item["slug"] != slug for item in listed.json()["items"])
        assert client.get(f"/api/v1/opportunities/{slug}").status_code == 404
        filters = client.get("/api/v1/opportunities/filters")
        assert filters.status_code == 200
        slugs = {item["slug"] for item in filters.json()["career_paths"]}
        assert "onchain-data-analytics" in slugs
    finally:
        _cleanup_slug(slug)
        _cleanup_user(admin_email)


def test_admin_publish_then_public_can_read():
    slug = f"published-opp-{uuid.uuid4().hex[:8]}"
    _cleanup_slug(slug)
    admin_email = f"admin-pub-{uuid.uuid4()}@example.com"
    admin = _make_user(admin_email, UserRole.ADMIN)
    try:
        created = client.post("/api/v1/admin/opportunities", headers=_auth(admin), json=_payload(slug=slug))
        assert created.status_code == 201, created.text
        opportunity_id = created.json()["id"]
        published = client.post(
            f"/api/v1/admin/opportunities/{opportunity_id}/publish",
            headers=_auth(admin),
            json={},
        )
        assert published.status_code == 200, published.text
        assert published.json()["status"] == "published"
        listed = client.get("/api/v1/opportunities")
        assert any(item["slug"] == slug for item in listed.json()["items"])
        detail = client.get(f"/api/v1/opportunities/{slug}")
        assert detail.status_code == 200
        body = detail.json()
        assert body["organization_name"] == "Analytic Sages Partners"
        assert "trust_score" not in body
        assert body["public_badge"] == "none"
        assert body["primary_career_path"]["slug"] == "onchain-data-analytics"
        assert body["application_domain"] == "example.com"
        assert body["closing_soon"] is False
    finally:
        _cleanup_slug(slug)
        _cleanup_user(admin_email)


def test_expired_deadline_is_hidden_and_cannot_publish_past_deadline():
    slug = f"expired-opp-{uuid.uuid4().hex[:8]}"
    _cleanup_slug(slug)
    admin_email = f"admin-exp-{uuid.uuid4()}@example.com"
    admin = _make_user(admin_email, UserRole.ADMIN)
    past = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    future = (datetime.now(UTC) + timedelta(days=14)).isoformat()
    try:
        created = client.post(
            "/api/v1/admin/opportunities",
            headers=_auth(admin),
            json=_payload(slug=slug, deadline=past),
        )
        assert created.status_code == 201, created.text
        opportunity_id = created.json()["id"]
        blocked = client.post(
            f"/api/v1/admin/opportunities/{opportunity_id}/publish",
            headers=_auth(admin),
            json={},
        )
        assert blocked.status_code == 400
        client.patch(
            f"/api/v1/admin/opportunities/{opportunity_id}",
            headers=_auth(admin),
            json={"deadline": future},
        )
        published = client.post(
            f"/api/v1/admin/opportunities/{opportunity_id}/publish",
            headers=_auth(admin),
            json={},
        )
        assert published.status_code == 200, published.text
        client.patch(
            f"/api/v1/admin/opportunities/{opportunity_id}",
            headers=_auth(admin),
            json={"deadline": past},
        )
        listed = client.get("/api/v1/opportunities")
        assert all(item["slug"] != slug for item in listed.json()["items"])
        assert client.get(f"/api/v1/opportunities/{slug}").status_code == 404
    finally:
        _cleanup_slug(slug)
        _cleanup_user(admin_email)


def test_non_admin_staff_cannot_manage_opportunities():
    author_email = f"author-opp-{uuid.uuid4()}@example.com"
    editor_email = f"editor-opp-{uuid.uuid4()}@example.com"
    ops_email = f"ops-opp-{uuid.uuid4()}@example.com"
    author = _make_user(author_email, UserRole.AUTHOR)
    editor = _make_user(editor_email, UserRole.EDITOR)
    ops = _make_user(ops_email, UserRole.OPERATIONS)
    forbidden_slug = f"forbidden-{uuid.uuid4().hex[:8]}"
    ops_slug = f"ops-allowed-{uuid.uuid4().hex[:8]}"
    try:
        assert client.post(
            "/api/v1/admin/opportunities",
            headers=_auth(author),
            json=_payload(slug=forbidden_slug),
        ).status_code == 403
        assert client.post(
            "/api/v1/admin/opportunities",
            headers=_auth(editor),
            json=_payload(slug=forbidden_slug),
        ).status_code == 403
        # Operations (and partnerships) may manage opportunities
        created = client.post(
            "/api/v1/admin/opportunities",
            headers=_auth(ops),
            json=_payload(slug=ops_slug),
        )
        assert created.status_code == 201
        assert client.get("/api/v1/admin/opportunities").status_code == 401
    finally:
        _cleanup_slug(ops_slug)
        _cleanup_user(author_email)
        _cleanup_user(editor_email)
        _cleanup_user(ops_email)


def test_rejects_html_and_unsafe_urls():
    admin_email = f"admin-safe-{uuid.uuid4()}@example.com"
    admin = _make_user(admin_email, UserRole.ADMIN)
    try:
        html = client.post(
            "/api/v1/admin/opportunities",
            headers=_auth(admin),
            json=_payload(description="<script>alert(1)</script>"),
        )
        assert html.status_code == 400
        local = client.post(
            "/api/v1/admin/opportunities",
            headers=_auth(admin),
            json=_payload(application_url="http://127.0.0.1/apply"),
        )
        assert local.status_code == 400
        reserved = client.post(
            "/api/v1/admin/opportunities",
            headers=_auth(admin),
            json=_payload(slug="jobs"),
        )
        assert reserved.status_code == 400
    finally:
        _cleanup_user(admin_email)


def test_reject_preserves_row_and_hides_from_public():
    slug = f"rejected-opp-{uuid.uuid4().hex[:8]}"
    _cleanup_slug(slug)
    admin_email = f"admin-rej-{uuid.uuid4()}@example.com"
    admin = _make_user(admin_email, UserRole.ADMIN)
    try:
        created = client.post("/api/v1/admin/opportunities", headers=_auth(admin), json=_payload(slug=slug))
        opportunity_id = created.json()["id"]
        client.post(f"/api/v1/admin/opportunities/{opportunity_id}/publish", headers=_auth(admin), json={})
        rejected = client.post(
            f"/api/v1/admin/opportunities/{opportunity_id}/reject",
            headers=_auth(admin),
            json={"notes": "Insufficient source evidence"},
        )
        assert rejected.status_code == 200
        assert rejected.json()["status"] == "rejected"
        listed = client.get("/api/v1/opportunities")
        assert all(item["slug"] != slug for item in listed.json()["items"])
        admin_row = client.get(f"/api/v1/admin/opportunities/{opportunity_id}", headers=_auth(admin))
        assert admin_row.status_code == 200
        assert admin_row.json()["slug"] == slug
    finally:
        _cleanup_slug(slug)
        _cleanup_user(admin_email)


def test_search_matches_description_and_skill():
    slug = f"search-opp-{uuid.uuid4().hex[:8]}"
    _cleanup_slug(slug)
    admin_email = f"admin-search-{uuid.uuid4()}@example.com"
    admin = _make_user(admin_email, UserRole.ADMIN)
    try:
        created = client.post(
            "/api/v1/admin/opportunities",
            headers=_auth(admin),
            json=_payload(slug=slug, title="Protocol researcher", description="Deep Dune dashboard work."),
        )
        opportunity_id = created.json()["id"]
        client.post(f"/api/v1/admin/opportunities/{opportunity_id}/publish", headers=_auth(admin), json={})
        by_skill = client.get("/api/v1/opportunities", params={"q": "SQL"})
        assert by_skill.status_code == 200
        assert any(item["slug"] == slug for item in by_skill.json()["items"])
        by_desc = client.get("/api/v1/opportunities", params={"q": "Dune dashboard"})
        assert any(item["slug"] == slug for item in by_desc.json()["items"])
    finally:
        _cleanup_slug(slug)
        _cleanup_user(admin_email)


def test_region_filter_and_closing_soon_sort():
    slug = f"region-opp-{uuid.uuid4().hex[:8]}"
    _cleanup_slug(slug)
    admin_email = f"admin-region-{uuid.uuid4()}@example.com"
    admin = _make_user(admin_email, UserRole.ADMIN)
    soon = (datetime.now(UTC) + timedelta(days=5)).isoformat()
    try:
        bad = client.post(
            "/api/v1/admin/opportunities",
            headers=_auth(admin),
            json=_payload(slug=slug, region="mars"),
        )
        assert bad.status_code == 422
        created = client.post(
            "/api/v1/admin/opportunities",
            headers=_auth(admin),
            json=_payload(slug=slug, region="africa", deadline=soon),
        )
        assert created.status_code == 201, created.text
        opportunity_id = created.json()["id"]
        client.post(f"/api/v1/admin/opportunities/{opportunity_id}/publish", headers=_auth(admin), json={})
        africa = client.get("/api/v1/opportunities", params={"region": "africa"})
        assert any(item["slug"] == slug for item in africa.json()["items"])
        europe = client.get("/api/v1/opportunities", params={"region": "europe"})
        assert all(item["slug"] != slug for item in europe.json()["items"])
        closing = client.get("/api/v1/opportunities", params={"sort": "closing_soon"})
        match = next(item for item in closing.json()["items"] if item["slug"] == slug)
        assert match["closing_soon"] is True
        filters = client.get("/api/v1/opportunities/filters")
        regions = {item["value"] for item in filters.json()["regions"]}
        assert "africa" in regions
        assert "nigeria" in regions
    finally:
        _cleanup_slug(slug)
        _cleanup_user(admin_email)


def test_public_hub_is_hidden_until_go_live(monkeypatch):
    monkeypatch.setattr(get_settings(), "opportunities_public", False)
    slug = f"private-hub-{uuid.uuid4().hex[:8]}"
    _cleanup_slug(slug)
    admin_email = f"admin-private-{uuid.uuid4()}@example.com"
    student_email = f"student-private-{uuid.uuid4()}@example.com"
    admin = _make_user(admin_email, UserRole.ADMIN)
    student = _make_user(student_email, UserRole.STUDENT)
    try:
        created = client.post("/api/v1/admin/opportunities", headers=_auth(admin), json=_payload(slug=slug))
        assert created.status_code == 201, created.text
        opportunity_id = created.json()["id"]
        published = client.post(
            f"/api/v1/admin/opportunities/{opportunity_id}/publish",
            headers=_auth(admin),
            json={},
        )
        assert published.status_code == 200, published.text
        assert client.get("/api/v1/opportunities").status_code == 404
        assert client.get("/api/v1/opportunities/filters").status_code == 404
        assert client.get(f"/api/v1/opportunities/{slug}").status_code == 404
        assert client.get("/api/v1/opportunities", headers=_auth(admin)).status_code == 404
        assert client.get("/api/v1/admin/opportunities", headers=_auth(admin)).status_code == 200
        assert client.get("/api/v1/me/opportunities", headers=_auth(student)).status_code == 404
        announce = client.post(
            f"/api/v1/admin/opportunities/{opportunity_id}/announce",
            headers=_auth(admin),
        )
        assert announce.status_code == 200
        assert announce.json()["status"] == "skipped"
        digest = client.post("/api/v1/admin/opportunities/digest", headers=_auth(admin))
        assert digest.status_code == 200
        assert digest.json()["status"] == "skipped"
    finally:
        _cleanup_slug(slug)
        _cleanup_user(admin_email)
        _cleanup_user(student_email)
