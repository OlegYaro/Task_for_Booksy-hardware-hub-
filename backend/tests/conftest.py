import os
import tempfile

# Point the app at a throwaway SQLite file and force the AI fallback BEFORE
# any app module is imported, so tests never hit the network or the dev DB.
_tmpdir = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmpdir}/test.db"
os.environ["ANTHROPIC_API_KEY"] = ""

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app
from app.seed import seed_database


@pytest.fixture(autouse=True)
def _reset_login_throttle():
    # The login rate limiter is process-global in-memory state; clear it around
    # every test so failure counts never leak between cases.
    from app.ratelimit import (
        ai_global_limiter,
        ai_per_ip_limiter,
        login_rate_limiter,
    )

    for limiter in (login_rate_limiter, ai_per_ip_limiter, ai_global_limiter):
        limiter.clear()
    yield
    for limiter in (login_rate_limiter, ai_per_ip_limiter, ai_global_limiter):
        limiter.clear()


@pytest.fixture
def client():
    # Fresh, freshly-seeded database for every test.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_database()
    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin_token(client):
    resp = client.post(
        "/api/auth/login",
        data={"username": "admin@booksy.com", "password": "admin123"},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture
def auth(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


def find_by_status(client, auth, status):
    """Return the first hardware item currently in the given status."""
    items = client.get("/api/hardware", headers=auth).json()
    return next(i for i in items if i["status"] == status)
