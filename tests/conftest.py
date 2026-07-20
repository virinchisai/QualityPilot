"""Isolated application fixtures."""

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_DB = Path(__file__).parent / "qualitypilot-test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["JWT_SECRET"] = "test-secret-that-is-long-enough-for-qualitypilot"
os.environ["LOGIN_RATE_LIMIT"] = "100"

from app.demo_app.main import app  # noqa: E402
from qualitypilot.database import Base, engine  # noqa: E402


@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def registered_user(client):
    payload = {
        "email": "user@example.com",
        "password": "StrongPass!123",
        "display_name": "Standard User",
    }
    assert client.post("/api/register", json=payload).status_code == 201
    return payload


@pytest.fixture
def tokens(client, registered_user):
    response = client.post("/api/login", json=registered_user)
    assert response.status_code == 200
    return response.json()
