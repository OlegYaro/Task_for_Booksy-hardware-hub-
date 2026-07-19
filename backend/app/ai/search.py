"""Semantic search over the inventory.

Turns a natural-language request ("something to test a mobile app on") into a
ranked list of matching devices. Uses Claude when a key is present; otherwise
falls back to a small keyword/intent map so the feature still works in a demo.
"""
from app.ai.client import ai_enabled, call_json
from app.models import Hardware

# Fallback intent -> keywords found in a device name/brand.
INTENT_KEYWORDS = {
    "phone": ["iphone", "galaxy", "pixel", "android"],
    "mobile": ["iphone", "galaxy", "pixel", "android"],
    "laptop": ["macbook", "xps", "thinkpad", "laptop"],
    "computer": ["macbook", "xps", "laptop"],
    "tablet": ["ipad", "tab"],
    "mouse": ["mouse", "basilisk", "mx master"],
    "headphone": ["wh-1000", "headphone", "sony"],
    "audio": ["wh-1000", "headphone", "sony"],
    "apple": ["apple", "macbook", "iphone", "ipad"],
}


def _item_dict(item: Hardware) -> dict:
    return {
        "id": item.id,
        "name": item.name,
        "brand": item.brand,
        "status": item.status,
    }


def semantic_search(query: str, items: list[Hardware]) -> dict:
    result = _ai_search(query, items) if ai_enabled() else None
    if result is not None:
        return {"source": "claude", **result}
    return {"source": "deterministic", **_keyword_search(query, items)}


# ---- Deterministic fallback ----
def _keyword_search(query: str, items: list[Hardware]) -> dict:
    q = query.lower()
    wanted: set[str] = set()
    for intent, keywords in INTENT_KEYWORDS.items():
        if intent in q:
            wanted.update(keywords)
    # Also match raw words from the query directly.
    wanted.update(w for w in q.split() if len(w) > 2)

    matches = []
    for item in items:
        haystack = f"{item.name} {item.brand}".lower()
        if any(kw in haystack for kw in wanted):
            matches.append(item.id)

    return {
        "matched_ids": matches,
        "explanation": "Matched by keyword/intent (no LLM key configured).",
    }


# ---- Claude-powered search ----
def _ai_search(query: str, items: list[Hardware]) -> dict | None:
    system = (
        "You match a user's natural-language hardware request to devices in an "
        "inventory. Given the user query and a JSON list of devices, return the "
        "ids of devices that fit the intent, best match first. Respond ONLY with "
        'JSON: {"matched_ids": [int], "explanation": str}.'
    )
    payload = [_item_dict(i) for i in items]
    user = f"User query: {query!r}\nInventory:\n{payload}"
    result = call_json(system, user)
    if result is None:
        return None
    return {
        "matched_ids": result.get("matched_ids", []),
        "explanation": result.get("explanation", ""),
    }
