"""Thin wrapper around the Anthropic API.

The whole AI layer degrades gracefully: if no API key is configured we return
None from here and the callers fall back to deterministic logic, so the app and
its demo work with or without a key.
"""
import json
from typing import Optional

from app.config import settings

_client = None


def ai_enabled() -> bool:
    return bool(settings.anthropic_api_key)


def _get_client():
    global _client
    if _client is None:
        from anthropic import Anthropic

        _client = Anthropic(api_key=settings.anthropic_api_key)
    return _client


def call_json(system: str, user: str, max_tokens: int = 1500) -> Optional[dict]:
    """Call Claude and parse a JSON object out of the response.

    Returns None if the AI layer is disabled or the call/parse fails, so the
    caller can fall back to deterministic logic instead of erroring the request.
    """
    if not ai_enabled():
        return None

    try:
        client = _get_client()
        message = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(
            block.text for block in message.content if block.type == "text"
        ).strip()
        return _extract_json(text)
    except Exception as exc:  # network, auth, rate-limit, malformed output...
        print(f"[ai] call failed, falling back to deterministic logic: {exc}")
        return None


def _extract_json(text: str) -> Optional[dict]:
    # Claude sometimes wraps JSON in ```json fences; strip them.
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return None
    return json.loads(text[start : end + 1])
