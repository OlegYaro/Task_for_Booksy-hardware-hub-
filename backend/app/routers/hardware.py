from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_admin
from app.constants import STATUS_AVAILABLE, STATUS_REPAIR, VALID_STATUSES
from app.database import get_db
from app.models import Hardware, User
from app.schemas import HardwareCreate, HardwareOut, HardwareUpdate

router = APIRouter(prefix="/api/hardware", tags=["hardware"])

SORTABLE = {"id", "name", "brand", "purchase_date", "status"}


@router.get("", response_model=list[HardwareOut])
def list_hardware(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
    status_filter: Optional[str] = Query(None, alias="status"),
    brand: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "id",
    order: str = "asc",
):
    query = db.query(Hardware)

    if status_filter:
        query = query.filter(Hardware.status == status_filter)
    if brand:
        query = query.filter(Hardware.brand == brand)
    if search:
        like = f"%{search.lower()}%"
        query = query.filter(Hardware.name.ilike(like))

    if sort_by not in SORTABLE:
        sort_by = "id"
    direction = desc if order == "desc" else asc
    query = query.order_by(direction(getattr(Hardware, sort_by)))

    return query.all()


@router.post("", response_model=HardwareOut, status_code=status.HTTP_201_CREATED)
def create_hardware(
    payload: HardwareCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    if payload.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status '{payload.status}'")

    item = Hardware(
        name=payload.name,
        brand=payload.brand,
        purchase_date=payload.purchase_date,
        status=payload.status,
        notes=payload.notes,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{hardware_id}", response_model=HardwareOut)
def update_hardware(
    hardware_id: int,
    payload: HardwareUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    item = db.get(Hardware, hardware_id)
    if not item:
        raise HTTPException(status_code=404, detail="Hardware not found")

    data = payload.model_dump(exclude_unset=True)
    if "status" in data and data["status"] not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status '{data['status']}'")

    for field, value in data.items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)
    return item


@router.post("/{hardware_id}/toggle-repair", response_model=HardwareOut)
def toggle_repair(
    hardware_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Flip a device in/out of Repair.

    A device that is currently In Use cannot be sent to repair without being
    returned first — that would strand the rental.
    """
    item = db.get(Hardware, hardware_id)
    if not item:
        raise HTTPException(status_code=404, detail="Hardware not found")

    if item.status == STATUS_REPAIR:
        item.status = STATUS_AVAILABLE
    elif item.status == STATUS_AVAILABLE:
        item.status = STATUS_REPAIR
    else:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot toggle repair while status is '{item.status}'",
        )

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{hardware_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_hardware(
    hardware_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    item = db.get(Hardware, hardware_id)
    if not item:
        raise HTTPException(status_code=404, detail="Hardware not found")
    db.delete(item)
    db.commit()
