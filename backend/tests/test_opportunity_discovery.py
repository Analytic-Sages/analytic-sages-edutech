from __future__ import annotations

import uuid
from unittest.mock import PropertyMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.core.roles import UserRole
from app.core.security import SecurityService
from app.db.session import SessionLocal
from app.main import app
from app.models.opportunity import Opportunity
from app.models.user import User
from app.services.opportunity_discovery import OpportunityDiscoveryService
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


def _seed() -> None:
    db = SessionLocal()
    try:
        seed_opportunity_taxonomy(db)
        db.commit()
    finally:
        db.close()


def test_discover_requires_auth():
    assert client.post("/api/v1/admin/opportunities/discover", json={}).status_code == 401


def test_discover_requires_llm_key():
    _seed()
    email = f"admin-disc-{uuid.uuid4()}@example.com"
    admin = _make_user(email, UserRole.ADMIN)
    try:
        with patch.object(OpportunityDiscoveryService, "configured", new_callable=PropertyMock) as configured:
            configured.return_value = False
            response = client.post(
                "/api/v1/admin/opportunities/discover",
                headers=_auth(admin),
                json={"types": ["hackathon"]},
            )
        assert response.status_code == 503
    finally:
        _cleanup_user(email)


def test_discover_and_import_stay_unpublished():
    _seed()
    email = f"admin-disc-imp-{uuid.uuid4()}@example.com"
    admin = _make_user(email, UserRole.ADMIN)
    suffix = uuid.uuid4().hex[:8]
    apply_url = f"https://ethglobal.com/events/prague-{suffix}"
    payload = {
        "candidates": [
            {
                "title": "ETHGlobal Prague Hackathon",
                "organization_name": "ETHGlobal",
                "opportunity_type": "hackathon",
                "application_url": apply_url,
                "description": "Build onchain analytics dashboards at ETHGlobal.",
                "why_relevant": "Onchain data analytics",
            },
            {
                "title": "Aggregator listing",
                "organization_name": "Web3 Career",
                "opportunity_type": "internship",
                "application_url": "https://web3.career/jobs/sql-intern",
                "description": "SQL internship",
                "why_relevant": "SQL",
            },
        ]
    }
    openai_rows = payload["candidates"]
    try:
        with patch.object(OpportunityDiscoveryService, "configured", new_callable=PropertyMock) as configured:
            configured.return_value = True
            with patch.object(OpportunityDiscoveryService, "_complete", return_value=(openai_rows, True, "openai")):
                found = client.post(
                    "/api/v1/admin/opportunities/discover",
                    headers=_auth(admin),
                    json={"types": ["hackathon", "internship"]},
                )
        assert found.status_code == 200, found.text
        assert found.json()["provider"] == "openai"
        urls = {row["application_url"] for row in found.json()["candidates"]}
        assert apply_url in urls
        assert all("web3.career" not in row["application_url"] for row in found.json()["candidates"])
        imported = client.post(
            "/api/v1/admin/opportunities/discover/import",
            headers=_auth(admin),
            json={"candidates": [row for row in found.json()["candidates"] if row["application_url"] == apply_url]},
        )
        assert imported.status_code == 200, imported.text
        assert imported.json()["published"] is False
        assert imported.json()["imported"] == 1
        opportunity_id = imported.json()["opportunity_ids"][0]
        detail = client.get(f"/api/v1/admin/opportunities/{opportunity_id}", headers=_auth(admin))
        assert detail.json()["status"] == "draft"
        assert detail.json()["opportunity_type"] == "hackathon"
        assert detail.json()["trust_status"] == "review_required"
        public = client.get("/api/v1/opportunities")
        assert all(item["id"] != opportunity_id for item in public.json()["items"])
        slug = detail.json()["slug"]
        _cleanup_slug(slug)
    finally:
        _cleanup_user(email)


def test_reclassify_draft_intern_false_positive():
    _seed()
    email = f"admin-reclass-{uuid.uuid4()}@example.com"
    admin = _make_user(email, UserRole.ADMIN)
    slug = f"reclass-{uuid.uuid4().hex[:8]}"
    try:
        created = client.post(
            "/api/v1/admin/opportunities",
            headers=_auth(admin),
            json={
                "slug": slug,
                "title": "Senior Software Engineer",
                "organization_name": "Example",
                "description": "Build internal analytics platforms with SQL and Python.",
                "opportunity_type": "internship",
                "workplace_type": "remote",
                "application_url": f"https://example.com/jobs/{slug}",
            },
        )
        assert created.status_code == 201, created.text
        result = client.post("/api/v1/admin/opportunities/reclassify-types", headers=_auth(admin))
        assert result.status_code == 200
        assert result.json()["updated"] >= 1
        detail = client.get(f"/api/v1/admin/opportunities/{created.json()['id']}", headers=_auth(admin))
        assert detail.json()["opportunity_type"] == "job"
    finally:
        _cleanup_slug(slug)
        _cleanup_user(email)


def test_discover_falls_back_to_gemini_when_openai_fails():
    _seed()
    email = f"admin-disc-gem-{uuid.uuid4()}@example.com"
    admin = _make_user(email, UserRole.ADMIN)
    suffix = uuid.uuid4().hex[:8]
    apply_url = f"https://ethglobal.com/events/lisbon-{suffix}"
    rows = [
        {
            "title": "ETHGlobal Lisbon Hackathon",
            "organization_name": "ETHGlobal",
            "opportunity_type": "hackathon",
            "application_url": apply_url,
            "description": "Build onchain analytics at ETHGlobal.",
            "why_relevant": "Onchain data analytics",
        }
    ]
    try:
        with patch.object(OpportunityDiscoveryService, "configured", new_callable=PropertyMock) as configured:
            configured.return_value = True
            with patch.object(OpportunityDiscoveryService, "_complete", return_value=(rows, True, "gemini")):
                found = client.post(
                    "/api/v1/admin/opportunities/discover",
                    headers=_auth(admin),
                    json={"types": ["hackathon"]},
                )
        assert found.status_code == 200, found.text
        assert found.json()["provider"] == "gemini"
        assert found.json()["candidates"][0]["application_url"] == apply_url
        assert "Gemini" in (found.json()["notes"] or "")
    finally:
        _cleanup_user(email)
