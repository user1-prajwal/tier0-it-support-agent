from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import Engine

from app.auth.ratelimit import FailureLimiter
from app.auth.tokens import InvalidToken, decode_access_token, require_secret
from app.config import Settings
from app.db.session import get_engine
from app.db.users import User, get_user_by_id

bearer = HTTPBearer(auto_error=False)  # we answer a missing token ourselves, with the same 401


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_login_limiter() -> FailureLimiter:
    settings = get_settings()
    return FailureLimiter(settings.login_max_failures, settings.login_window_seconds)


def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    settings: Annotated[Settings, Depends(get_settings)],
    engine: Annotated[Engine, Depends(get_engine)],
) -> User:
    """Who is asking? The token proves identity only. Everything else is read fresh from the
    database now: whether the account is active, its role, its groups."""
    unauthorized = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Not authenticated.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    try:
        user_id = decode_access_token(credentials.credentials, require_secret(settings.jwt_secret))
    except InvalidToken:
        raise unauthorized from None

    user = get_user_by_id(engine, user_id)
    if user is None or not user.is_active:
        raise unauthorized  # unknown and deactivated look the same as a bad token
    return user