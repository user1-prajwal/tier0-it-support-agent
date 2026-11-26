"""Access tokens: a signed statement of WHO the caller is, and nothing more.

The token holds only the user id and an expiry. Role, active flag and group membership are
read from the database on every request (see deps.py), so revoking access works at once.
"""

from datetime import UTC, datetime, timedelta

import jwt
from pydantic import SecretStr

ALGORITHM = "HS256"
MIN_SECRET_LENGTH = 32


class InvalidToken(Exception):
    """The token is missing, malformed, forged or expired. The caller learns no more than that."""


def _check_secret(secret: str) -> None:
    if len(secret) < MIN_SECRET_LENGTH:
        raise ValueError(f"the JWT secret must be at least {MIN_SECRET_LENGTH} characters")


def require_secret(secret: SecretStr | None) -> str:
    """Unwrap the configured secret, refusing a missing or weak one."""
    value = secret.get_secret_value() if secret is not None else ""
    _check_secret(value)
    return value


def create_access_token(
    user_id: int, secret: str, *, minutes: int = 60, now: datetime | None = None
) -> str:
    _check_secret(secret)
    issued = now or datetime.now(UTC)
    payload = {"sub": str(user_id), "iat": issued, "exp": issued + timedelta(minutes=minutes)}
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def decode_access_token(token: str, secret: str) -> int:
    _check_secret(secret)
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=[ALGORITHM],  # a fixed list: a token cannot choose its own algorithm
            options={"require": ["exp", "sub"]},
        )
        return int(payload["sub"])
    except (jwt.PyJWTError, ValueError, KeyError) as exc:
        raise InvalidToken("invalid token") from exc