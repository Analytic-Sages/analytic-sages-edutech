from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_openapi_available_in_development():
    response = client.get("/openapi.json")
    assert response.status_code == 200


def test_health_endpoint_shape():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert "status" in body
    assert "database" in body
    assert "redis" in body


def test_admin_overview_requires_auth():
    response = client.get("/api/v1/admin/overview")
    assert response.status_code == 401


def test_admin_invite_instructor_requires_auth():
    response = client.post(
        "/api/v1/admin/instructors",
        json={"email": "teacher@example.com", "full_name": "Teacher"},
    )
    assert response.status_code == 401
