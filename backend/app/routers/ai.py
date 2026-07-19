from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.ai.auditor import audit_inventory
from app.ai.client import ai_enabled
from app.ai.search import semantic_search
from app.auth import get_current_user
from app.database import get_db
from app.models import Hardware, User
from app.ratelimit import ai_global_limiter, ai_per_ip_limiter
from app.schemas import HardwareOut, SearchQuery

router = APIRouter(prefix="/api/ai", tags=["ai"])


def throttle_ai(request: Request):
    """Cap the billable AI endpoints: per-IP burst + a hard global daily limit.

    The demo credentials are public, so without this anyone could loop these
    endpoints and run up the LLM bill.
    """
    ip = request.client.host if request.client else "unknown"
    if not ai_per_ip_limiter.allow(ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many AI requests from your address. Please slow down.",
        )
    if not ai_global_limiter.allow("global"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="The demo's daily AI limit has been reached. Try again tomorrow.",
        )


@router.get("/status")
def ai_status(_user: User = Depends(get_current_user)):
    """Tells the frontend whether the live LLM or the fallback is in use."""
    return {"llm_enabled": ai_enabled()}


@router.get("/audit")
def audit(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
    _throttle: None = Depends(throttle_ai),
):
    items = db.query(Hardware).order_by(Hardware.id).all()
    return audit_inventory(items)


@router.post("/search")
def search(
    payload: SearchQuery,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
    _throttle: None = Depends(throttle_ai),
):
    items = db.query(Hardware).all()
    result = semantic_search(payload.query, items)

    by_id = {i.id: i for i in items}
    ordered = [by_id[i] for i in result["matched_ids"] if i in by_id]
    return {
        "source": result["source"],
        "explanation": result.get("explanation", ""),
        "results": [HardwareOut.model_validate(i).model_dump() for i in ordered],
    }
