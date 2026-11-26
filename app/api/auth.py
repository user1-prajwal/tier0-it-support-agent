from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import Engine

from app.auth.deps import current_user, get_login_limiter, get_settings
from app.auth.passwords import dummy_hash, verify_password
from app.auth.ratelimit import FailureLimiter
from app.auth.tokens import create_access_token, require_secret
from app.config import Settings
from app.db.groups import group_names_by_id
from app.db.session import get_engine
from app.db.users import User, get_credentials

router = APIRouter(prefix="/auth")


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


@router.post("/login")
def login(
    body: LoginRequest,
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    engine: Annotated[Engine, Depends(get_engine)],
    limiter: Annotated[FailureLimiter, Depends(get_login_limiter)],
) -> TokenResponse:
    # The account key is built from whatever email was typed, real or not, so a lockout
    # never reveals which accounts exist.
    keys = [
        f"ip:{request.client.host if request.client else 'unknown'}",
        f"account:{body.email.strip().lower()}",
    ]
    if any(limiter.is_blocked(key) for key in keys):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many failed attempts. Try again later.",
            headers={"Retry-After": str(settings.login_window_seconds)},
        )

    credentials = get_credentials(engine, body.email)
    # Always run the password check, against a dummy hash if the account does not exist.
    stored_hash = credentials.password_hash if credentials else dummy_hash()
    password_ok = verify_password(stored_hash, body.password)

    if credentials is None or not credentials.is_active or not password_ok:
        for key in keys:
            limiter.record_failure(key)
        # One message for every reason: wrong password, no such account, deactivated account.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password.")

    token = create_access_token(
        credentials.user_id,
        require_secret(settings.jwt_secret),
        minutes=settings.access_token_minutes,
    )
    return TokenResponse(access_token=token, expires_in=settings.access_token_minutes * 60)


@router.get("/me")
def me(
    user: Annotated[User, Depends(current_user)],
    engine: Annotated[Engine, Depends(get_engine)],
) -> dict[str, object]:
    return {
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role,
        "groups": group_names_by_id(engine, user.group_ids),
    }