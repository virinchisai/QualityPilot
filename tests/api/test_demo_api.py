import pytest

pytestmark = pytest.mark.api


def test_health_and_openapi(client):
    assert client.get("/health").json()["status"] == "healthy"
    assert "/api/login" in client.get("/openapi.json").json()["paths"]


def test_registration_rejects_weak_and_duplicate_passwords(client, registered_user):
    weak = client.post("/api/register", json={"email": "weak@example.com", "password": "short"})
    assert weak.status_code == 422
    duplicate = client.post("/api/register", json=registered_user)
    assert duplicate.status_code == 409


def test_profile_requires_auth_and_persists_update(client, tokens):
    assert client.get("/api/me").status_code == 401
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    assert client.get("/api/me", headers=headers).status_code == 200
    update = client.patch("/api/me", headers=headers, json={"display_name": "Updated"})
    assert update.json()["display_name"] == "Updated"
    assert client.get("/api/me", headers=headers).json()["display_name"] == "Updated"


def test_invalid_payload_and_error_shape(client):
    assert client.post("/api/login", json={"email": "not-email"}).status_code == 422
    invalid = client.post("/api/login", json={"email": "none@example.com", "password": "x"})
    assert invalid.status_code == 401
    assert invalid.json()["detail"] == "invalid credentials"
