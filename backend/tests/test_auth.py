"""Access-control tests: accounts are admin-created only."""


def test_anonymous_cannot_create_user(client):
    resp = client.post(
        "/api/auth/users", json={"email": "x@booksy.com", "password": "pw"}
    )
    assert resp.status_code == 401


def test_admin_can_create_user_who_can_then_log_in(client, auth):
    created = client.post(
        "/api/auth/users",
        headers=auth,
        json={"email": "new.hire@booksy.com", "password": "welcome1"},
    )
    assert created.status_code == 201

    login = client.post(
        "/api/auth/login",
        data={"username": "new.hire@booksy.com", "password": "welcome1"},
    )
    assert login.status_code == 200


def test_non_admin_cannot_create_user(client, auth):
    # Create a normal (non-admin) user, then act as them.
    client.post(
        "/api/auth/users",
        headers=auth,
        json={"email": "regular@booksy.com", "password": "pw123456"},
    )
    token = client.post(
        "/api/auth/login",
        data={"username": "regular@booksy.com", "password": "pw123456"},
    ).json()["access_token"]

    resp = client.post(
        "/api/auth/users",
        headers={"Authorization": f"Bearer {token}"},
        json={"email": "another@booksy.com", "password": "pw123456"},
    )
    assert resp.status_code == 403
