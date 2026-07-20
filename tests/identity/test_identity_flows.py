from datetime import UTC, datetime, timedelta

import jwt
import pytest

from qualitypilot.config import get_settings
from qualitypilot.database import SessionLocal, User

pytestmark = pytest.mark.identity


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def test_access_token_has_valid_signature_and_claims(client, tokens):
    claims = jwt.decode(tokens["access_token"], get_settings().jwt_secret, algorithms=["HS256"])
    assert claims["type"] == "access"
    assert claims["role"] == "user"
    assert claims["sub"]


def test_refresh_rotates_and_old_token_is_rejected(client, tokens):
    refreshed = client.post("/api/token/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200
    assert refreshed.json()["refresh_token"] != tokens["refresh_token"]
    replay = client.post("/api/token/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert replay.status_code == 401


def test_logout_revokes_entire_refresh_family(client, tokens):
    rotated = client.post(
        "/api/token/refresh", json={"refresh_token": tokens["refresh_token"]}
    ).json()
    assert (
        client.post("/api/logout", json={"refresh_token": rotated["refresh_token"]}).status_code
        == 204
    )
    assert (
        client.post(
            "/api/token/refresh", json={"refresh_token": rotated["refresh_token"]}
        ).status_code
        == 401
    )


def test_expired_malformed_and_wrong_type_tokens_are_rejected(client, registered_user, tokens):
    secret = get_settings().jwt_secret
    expired = jwt.encode(
        {
            "sub": "1",
            "role": "user",
            "type": "access",
            "jti": "x",
            "exp": datetime.now(UTC) - timedelta(seconds=1),
        },
        secret,
        algorithm="HS256",
    )
    assert client.get("/api/me", headers=bearer(expired)).status_code == 401
    assert client.get("/api/me", headers=bearer("malformed.token")).status_code == 401
    assert client.get("/api/me", headers=bearer(tokens["refresh_token"])).status_code == 401


def test_rbac_denies_user_and_allows_admin(client, registered_user, tokens):
    assert client.get("/api/admin/audit", headers=bearer(tokens["access_token"])).status_code == 403
    with SessionLocal() as db:
        user = db.query(User).filter_by(email=registered_user["email"]).one()
        user.role = "admin"
        db.commit()
    admin_tokens = client.post("/api/login", json=registered_user).json()
    assert (
        client.get("/api/admin/audit", headers=bearer(admin_tokens["access_token"])).status_code
        == 200
    )
