import pytest

from app.demo_app.main import app
from app.demo_app.rate_limit import login_limiter
from qualitypilot.config import Settings, get_settings

pytestmark = pytest.mark.security


def test_login_rate_limit_returns_retry_after(client):
    login_limiter.clear()
    limited = Settings(
        jwt_secret="rate-limit-test-secret-that-is-long-enough",
        login_rate_limit=2,
        login_rate_window_seconds=30,
    )
    app.dependency_overrides[get_settings] = lambda: limited
    try:
        payload = {"email": "rate-limit@example.com", "password": "invalid"}
        assert client.post("/api/login", json=payload).status_code == 401
        assert client.post("/api/login", json=payload).status_code == 401
        blocked = client.post("/api/login", json=payload)
        assert blocked.status_code == 429
        assert blocked.headers["retry-after"] == "30"
    finally:
        app.dependency_overrides.clear()
        login_limiter.clear()
