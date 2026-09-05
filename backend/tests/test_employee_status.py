from fastapi.testclient import TestClient
from sqlmodel import Session

from app.db import get_session
from app.main import app


def make_client(db_session: Session) -> TestClient:
    app.dependency_overrides[get_session] = lambda: db_session
    client = TestClient(app)
    return client


def test_status_with_no_sessions_reports_no_completed_session(db_session: Session):
    client = make_client(db_session)

    response = client.get("/employee/status")

    assert response.status_code == 200
    body = response.json()
    assert body["has_completed_session"] is False
    assert body["last_completed_at"] is None
    assert body["last_session_id"] is None


def test_status_with_only_in_progress_session_reports_no_completed_session(db_session: Session):
    client = make_client(db_session)
    client.post("/sessions", json={"role_title": "Software Engineer"})

    response = client.get("/employee/status")

    body = response.json()
    assert body["has_completed_session"] is False
    assert body["last_session_id"] is None


def test_status_after_completed_session_reports_it(db_session: Session):
    client = make_client(db_session)
    start = client.post("/sessions", json={"role_title": "Software Engineer"})
    session_id = start.json()["session_id"]
    for _ in range(5):
        client.post(f"/sessions/{session_id}/answer", json={"answer": "a reasonably detailed answer"})

    response = client.get("/employee/status")

    body = response.json()
    assert body["has_completed_session"] is True
    assert body["last_session_id"] == session_id
    assert body["last_completed_at"] is not None
