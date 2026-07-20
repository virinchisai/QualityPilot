import pytest

from qualitypilot.config import Settings

pytestmark = pytest.mark.security


def test_production_rejects_defect_flags():
    with pytest.raises(ValueError, match="forbidden"):
        Settings(environment="production", jwt_secret="x" * 32, defect_break_admin_auth=True)


def test_password_policy_reports_all_required_classes(client):
    response = client.post(
        "/api/register", json={"email": "weak@example.com", "password": "alllowercase"}
    )
    messages = response.json()["detail"]["password"]
    assert "contain an uppercase letter" in messages
    assert "contain a number" in messages
    assert "contain a symbol" in messages
