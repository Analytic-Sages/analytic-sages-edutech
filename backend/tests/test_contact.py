from fastapi.testclient import TestClient

from app.main import app
from app.services.email import EmailService

client = TestClient(app)

VALID_PAYLOAD = {
    "name": "Ada Lovelace",
    "email": "ada@example.com",
    "subject": "Cohort 9 question",
    "message": "I would like to know when the next live cohort starts.",
}


def test_contact_accepts_valid_message(monkeypatch):
    monkeypatch.setattr(
        EmailService,
        "send_contact_message",
        lambda self, **_kwargs: True,
    )
    response = client.post("/api/v1/contact", json=VALID_PAYLOAD)
    assert response.status_code == 200
    assert "message" in response.json()


def test_contact_returns_unavailable_when_send_fails(monkeypatch):
    monkeypatch.setattr(
        EmailService,
        "send_contact_message",
        lambda self, **_kwargs: False,
    )
    response = client.post("/api/v1/contact", json=VALID_PAYLOAD)
    assert response.status_code == 503


def test_contact_rejects_short_message():
    response = client.post(
        "/api/v1/contact",
        json={**VALID_PAYLOAD, "message": "Hi"},
    )
    assert response.status_code == 422


def test_contact_rejects_invalid_email():
    response = client.post(
        "/api/v1/contact",
        json={**VALID_PAYLOAD, "email": "not-an-email"},
    )
    assert response.status_code == 422
