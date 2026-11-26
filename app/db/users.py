from dataclasses import dataclass, field

from sqlalchemy import Engine, text

_USER_SELECT = """
    SELECT u.id, u.email, u.display_name, u.role, u.is_active,
           COALESCE(
               array_agg(ug.group_id ORDER BY ug.group_id) FILTER (WHERE ug.group_id IS NOT NULL),
               CAST('{}' AS bigint[])
           ) AS group_ids
    FROM users u
    LEFT JOIN user_groups ug ON ug.user_id = u.id
"""  # constant text only: no user input is ever placed into SQL
BY_EMAIL_SQL = text(_USER_SELECT + " WHERE u.email = lower(:email) GROUP BY u.id")
BY_ID_SQL = text(_USER_SELECT + " WHERE u.id = :id GROUP BY u.id")
CREDENTIALS_SQL = text(
    "SELECT id, password_hash, is_active FROM users WHERE email = lower(:email)"
)


@dataclass(frozen=True)
class User:
    id: int
    email: str
    display_name: str
    role: str
    is_active: bool
    group_ids: tuple[int, ...]  # read from the database at the moment of the call. Never cached


@dataclass(frozen=True)
class Credentials:
    user_id: int
    password_hash: str = field(repr=False)  # never appears in a log line or an error message
    is_active: bool


def _to_user(row) -> User | None:
    if row is None:
        return None
    return User(row.id, row.email, row.display_name, row.role, row.is_active, tuple(row.group_ids))


def get_user_by_email(engine: Engine, email: str) -> User | None:
    with engine.connect() as conn:
        return _to_user(conn.execute(BY_EMAIL_SQL, {"email": email}).one_or_none())


def get_user_by_id(engine: Engine, user_id: int) -> User | None:
    with engine.connect() as conn:
        return _to_user(conn.execute(BY_ID_SQL, {"id": user_id}).one_or_none())


def get_credentials(engine: Engine, email: str) -> Credentials | None:
    with engine.connect() as conn:
        row = conn.execute(CREDENTIALS_SQL, {"email": email}).one_or_none()
    return None if row is None else Credentials(row.id, row.password_hash, row.is_active)