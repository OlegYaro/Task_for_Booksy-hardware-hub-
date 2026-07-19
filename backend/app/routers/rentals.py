from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.constants import STATUS_AVAILABLE, STATUS_IN_USE, RENTABLE_STATUSES
from app.database import get_db
from app.models import Hardware, Rental, User
from app.schemas import HardwareOut

router = APIRouter(prefix="/api/hardware", tags=["rentals"])


@router.post("/{hardware_id}/rent", response_model=HardwareOut)
def rent(
    hardware_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = db.get(Hardware, hardware_id)
    if not item:
        raise HTTPException(status_code=404, detail="Hardware not found")

    # Guard: only Available devices can be rented. This blocks renting
    # something already In Use or in Repair (an impossible state otherwise).
    if item.status not in RENTABLE_STATUSES:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot rent '{item.name}': status is '{item.status}'",
        )

    item.status = STATUS_IN_USE
    item.assigned_to = user.email
    db.add(Rental(hardware_id=item.id, user_id=user.id))
    db.commit()
    db.refresh(item)
    return item


@router.post("/{hardware_id}/return", response_model=HardwareOut)
def return_item(
    hardware_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = db.get(Hardware, hardware_id)
    if not item:
        raise HTTPException(status_code=404, detail="Hardware not found")

    # Guard: can only return something that is actually out on loan.
    if item.status != STATUS_IN_USE:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot return '{item.name}': it is not currently in use",
        )

    # Guard: a user can only return what they hold. Admins can force-return.
    if item.assigned_to and item.assigned_to != user.email and not user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="This device is assigned to another user",
        )

    # Close the open rental record, if we have one.
    open_rental = (
        db.query(Rental)
        .filter(Rental.hardware_id == item.id, Rental.returned_at.is_(None))
        .order_by(Rental.rented_at.desc())
        .first()
    )
    if open_rental:
        open_rental.returned_at = datetime.now(timezone.utc)

    item.status = STATUS_AVAILABLE
    item.assigned_to = None
    db.commit()
    db.refresh(item)
    return item
