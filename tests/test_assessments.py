"""Integration tests for authenticated assessment creation endpoints."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import JSON, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from core.database import Base, get_db
from core.security import create_access_token, hash_password
from models.profile import CareerProfile, FinanceProfile, HealthProfile, UserProfile
from models.progress import AssessmentEvent
from models.user import User
from routes.assessments import router as assessments_router
from tools.calculators import _extract_skills_from_career_knowledge

# Register every model, including AssessmentEvent, with Base.metadata.
from models import conversation, memory, profile, progress, report, user  # noqa: F401,E402


@pytest.fixture()
def assessment_context():
    skills_column = CareerProfile.__table__.c.current_skills
    original_skills_type = skills_column.type
    skills_column.type = JSON()
    engine = None
    app = FastAPI()

    try:
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=engine)
        session_factory = sessionmaker(bind=engine, expire_on_commit=False)

        def override_get_db():
            db = session_factory()
            try:
                yield db
            finally:
                db.close()

        app.include_router(assessments_router)
        app.dependency_overrides[get_db] = override_get_db

        with TestClient(app) as client:
            yield client, session_factory
    finally:
        app.dependency_overrides.clear()
        if engine is not None:
            Base.metadata.drop_all(bind=engine)
            engine.dispose()
        skills_column.type = original_skills_type


def _create_user(db: Session, name: str | None = None) -> User:
    suffix = uuid.uuid4().hex[:8]
    user = User(
        name=name or f"Assessment User {suffix}",
        email=f"assessment-{suffix}@example.com",
        password_hash=hash_password("secret123"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _token(user: User) -> str:
    return create_access_token({"sub": user.id, "email": user.email})


def _headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token(user)}"}


def _career_profile(db: Session, user: User, **overrides) -> CareerProfile:
    values = {
        "target_role": "data scientist",
        "current_skills": ["python", "sql"],
    }
    values.update(overrides)
    profile = CareerProfile(user_id=user.id, **values)
    db.add(profile)
    db.commit()
    return profile


def _health_profiles(
    db: Session,
    user: User,
    *,
    age=30,
    height_cm=170,
    weight_kg=65,
    include_health=True,
) -> None:
    db.add(UserProfile(
        user_id=user.id,
        age=age,
        height_cm=height_cm,
        weight_kg=weight_kg,
    ))
    if include_health:
        db.add(HealthProfile(user_id=user.id, sleep_quality=8))
    db.commit()


def _finance_profile(db: Session, user: User, income=40000, expenses=30000) -> None:
    db.add(FinanceProfile(
        user_id=user.id,
        monthly_income=income,
        monthly_expenses=expenses,
    ))
    db.commit()


def _event_count(session_factory) -> int:
    with session_factory() as db:
        return db.query(AssessmentEvent).count()


def _assessment_event(db: Session, user: User, *, created_at: datetime, value: float, target_role: str | None = None) -> AssessmentEvent:
    event = AssessmentEvent(
        user_id=user.id,
        domain="career",
        assessment_type="target_role_skill_match",
        value=value,
        value_kind="score",
        target_role=target_role or "data scientist",
        created_at=created_at,
        source="skill_gap_analyzer",
        calculation_version="skill-gap-v1",
        details={"sensitive": "not returned"},
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def test_career_assessment_success_and_persistence(assessment_context):
    client, session_factory = assessment_context
    with session_factory() as db:
        user = _create_user(db)
        _career_profile(db, user)

    response = client.post("/assessments/career", headers=_headers(user))

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["assessment_id"]
    assert body["domain"] == "career"
    assert body["assessment_type"] == "target_role_skill_match"
    assert body["value_kind"] == "score"
    assert 0 <= body["value"] <= 100
    assert body["target_role"] == "data scientist"
    assert body["source"] == "skill_gap_analyzer"
    assert body["calculation_version"] == "skill-gap-v1"
    assert body["details"]["matched_skills"] == ["python", "sql"]
    assert body["details"]["missing_skills"] == [
        "machine learning",
        "statistics",
        "data visualization",
    ]
    assert body["details"]["total_required_skills"] == 5

    with session_factory() as db:
        event = db.query(AssessmentEvent).one()
        assert event.id == body["assessment_id"]
        assert event.user_id == user.id
        assert event.domain == "career"
        assert event.assessment_type == "target_role_skill_match"
        assert event.target_role == "data scientist"


@pytest.mark.parametrize(
    "profile_overrides",
    [
        {"target_role": None},
        {"current_skills": []},
        {"current_skills": None},
    ],
)
def test_career_assessment_incomplete_profile_returns_400(
    assessment_context, profile_overrides
):
    client, session_factory = assessment_context
    with session_factory() as db:
        user = _create_user(db)
        _career_profile(db, user, **profile_overrides)

    response = client.post("/assessments/career", headers=_headers(user))

    assert response.status_code == 400, response.text
    assert _event_count(session_factory) == 0


def test_career_assessment_supports_non_hardcoded_target_role(monkeypatch, assessment_context):
    client, session_factory = assessment_context
    with session_factory() as db:
        user = _create_user(db, "Dynamic Role User")
        _career_profile(db, user, target_role="platform engineer", current_skills=["python", "sql", "aws"])

    monkeypatch.setattr(
        "rag.retriever.retrieve_as_context",
        lambda *args, **kwargs: "Platform engineering requires Python, SQL, cloud infrastructure, CI/CD, and Kubernetes.",
    )
    monkeypatch.setattr(
        "core.llm_client.call_llm",
        lambda *args, **kwargs: {
            "required_skills": ["python", "sql", "ci/cd", "kubernetes", "aws"],
            "confidence": 0.9,
        },
    )

    response = client.post("/assessments/career", headers=_headers(user))

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["target_role"] == "platform engineer"
    assert body["details"]["matched_skills"] == ["python", "sql"]
    assert body["details"]["missing_skills"] == ["ci/cd", "kubernetes"]
    assert body["details"]["total_required_skills"] == 4


@pytest.mark.parametrize(
    ("knowledge", "expected"),
    [
        (
            "Essential Skills\n1. Python\n2. SQL\n3. Machine learning",
            ["python", "sql", "machine learning"],
        ),
        (
            "The most in-demand skills are: 1. Python programming ... 2. SQL ... 3. Machine learning ... 4. Statistics and probability ... 5. Data visualization ...",
            ["python", "sql", "machine learning", "statistics", "data visualization"],
        ),
        (
            "Essential Skills\n1. Python\n2. SQL ... 3. Machine learning\n4. Statistics",
            ["python", "sql", "machine learning", "statistics"],
        ),
        (
            "Essential Skills: 1. Python programming 2. SQL 3. Python development 4. Kubernetes",
            ["python", "sql", "kubernetes"],
        ),
    ],
)
def test_extracts_numbered_skills_from_rag_formats(knowledge, expected):
    assert _extract_skills_from_career_knowledge(knowledge, "product manager") == expected


def test_career_assessment_uses_authenticated_user_profile(assessment_context):
    client, session_factory = assessment_context
    with session_factory() as db:
        user_a = _create_user(db, "User A")
        _career_profile(db, user_a, current_skills=["python"])
        user_b = _create_user(db, "User B")
        _career_profile(db, user_b, current_skills=["python", "sql", "machine learning"])

    response_a = client.post("/assessments/career", headers=_headers(user_a))
    response_b = client.post("/assessments/career", headers=_headers(user_b))

    assert response_a.status_code == 200, response_a.text
    assert response_b.status_code == 200, response_b.text
    assert response_a.json()["value"] != response_b.json()["value"]

    with session_factory() as db:
        events = db.query(AssessmentEvent).order_by(AssessmentEvent.created_at).all()
        assert {event.user_id for event in events} == {user_a.id, user_b.id}



def test_health_assessment_success_hides_raw_inputs(assessment_context):
    client, session_factory = assessment_context
    with session_factory() as db:
        user = _create_user(db)
        _health_profiles(db, user)

    payload = {
        "sleep_quality": 8,
        "stress_level": 3,
        "mood_score": 7,
        "active_days_per_week": 4,
    }
    response = client.post("/assessments/health", headers=_headers(user), json=payload)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["assessment_id"]
    assert body["domain"] == "health"
    assert body["assessment_type"] == "fitness"
    assert body["value_kind"] == "score"
    assert 0 <= body["value"] <= 100
    assert body["source"] == "fitness_score"
    assert body["calculation_version"] == "fitness-score-v1"
    assert body["details"]["bmi"]
    assert body["details"]["component_scores"]
    assert not {"sleep_quality", "stress_level", "mood_score", "active_days_per_week"} & body["details"].keys()
    assert not {"age", "height_cm", "weight_kg"} & body["details"].keys()

    with session_factory() as db:
        event = db.query(AssessmentEvent).one()
        assert event.user_id == user.id
        assert not {"sleep_quality", "stress_level", "mood_score", "active_days_per_week"} & event.details.keys()


@pytest.mark.parametrize("missing_field", [
    "sleep_quality",
    "stress_level",
    "mood_score",
    "active_days_per_week",
])
def test_health_assessment_missing_input_returns_400(assessment_context, missing_field):
    client, session_factory = assessment_context
    with session_factory() as db:
        user = _create_user(db)
        _health_profiles(db, user)

    payload = {
        "sleep_quality": 8,
        "stress_level": 3,
        "mood_score": 7,
        "active_days_per_week": 4,
    }
    payload.pop(missing_field)
    response = client.post("/assessments/health", headers=_headers(user), json=payload)

    assert response.status_code == 400, response.text
    assert _event_count(session_factory) == 0


@pytest.mark.parametrize("field,value", [
    ("sleep_quality", 0),
    ("sleep_quality", 11),
    ("stress_level", 0),
    ("stress_level", 11),
    ("mood_score", 0),
    ("mood_score", 11),
    ("active_days_per_week", -1),
    ("active_days_per_week", 8),
])
def test_health_assessment_invalid_range_returns_400(assessment_context, field, value):
    client, session_factory = assessment_context
    with session_factory() as db:
        user = _create_user(db)
        _health_profiles(db, user)

    payload = {
        "sleep_quality": 8,
        "stress_level": 3,
        "mood_score": 7,
        "active_days_per_week": 4,
    }
    payload[field] = value
    response = client.post("/assessments/health", headers=_headers(user), json=payload)

    assert response.status_code == 400, response.text
    assert _event_count(session_factory) == 0


def test_health_assessment_rejects_undeclared_input(assessment_context):
    client, session_factory = assessment_context
    with session_factory() as db:
        user = _create_user(db)
        _health_profiles(db, user)

    response = client.post(
        "/assessments/health",
        headers=_headers(user),
        json={
            "sleep_quality": 8,
            "stress_level": 3,
            "mood_score": 7,
            "active_days_per_week": 4,
            "age": 30,
        },
    )

    assert response.status_code == 422, response.text
    assert _event_count(session_factory) == 0


@pytest.mark.parametrize("missing_field", ["age", "height_cm", "weight_kg"])
def test_health_assessment_missing_stored_profile_data_returns_400(
    assessment_context, missing_field
):
    client, session_factory = assessment_context
    with session_factory() as db:
        user = _create_user(db)
        values = {"age": 30, "height_cm": 170, "weight_kg": 65}
        values[missing_field] = None
        _health_profiles(db, user, **values)

    response = client.post(
        "/assessments/health",
        headers=_headers(user),
        json={
            "sleep_quality": 8,
            "stress_level": 3,
            "mood_score": 7,
            "active_days_per_week": 4,
        },
    )

    assert response.status_code == 400, response.text
    assert _event_count(session_factory) == 0


def test_health_assessment_requires_health_profile(assessment_context):
    client, session_factory = assessment_context
    with session_factory() as db:
        user = _create_user(db)
        _health_profiles(db, user, include_health=False)

    response = client.post(
        "/assessments/health",
        headers=_headers(user),
        json={
            "sleep_quality": 8,
            "stress_level": 3,
            "mood_score": 7,
            "active_days_per_week": 4,
        },
    )

    assert response.status_code == 400, response.text
    assert _event_count(session_factory) == 0


def test_finance_assessment_success_and_persistence(assessment_context):
    client, session_factory = assessment_context
    with session_factory() as db:
        user = _create_user(db)
        _finance_profile(db, user, income=40000, expenses=30000)

    response = client.post("/assessments/finance", headers=_headers(user), json={})

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["assessment_id"]
    assert body["domain"] == "finance"
    assert body["assessment_type"] == "savings_rate"
    assert body["value_kind"] == "percentage"
    assert body["value"] == 25.0
    assert body["details"]["monthly_savings"] == 10000
    assert body["source"] == "calculate_savings"
    assert body["calculation_version"] == "savings-rate-v1"

    with session_factory() as db:
        event = db.query(AssessmentEvent).one()
        assert event.user_id == user.id
        assert event.value == 25.0


@pytest.mark.parametrize("profile_overrides", [
    {"income": None, "expenses": 30000},
    {"income": 40000, "expenses": None},
])
def test_finance_assessment_incomplete_profile_returns_400(
    assessment_context, profile_overrides
):
    client, session_factory = assessment_context
    with session_factory() as db:
        user = _create_user(db)
        _finance_profile(db, user, **profile_overrides)

    response = client.post("/assessments/finance", headers=_headers(user), json={})

    assert response.status_code == 400, response.text
    assert _event_count(session_factory) == 0


def test_finance_assessment_zero_expenses_is_valid(assessment_context):
    client, session_factory = assessment_context
    with session_factory() as db:
        user = _create_user(db)
        _finance_profile(db, user, income=40000, expenses=0)

    response = client.post("/assessments/finance", headers=_headers(user), json={})

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["details"]["monthly_savings"] == 40000
    assert body["value"] == 100.0


def test_finance_assessment_deficit_is_not_clamped(assessment_context):
    client, session_factory = assessment_context
    with session_factory() as db:
        user = _create_user(db)
        _finance_profile(db, user, income=30000, expenses=35000)

    response = client.post("/assessments/finance", headers=_headers(user), json={})

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["details"]["monthly_savings"] == -5000
    assert body["value"] == pytest.approx(-16.7, abs=0.01)


def test_finance_assessment_zero_income_returns_400(assessment_context):
    client, session_factory = assessment_context
    with session_factory() as db:
        user = _create_user(db)
        _finance_profile(db, user, income=0, expenses=0)

    response = client.post("/assessments/finance", headers=_headers(user), json={})

    assert response.status_code == 400, response.text
    assert _event_count(session_factory) == 0


def test_finance_assessment_isolated_by_authenticated_user(assessment_context):
    client, session_factory = assessment_context
    with session_factory() as db:
        user_a = _create_user(db, "Finance A")
        _finance_profile(db, user_a, income=40000, expenses=30000)
        user_b = _create_user(db, "Finance B")
        _finance_profile(db, user_b, income=30000, expenses=35000)

    response_a = client.post("/assessments/finance", headers=_headers(user_a), json={})
    response_b = client.post("/assessments/finance", headers=_headers(user_b), json={})

    assert response_a.status_code == 200, response_a.text
    assert response_b.status_code == 200, response_b.text
    assert response_a.json()["value"] == 25.0
    assert response_b.json()["value"] == pytest.approx(-16.7, abs=0.01)

    with session_factory() as db:
        events = db.query(AssessmentEvent).all()
        assert {event.user_id for event in events} == {user_a.id, user_b.id}


def test_assessment_history_returns_empty_for_user_without_events(assessment_context):
    client, session_factory = assessment_context
    with session_factory() as db:
        user = _create_user(db)

    response = client.get("/assessments/history", headers=_headers(user))

    assert response.status_code == 200, response.text
    assert response.json() == []


def test_assessment_history_returns_only_authenticated_users_events(assessment_context):
    client, session_factory = assessment_context
    now = datetime.now(timezone.utc)
    with session_factory() as db:
        user_a = _create_user(db, "History A")
        user_b = _create_user(db, "History B")
        event_a = _assessment_event(db, user_a, created_at=now, value=40)
        _assessment_event(db, user_b, created_at=now + timedelta(seconds=1), value=90)

    response = client.get("/assessments/history", headers=_headers(user_a))

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body) == 1
    assert body[0] == {
        "assessment_id": event_a.id,
        "domain": "career",
        "assessment_type": "target_role_skill_match",
        "value": 40.0,
        "value_kind": "score",
        "target_role": "data scientist",
        "assessed_at": event_a.created_at.isoformat().replace("+00:00", "Z"),
    }
    assert "details" not in body[0]
    assert "source" not in body[0]
    assert "calculation_version" not in body[0]
    assert "user_id" not in body[0]


def test_assessment_history_returns_events_newest_first(assessment_context):
    client, session_factory = assessment_context
    now = datetime.now(timezone.utc)
    with session_factory() as db:
        user = _create_user(db)
        older = _assessment_event(db, user, created_at=now, value=40)
        newer = _assessment_event(db, user, created_at=now + timedelta(days=1), value=60)

    response = client.get("/assessments/history", headers=_headers(user))

    assert response.status_code == 200, response.text
    assert [item["assessment_id"] for item in response.json()] == [newer.id, older.id]


def test_assessment_history_does_not_return_another_users_event(assessment_context):
    client, session_factory = assessment_context
    with session_factory() as db:
        user_a = _create_user(db, "Owner")
        user_b = _create_user(db, "Other")
        _assessment_event(db, user_a, created_at=datetime.now(timezone.utc), value=55)
        event_b = _assessment_event(db, user_b, created_at=datetime.now(timezone.utc), value=75)

    response = client.get("/assessments/history", headers=_headers(user_a))

    assert response.status_code == 200, response.text
    assert event_b.id not in {item["assessment_id"] for item in response.json()}
