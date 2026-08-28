from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.core.roles import UserRole
from app.core.security import SecurityService
from app.db.session import SessionLocal
from app.main import app
from app.models.user import User

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


def test_admin_analytics_requires_auth():
    assert client.get("/api/v1/admin/analytics").status_code == 401


def test_admin_analytics_returns_live_shape():
    email = "analytics-admin@example.com"
    _cleanup_user(email)
    admin = _make_user(email, UserRole.ADMIN)
    try:
        response = client.get("/api/v1/admin/analytics", headers=_auth(admin))
        assert response.status_code == 200
        body = response.json()
        assert body["users_total"] >= 1
        assert body["users_verified"] >= 1
        assert len(body["signups_by_day"]) == 30
        assert len(body["enrollments_by_day"]) == 30
        assert all(point["value"] >= 0 for point in body["signups_by_day"])
        assert {row["name"] for row in body["roles"]} == {role.value for role in UserRole}
        assert "Watch time is not recorded." in body["untracked"]
        assert "enrollments_active" in body
        assert "published_opportunities" in body
    finally:
        _cleanup_user(email)


def test_admin_overview_returns_live_shape():
    email = "overview-admin@example.com"
    _cleanup_user(email)
    admin = _make_user(email, UserRole.ADMIN)
    try:
        response = client.get("/api/v1/admin/overview", headers=_auth(admin))
        assert response.status_code == 200
        body = response.json()
        assert "users_total" in body
        assert "recent_payments" in body
        allowed = {"mock", "paystack", "nowpayments"}
        assert all(row["provider"] in allowed for row in body["recent_payments"])
    finally:
        _cleanup_user(email)


def test_admin_analytics_forbids_operations():
    email = "analytics-ops@example.com"
    _cleanup_user(email)
    ops = _make_user(email, UserRole.OPERATIONS)
    try:
        assert client.get("/api/v1/admin/analytics", headers=_auth(ops)).status_code == 403
    finally:
        _cleanup_user(email)
