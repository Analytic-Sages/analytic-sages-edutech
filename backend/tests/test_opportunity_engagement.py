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
from app.models.opportunity import CareerPath, Opportunity
from app.models.user import User
from app.services.opportunity_review_assist import OpportunityReviewAssistService
from app.services.seed_opportunities import seed_opportunity_taxonomy

client = TestClient(app)


def _token_for(user: User) -> str:
    return SecurityService(get_settings()).create_access_token(user_id=str(user.id), role=user.role.value)


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


def _path_id() -> str:
    db = SessionLocal()
    try:
        seed_opportunity_taxonomy(db)
        db.commit()
        path = db.scalar(select(CareerPath).where(CareerPath.slug == "onchain-data-analytics"))
        assert path is not None
        return str(path.id)
    finally:
        db.close()


def test_student_can_save_and_list_published_opportunity():
    slug = f"save-opp-{uuid.uuid4().hex[:8]}"
    _cleanup_slug(slug)
    admin_email = f"admin-save-{uuid.uuid4()}@example.com"
    student_email = f"student-save-{uuid.uuid4()}@example.com"
    admin = _make_user(admin_email, UserRole.ADMIN)
    student = _make_user(student_email, UserRole.STUDENT)
    try:
        created = client.post(
            "/api/v1/admin/opportunities",
            headers=_auth(admin),
            json={
                "slug": slug,
                "title": "Onchain Data Analyst",
                "organization_name": "Example Analytics",
                "description": "Analyze public blockchain data.",
                "requirements": "SQL",
                "opportunity_type": "job",
                "workplace_type": "remote",
                "experience_level": "mid",
                "location": "Remote",
                "application_url": "https://example.com/jobs/onchain",
                "career_path_ids": [_path_id()],
            },
        )
        assert created.status_code == 201, created.text
        opportunity_id = created.json()["id"]
        guest_save = client.post(f"/api/v1/me/opportunities/{opportunity_id}/save")
        assert guest_save.status_code == 401
        unpublished = client.post(f"/api/v1/me/opportunities/{opportunity_id}/save", headers=_auth(student))
        assert unpublished.status_code == 404
        published = client.post(f"/api/v1/admin/opportunities/{opportunity_id}/publish", headers=_auth(admin), json={})
        assert published.status_code == 200, published.text
        saved = client.post(f"/api/v1/me/opportunities/{opportunity_id}/save", headers=_auth(student))
        assert saved.status_code == 200, saved.text
        listed = client.get("/api/v1/me/opportunities", headers=_auth(student))
        assert listed.status_code == 200
        assert any(item["opportunity"]["slug"] == slug for item in listed.json()["items"])
        public = client.get("/api/v1/opportunities", headers=_auth(student))
        match = next(item for item in public.json()["items"] if item["slug"] == slug)
        assert match["saved"] is True
        interests = client.put(
            "/api/v1/me/opportunity-interests",
            headers=_auth(student),
            json={"career_path_ids": [_path_id()]},
        )
        assert interests.status_code == 200, interests.text
        matched = client.get("/api/v1/opportunities", headers=_auth(student), params={"sort": "matched"})
        assert matched.status_code == 200
        assert any(item["slug"] == slug for item in matched.json()["items"])
        applied = client.post(f"/api/v1/me/opportunities/{opportunity_id}/applied", headers=_auth(student))
        assert applied.json()["state"] == "applied"
        client.delete(f"/api/v1/me/opportunities/{opportunity_id}/save", headers=_auth(student))
        empty = client.get("/api/v1/me/opportunities", headers=_auth(student))
        assert all(item["opportunity"]["slug"] != slug for item in empty.json()["items"])
        announce = client.post(f"/api/v1/admin/opportunities/{opportunity_id}/announce", headers=_auth(admin))
        assert announce.status_code == 200
        assert announce.json()["status"] == "skipped"
        with patch.object(OpportunityReviewAssistService, "configured", new_callable=PropertyMock) as configured:
            configured.return_value = False
            assist = client.post(f"/api/v1/admin/opportunities/{opportunity_id}/review-assist", headers=_auth(admin))
        assert assist.status_code == 503
    finally:
        _cleanup_slug(slug)
        _cleanup_user(admin_email)
        _cleanup_user(student_email)
