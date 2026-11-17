from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.security import verify_password, get_password_hash, create_access_token
from backend.app.core.dependencies import get_current_user
from backend.app.models.user import User
from backend.app.schemas import UserRegister, UserLogin, UserUpdate, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["Authentication"])

# In-memory IP-based rate limiter for authentication endpoints
_LOGIN_ATTEMPTS: Dict[str, List[datetime]] = defaultdict(list)
_MAX_ATTEMPTS_PER_MINUTE = 15


def check_rate_limit(request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    now = datetime.now(timezone.utc)
    one_minute_ago = now - timedelta(minutes=1)

    # Filter attempts within the last minute
    _LOGIN_ATTEMPTS[client_ip] = [
        t for t in _LOGIN_ATTEMPTS[client_ip] if t > one_minute_ago
    ]

    if len(_LOGIN_ATTEMPTS[client_ip]) >= _MAX_ATTEMPTS_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts. Please wait one minute before trying again.",
        )
    _LOGIN_ATTEMPTS[client_ip].append(now)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, request: Request, db: Session = Depends(get_db)):
    check_rate_limit(request)

    # Check if user already exists
    existing = db.query(User).filter(User.email == user_in.email.lower().strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists",
        )

    user = User(
        display_name=user_in.display_name.strip(),
        email=user_in.email.lower().strip(),
        password_hash=get_password_hash(user_in.password),
        role="student",
        is_active=True,
        college=user_in.college.strip() if user_in.college else "Medi-Caps University",
        target_role=user_in.target_role.strip() if user_in.target_role else "Software Development Engineer (SDE)",
        research_consent=user_in.research_consent if user_in.research_consent is not None else True,
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=user.id, role=user.role)
    return TokenResponse(access_token=token, token_type="bearer", user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(login_in: UserLogin, request: Request, db: Session = Depends(get_db)):
    check_rate_limit(request)

    user = db.query(User).filter(User.email == login_in.email.lower().strip()).first()
    if not user or not verify_password(login_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password credentials",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    token = create_access_token(subject=user.id, role=user.role)
    return TokenResponse(access_token=token, token_type="bearer", user=UserOut.model_validate(user))


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """Session invalidation handled client-side (token removal)."""
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)


@router.patch("/profile", response_model=UserOut)
def update_profile(
    profile_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Updates user profile information and research consent."""
    if profile_in.display_name is not None:
        current_user.display_name = profile_in.display_name.strip()
    if profile_in.college is not None:
        current_user.college = profile_in.college.strip()
    if profile_in.target_role is not None:
        current_user.target_role = profile_in.target_role.strip()
    if profile_in.research_consent is not None:
        current_user.research_consent = profile_in.research_consent

    db.commit()
    db.refresh(current_user)
    return UserOut.model_validate(current_user)
