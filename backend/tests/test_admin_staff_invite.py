from __future__ import annotations

import uuid

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


def _make_user(email: str, role: UserRole, *, with_password: bool = True) -> User:
    db = SessionLocal()
    try:
        user = User(
            email=email,
            full_name=email.split("@")[0],
            role=role,
            email_verified=True,
            is_active=True,
            password_hash=(
                SecurityService(get_settings()).hash_password("Password123!") if with_password else None
            ),
        )
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


def test_promote_existing_student_to_operations():
    admin_email = f"admin-promote-{uuid.uuid4()}@example.com"
    student_email = f"student-promote-{uuid.uuid4()}@example.com"
    admin = _make_user(admin_email, UserRole.ADMIN)
    _make_user(student_email, UserRole.STUDENT)
    try:
        with client:
            app.dependency_overrides.clear()
            response = client.post(
                "/api/v1/admin/operations",
                headers=_auth(admin),
                json={"email": student_email, "full_name": "Ops Person"},
            )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["role"] == "operations"
        assert body["promoted"] is True
        assert "Promoted" in body["message"]

        db = SessionLocal()
        try:
            user = db.scalar(select(User).where(User.email == student_email))
            assert user is not None
            assert user.role == UserRole.OPERATIONS
            assert user.password_hash is not None
        finally:
            db.close()
    finally:
        _cleanup_user(student_email)
        _cleanup_user(admin_email)


def test_existing_operations_account_can_sign_in_conflict():
    admin_email = f"admin-ops-exist-{uuid.uuid4()}@example.com"
    ops_email = f"ops-exist-{uuid.uuid4()}@example.com"
    admin = _make_user(admin_email, UserRole.ADMIN)
    _make_user(ops_email, UserRole.OPERATIONS)
    try:
        response = client.post(
            "/api/v1/admin/operations",
            headers=_auth(admin),
            json={"email": ops_email},
        )
        assert response.status_code == 409
        assert "already has an account" in response.json()["detail"].lower()
    finally:
        _cleanup_user(ops_email)
        _cleanup_user(admin_email)


def test_change_staff_role_from_instructor_to_operations():
    admin_email = f"admin-role-chg-{uuid.uuid4()}@example.com"
    staff_email = f"staff-role-chg-{uuid.uuid4()}@example.com"
    admin = _make_user(admin_email, UserRole.ADMIN)
    _make_user(staff_email, UserRole.INSTRUCTOR)
    try:
        response = client.post(
            "/api/v1/admin/operations",
            headers=_auth(admin),
            json={"email": staff_email},
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["promoted"] is True
        assert body["role"] == "operations"
        db = SessionLocal()
        try:
            user = db.scalar(select(User).where(User.email == staff_email))
            assert user is not None
            assert user.role == UserRole.OPERATIONS
        finally:
            db.close()
    finally:
        _cleanup_user(staff_email)
        _cleanup_user(admin_email)
