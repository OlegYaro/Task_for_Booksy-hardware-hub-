from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


# ---- Auth ----
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    is_admin: bool = False


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    is_admin: bool


# ---- Hardware ----
class HardwareCreate(BaseModel):
    name: str
    brand: str = ""
    purchase_date: Optional[str] = None
    status: str = "Available"
    notes: Optional[str] = None


class HardwareUpdate(BaseModel):
    name: Optional[str] = None
    brand: Optional[str] = None
    purchase_date: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class HardwareOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_seed_id: Optional[int] = None
    name: str
    brand: str
    purchase_date: Optional[str]
    status: str
    notes: Optional[str]
    assigned_to: Optional[str]
    data_flag: Optional[str]


# ---- AI ----
class SearchQuery(BaseModel):
    query: str


class AuditFinding(BaseModel):
    hardware_id: int
    name: str
    severity: str  # "high" | "medium" | "low"
    issue: str
    recommendation: str
