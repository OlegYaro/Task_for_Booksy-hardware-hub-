from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai.auditor import audit_inventory
from app.ai.client import ai_enabled
from app.ai.search import semantic_search
from app.auth import get_current_user
from app.database import get_db
from app.models import Hardware, User
from app.schemas import HardwareOut, SearchQuery

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.get("/status")
def ai_status(_user: User = Depends(get_current_user)):
    """Tells the frontend whether the live LLM or the fallback is in use."""
    return {"llm_enabled": ai_enabled()}


@router.get("/audit")
def audit(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    items = db.query(Hardware).order_by(Hardware.id).all()
    return audit_inventory(items)


@router.post("/search")
def search(
    payload: SearchQuery,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
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
