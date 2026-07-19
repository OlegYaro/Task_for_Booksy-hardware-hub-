"""Seed + audit migration for the initial dataset.

The raw seed (see seed_data.py) is intentionally dirty. This module normalises
it into clean rows and records every correction it makes so the process is
auditable rather than a silent black box.
"""
from datetime import date, datetime

from app.auth import hash_password
from app.config import settings
from app.constants import STATUS_AVAILABLE, VALID_STATUSES
from app.database import SessionLocal
from app.models import Hardware, User
from app.seed_data import RAW_SEED

# Known brand typos -> canonical spelling.
BRAND_FIXES = {
    "appel": "Apple",
}

# Collected during seeding so we can print / document what was changed.
audit_log: list[str] = []


def _log(message: str) -> None:
    audit_log.append(message)
    print(f"[seed-audit] {message}")


def _normalize_brand(brand: str) -> str:
    brand = (brand or "").strip()
    fixed = BRAND_FIXES.get(brand.lower())
    if fixed:
        _log(f"Brand typo '{brand}' -> '{fixed}'")
        return fixed
    return brand


def _parse_date(raw, name: str):
    """Return (iso_string_or_None, flag_or_None)."""
    if raw is None:
        return None, "missing purchase date"

    # Try ISO first, then the day-first format seen in the seed.
    parsed = None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
        try:
            parsed = datetime.strptime(raw, fmt).date()
            break
        except ValueError:
            continue

    if parsed is None:
        _log(f"'{name}': unparseable date '{raw}', kept as null")
        return None, f"unparseable date '{raw}'"

    iso = parsed.isoformat()
    if iso != raw:
        _log(f"'{name}': date '{raw}' normalized to '{iso}'")

    if parsed > date.today():
        _log(f"'{name}': purchase date '{iso}' is in the future")
        return iso, f"purchase date in the future ({iso})"

    return iso, None


def _normalize_status(raw: str, name: str):
    status = (raw or "").strip()
    if status not in VALID_STATUSES:
        _log(f"'{name}': unknown status '{status}', defaulting to Available + flag")
        return STATUS_AVAILABLE, f"original status was '{status}'"
    return status, None


def _clean_record(rec: dict):
    name = rec.get("name") or "Unnamed device"
    flags: list[str] = []

    brand = _normalize_brand(rec.get("brand", ""))
    if not brand:
        flags.append("empty brand")

    purchase_date, date_flag = _parse_date(rec.get("purchaseDate"), name)
    if date_flag:
        flags.append(date_flag)

    status, status_flag = _normalize_status(rec.get("status", ""), name)
    if status_flag:
        flags.append(status_flag)

    # Fold notes/history into one free-text field for the auditor to read.
    notes = rec.get("notes") or rec.get("history")

    return Hardware(
        name=name,
        brand=brand,
        purchase_date=purchase_date,
        status=status,
        notes=notes,
        assigned_to=rec.get("assignedTo"),
        data_flag="; ".join(flags) if flags else None,
    )


def seed_database() -> None:
    db = SessionLocal()
    try:
        if db.query(Hardware).count() > 0:
            return  # already seeded

        audit_log.clear()

        # Deduplicate the raw records by their id before inserting.
        by_id: dict[int, dict] = {}
        for rec in RAW_SEED:
            by_id[rec["id"]] = rec

        for rec in by_id.values():
            db.add(_clean_record(rec))

        # Ensure there is always a way into the system.
        if not db.query(User).filter(User.email == settings.default_admin_email).first():
            db.add(
                User(
                    email=settings.default_admin_email,
                    hashed_password=hash_password(settings.default_admin_password),
                    is_admin=True,
                )
            )

        db.commit()
        _log(f"Seed complete: {db.query(Hardware).count()} hardware rows inserted")
    finally:
        db.close()
