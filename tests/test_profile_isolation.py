"""Verify profile data is isolated per authenticated user."""
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.database import Base, get_db
from routes.auth import router as auth_router
from routes.profile import router as profile_router

# Register models on Base.metadata
from models import conversation, memory, profile, report, user  # noqa: F401


def _register(client: TestClient, name: str, email: str, password: str) -> None:
    response = client.post(
        "/auth/register",
        json={"name": name, "email": email, "password": password},
    )
    assert response.status_code == 200, response.text


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post(
        "/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture()
def client():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(profile_router)
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client


def test_user_b_cannot_see_user_a_profile(client: TestClient):
    suffix = uuid.uuid4().hex[:8]
    password = "secret123"

    _register(client, "User A", f"user-a-{suffix}@example.com", password)
    token_a = _login(client, f"user-a-{suffix}@example.com", password)

    marker = "USER_A_MARKER"
    create_response = client.post(
        "/profile/create",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "general": {"age": 42, "location": marker},
            "career": {"target_role": marker},
        },
    )
    assert create_response.status_code == 200, create_response.text

    profile_a = client.get("/profile", headers={"Authorization": f"Bearer {token_a}"})
    assert profile_a.status_code == 200
    assert profile_a.json()["general"]["location"] == marker

    _register(client, "User B", f"user-b-{suffix}@example.com", password)
    token_b = _login(client, f"user-b-{suffix}@example.com", password)

    profile_b = client.get("/profile", headers={"Authorization": f"Bearer {token_b}"})
    assert profile_b.status_code == 200
    body_b = profile_b.json()
    assert body_b["general"] is None
    assert body_b["career"] is None
    assert body_b["health"] is None
    assert body_b["finance"] is None

    profile_a_again = client.get("/profile", headers={"Authorization": f"Bearer {token_a}"})
    assert profile_a_again.status_code == 200
    assert profile_a_again.json()["general"]["location"] == marker
