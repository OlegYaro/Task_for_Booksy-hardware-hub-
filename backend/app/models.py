from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    rentals = relationship("Rental", back_populates="user")


class Hardware(Base):
    __tablename__ = "hardware"

    id = Column(Integer, primary_key=True, index=True)

    # The id that came from the seed file. NOT used as the primary key: the
    # seed contains a duplicate id, so trusting it would drop a real record.
    # Kept only for provenance/traceability back to the source data.
    original_seed_id = Column(Integer, nullable=True)

    name = Column(String, nullable=False)
    brand = Column(String, nullable=False, default="")
    purchase_date = Column(String, nullable=True)  # ISO string, nullable for unknown
    status = Column(String, nullable=False, default="Available")

    # Free-text signal from the seed data (notes / history). Fed to the AI auditor.
    notes = Column(String, nullable=True)

    # Email of the current holder when status == "In Use".
    assigned_to = Column(String, nullable=True)

    # Set when the migration flagged this record as needing a human look
    # (dirty seed data: bad date, unknown status, empty brand, id collision...).
    data_flag = Column(String, nullable=True)

    rentals = relationship("Rental", back_populates="hardware")


class Rental(Base):
    __tablename__ = "rentals"

    id = Column(Integer, primary_key=True, index=True)
    hardware_id = Column(Integer, ForeignKey("hardware.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rented_at = Column(DateTime, default=_utcnow, nullable=False)
    returned_at = Column(DateTime, nullable=True)

    hardware = relationship("Hardware", back_populates="rentals")
    user = relationship("User", back_populates="rentals")
