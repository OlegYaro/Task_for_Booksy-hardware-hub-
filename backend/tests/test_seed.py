"""Tests for the dirty-data audit migration."""


def test_seed_preserves_duplicate_id_records(client, auth):
    """The seed has two records with id=4; neither may be dropped."""
    items = client.get("/api/hardware", headers=auth).json()
    assert len(items) == 11

    from_seed_id_4 = [i for i in items if i["original_seed_id"] == 4]
    assert len(from_seed_id_4) == 2
    names = {i["name"] for i in from_seed_id_4}
    assert "SAMSUNG Galaxy S21" in names
    assert "Duplicate ID Test Laptop" in names


def test_brand_typo_is_normalized(client, auth):
    items = client.get("/api/hardware", headers=auth).json()
    ipad = next(i for i in items if i["name"] == "iPad Pro 12.9")
    assert ipad["brand"] == "Apple"  # was "Appel" in the seed


def test_future_purchase_date_is_flagged(client, auth):
    items = client.get("/api/hardware", headers=auth).json()
    logitech = next(i for i in items if i["name"] == "Logitech MX Master 3")
    assert logitech["data_flag"] is not None
    assert "future" in logitech["data_flag"].lower()
