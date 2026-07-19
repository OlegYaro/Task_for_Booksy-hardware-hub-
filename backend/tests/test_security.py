"""Auth-hardening tests (OWASP ASVS mapping in README ## Security).

Covers the three guarantees the hardening adds:
  V6  — a JWT signed with the wrong key is rejected (no forged tokens).
  V2.2 — login gives one generic error for unknown-user vs wrong-password.
  V2.2.1 — repeated failures for one IP/email pair get locked out (429).
Plus the fail-closed config guard against shipping default secrets.
"""
import pytest
from jose import jwt

from app.auth import ALGORITHM
from app.config import Settings


def test_forged_token_with_wrong_key_is_rejected(client):
    # Anyone who *doesn't* know the server's signing key cannot mint a token.
    forged = jwt.encode(
        {"sub": "admin@booksy.com"}, "attacker-guessed-key", algorithm=ALGORITHM
    )
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {forged}"})
    assert resp.status_code == 401


def test_unknown_user_and_wrong_password_are_indistinguishable(client):
    unknown = client.post(
        "/api/auth/login",
        data={"username": "ghost@booksy.com", "password": "whatever"},
    )
    wrong_pw = client.post(
        "/api/auth/login",
        data={"username": "admin@booksy.com", "password": "not-the-password"},
    )
    # Same status and same body — the response leaks nothing about which emails exist.
    assert unknown.status_code == wrong_pw.status_code == 401
    assert unknown.json() == wrong_pw.json()


def test_repeated_failures_get_locked_out(client):
    from app.ratelimit import MAX_FAILURES

    creds = {"username": "admin@booksy.com", "password": "wrong"}
    # Burn through the allowed failures...
    for _ in range(MAX_FAILURES):
        assert client.post("/api/auth/login", data=creds).status_code == 401
    # ...the next attempt is throttled, even with the *correct* password.
    locked = client.post(
        "/api/auth/login",
        data={"username": "admin@booksy.com", "password": "admin123"},
    )
    assert locked.status_code == 429
    assert "Retry-After" in locked.headers


def test_successful_login_resets_the_throttle(client):
    creds = {"username": "admin@booksy.com", "password": "wrong"}
    for _ in range(3):
        client.post("/api/auth/login", data=creds)
    # A correct login clears the counter, so the account isn't stuck.
    ok = client.post(
        "/api/auth/login",
        data={"username": "admin@booksy.com", "password": "admin123"},
    )
    assert ok.status_code == 200


def test_production_refuses_default_signing_key():
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        Settings(environment="production", default_admin_password="a-strong-one")


def test_production_refuses_default_admin_password():
    with pytest.raises(RuntimeError, match="DEFAULT_ADMIN_PASSWORD"):
        Settings(environment="production", secret_key="a-real-secret")


def test_production_boots_with_real_secrets():
    s = Settings(
        environment="production",
        secret_key="a-real-secret",
        default_admin_password="a-strong-one",
    )
    assert s.is_production
