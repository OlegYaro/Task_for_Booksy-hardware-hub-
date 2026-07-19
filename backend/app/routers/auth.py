from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    require_admin,
    verify_password_constant_time,
)
from app.database import get_db
from app.models import User
from app.ratelimit import login_rate_limiter
from app.schemas import Token, UserCreate, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])

# One generic message for every failure mode, so the response never reveals
# whether the email exists (OWASP ASVS V2.2 — no user enumeration).
_INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Incorrect email or password",
)


def _throttle_key(request: Request, email: str) -> str:
    client_ip = request.client.host if request.client else "unknown"
    return f"{client_ip}|{email.strip().lower()}"


@router.post("/login", response_model=Token)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    key = _throttle_key(request, form_data.username)

    # Refuse before touching the DB once this IP/email pair has failed too often.
    retry_after = login_rate_limiter.retry_after(key)
    if retry_after:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    user = db.query(User).filter(User.email == form_data.username).first()
    # Constant-time even when the user is missing: same bcrypt work either way.
    hashed = user.hashed_password if user else None
    if not verify_password_constant_time(form_data.password, hashed) or user is None:
        login_rate_limiter.record_failure(key)
        raise _INVALID_CREDENTIALS

    login_rate_limiter.reset(key)
    return Token(access_token=create_access_token(user.email))


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Only an admin can create accounts — there is no public sign-up."""
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        is_admin=payload.is_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    return db.query(User).order_by(User.id).all()
