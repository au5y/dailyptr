import os
import tempfile

import pytest

# Must be set before `app.*` modules are imported anywhere, since database.py
# reads config.DATABASE_URL at import time to build the SQLAlchemy engine.
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mktemp(suffix='.db')}"
os.environ.setdefault("SANDBOX_MODE", "subprocess")  # no Docker daemon needed to run the suite

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.database import SessionLocal, init_db  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _ensure_tables():
    # Some tests (test_scoring.py) talk to the DB directly without going
    # through the app's startup event, so create the schema once up front.
    init_db()


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
