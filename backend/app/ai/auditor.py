"""Inventory Auditor.

Reads the whole inventory (statuses, dates, and the free-text notes/history that
came with the seed) and flags records that a human should look at — a device
marked Available that is physically broken, an impossible purchase date, a data
record still carrying a migration flag, and so on.

With an API key it uses Claude to reason over the free text; without one it
falls back to deterministic rules so the feature is always demoable.
"""
from datetime import date, datetime

from app.ai.client import ai_enabled, call_json
from app.constants import STATUS_AVAILABLE
from app.models import Hardware

# Keywords in notes/history that suggest a device is not fit to be issued.
DAMAGE_KEYWORDS = [
    "swelling", "swollen", "liquid", "damage", "damaged", "cracked",
    "broken", "do not issue", "sticky", "service", "faulty",
]


def _item_dict(item: Hardware) -> dict:
    return {
        "id": item.id,
        "name": item.name,
        "brand": item.brand,
        "purchase_date": item.purchase_date,
        "status": item.status,
        "notes": item.notes,
        "data_flag": item.data_flag,
    }


def audit_inventory(items: list[Hardware]) -> dict:
    findings = _ai_audit(items) if ai_enabled() else None
    if findings is None:
        findings = _rule_audit(items)
        source = "deterministic"
    else:
        source = "claude"
    # High severity first.
    order = {"high": 0, "medium": 1, "low": 2}
    findings.sort(key=lambda f: order.get(f.get("severity", "low"), 3))
    return {"source": source, "findings": findings}


# ---- Deterministic fallback ----
def _rule_audit(items: list[Hardware]) -> list[dict]:
    findings: list[dict] = []
    for item in items:
        text = (item.notes or "").lower()
        matched = [kw for kw in DAMAGE_KEYWORDS if kw in text]

        if matched and item.status == STATUS_AVAILABLE:
            findings.append({
                "hardware_id": item.id,
                "name": item.name,
                "severity": "high",
                "issue": f"Marked Available but notes mention: {item.notes}",
                "recommendation": "Move to Repair until inspected.",
            })
        elif matched:
            findings.append({
                "hardware_id": item.id,
                "name": item.name,
                "severity": "medium",
                "issue": f"Notes mention a possible defect: {item.notes}",
                "recommendation": "Confirm the device was serviced.",
            })

        if item.purchase_date:
            try:
                if datetime.strptime(item.purchase_date, "%Y-%m-%d").date() > date.today():
                    findings.append({
                        "hardware_id": item.id,
                        "name": item.name,
                        "severity": "medium",
                        "issue": f"Purchase date {item.purchase_date} is in the future.",
                        "recommendation": "Likely a data-entry error; verify the date.",
                    })
            except ValueError:
                pass

        if item.data_flag:
            findings.append({
                "hardware_id": item.id,
                "name": item.name,
                "severity": "low",
                "issue": f"Carries a data-migration flag: {item.data_flag}",
                "recommendation": "Review the imported record for correctness.",
            })
    return findings


# ---- Claude-powered audit ----
def _ai_audit(items: list[Hardware]) -> list[dict] | None:
    system = (
        "You are an inventory auditor for an internal hardware-rental tool. "
        "You are given a JSON list of devices with statuses, purchase dates and "
        "free-text notes. Identify records a human should review: devices that "
        "are Available but physically damaged, impossible or suspicious dates, "
        "missing or inconsistent data. Do NOT invent problems that aren't "
        "supported by the data. Respond ONLY with a JSON object of the form "
        '{"findings": [{"hardware_id": int, "name": str, "severity": '
        '"high"|"medium"|"low", "issue": str, "recommendation": str}]}.'
    )
    payload = [_item_dict(i) for i in items]
    result = call_json(system, f"Inventory:\n{payload}")
    if result is None:
        return None
    return result.get("findings", [])
