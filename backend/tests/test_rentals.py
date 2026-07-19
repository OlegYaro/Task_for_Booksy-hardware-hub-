"""Critical business-logic tests for the rental engine.

These guard the "no impossible states" rule from the brief.
"""
from tests.conftest import find_by_status


def test_cannot_rent_hardware_in_repair(client, auth):
    broken = find_by_status(client, auth, "Repair")
    resp = client.post(f"/api/hardware/{broken['id']}/rent", headers=auth)
    assert resp.status_code == 409
    assert "Repair" in resp.json()["detail"]


def test_cannot_rent_already_in_use(client, auth):
    in_use = find_by_status(client, auth, "In Use")
    resp = client.post(f"/api/hardware/{in_use['id']}/rent", headers=auth)
    assert resp.status_code == 409


def test_rent_then_return_happy_path(client, auth):
    item = find_by_status(client, auth, "Available")

    rented = client.post(f"/api/hardware/{item['id']}/rent", headers=auth)
    assert rented.status_code == 200
    assert rented.json()["status"] == "In Use"
    assert rented.json()["assigned_to"] == "admin@booksy.com"

    returned = client.post(f"/api/hardware/{item['id']}/return", headers=auth)
    assert returned.status_code == 200
    assert returned.json()["status"] == "Available"
    assert returned.json()["assigned_to"] is None


def test_cannot_return_item_that_is_not_in_use(client, auth):
    available = find_by_status(client, auth, "Available")
    resp = client.post(f"/api/hardware/{available['id']}/return", headers=auth)
    assert resp.status_code == 409
