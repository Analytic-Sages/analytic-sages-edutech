from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.roles import UserRole
from app.core.security import SecurityService
from app.db.session import SessionLocal
from app.main import app
from app.models.course_card_placement import CourseCardPlacement
from app.models.user import User

client = TestClient(app)


def _auth_admin() -> dict[str, str]:
    db = SessionLocal()
    try:
        user = User(
            email=f"placement-admin-{uuid.uuid4().hex[:8]}@example.com",
            full_name="Placement Admin",
            role=UserRole.ADMIN,
            email_verified=True,
            is_active=True,
        )
        db.add(user)
        db.commit()
        token = SecurityService(get_settings()).create_access_token(
            user_id=str(user.id), role=user.role.value
        )
        return {"Authorization": f"Bearer {token}"}
    finally:
        db.close()


def test_admin_can_replace_order_and_visibility_for_multiple_cards():
    headers = _auth_admin()
    page = f"test-page-{uuid.uuid4().hex[:8]}"
    payload = {
        "page_key": page,
        "section_key": "sidebar",
        "placements": [
            {"page_key": page, "section_key": "sidebar", "card_key": "sql-excel", "position": 9, "visible": True},
            {"page_key": page, "section_key": "sidebar", "card_key": "blockchain-data-engineering", "position": 0, "visible": False},
        ],
    }
    response = client.put("/api/v1/admin/course-card-placements", headers=headers, json=payload)
    assert response.status_code == 200
    rows = response.json()
    assert [row["card_key"] for row in rows] == ["sql-excel", "blockchain-data-engineering"]
    assert [row["position"] for row in rows] == [0, 1]
    assert rows[1]["visible"] is False

    public = client.get(
        "/api/v1/course-card-placements",
        params={"page_key": page, "section_key": "sidebar"},
    )
    assert public.status_code == 200
    assert [row["card_key"] for row in public.json()] == [
        "sql-excel", "blockchain-data-engineering"
    ]
    assert public.json()[1]["visible"] is False

    db = SessionLocal()
    try:
        db.query(CourseCardPlacement).filter(CourseCardPlacement.page_key == page).delete()
        db.commit()
    finally:
        db.close()


def test_admin_placement_rejects_duplicate_card_keys():
    headers = _auth_admin()
    page = f"test-page-{uuid.uuid4().hex[:8]}"
    response = client.put(
        "/api/v1/admin/course-card-placements",
        headers=headers,
        json={
            "page_key": page,
            "section_key": "sidebar",
            "placements": [
                {"page_key": page, "section_key": "sidebar", "card_key": "sql-excel", "position": 0},
                {"page_key": page, "section_key": "sidebar", "card_key": "sql-excel", "position": 1},
            ],
        },
    )
    assert response.status_code == 422
