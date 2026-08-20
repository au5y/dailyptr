import os
import tempfile
import uuid

import pytest

# Must be set before `app.*` modules are imported anywhere, since database.py
# reads config.DATABASE_URL at import time to build the SQLAlchemy engine.
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mktemp(suffix='.db')}"

from fastapi.testclient import TestClient  # noqa: E402
from app import auth, models  # noqa: E402
from app.main import app  # noqa: E402
from app.database import SessionLocal, init_db  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _ensure_tables():
    # Some tests (test_scoring.py) talk to the DB directly without going
    # through the app's startup event, so create the schema once up front.
    init_db()


def _make_user(db) -> models.User:
    """A real User row - identity would normally come from Google (see
    app/auth.py), but the app's own login/session logic is independent of
    that OAuth handshake, so tests skip it and create the row + session
    cookie directly rather than mocking Google's endpoints."""
    unique = uuid.uuid4().hex[:8]
    user = models.User(google_sub=f"test-sub-{unique}", email=f"test-{unique}@example.com", name=f"Test {unique}")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def test_user(db_session):
    """A real User row, for tests that talk to the DB directly (test_scoring.py)."""
    return _make_user(db_session)


@pytest.fixture()
def client():
    """A TestClient logged in as a fresh, unique user, so every test's Day
    rows are isolated from every other test's regardless of which dates
    they touch."""
    with TestClient(app) as c:
        db = SessionLocal()
        try:
            user = _make_user(db)
        finally:
            db.close()
        c.cookies.set(auth.COOKIE_NAME, auth.make_session_cookie(user.id))
        yield c


@pytest.fixture()
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
