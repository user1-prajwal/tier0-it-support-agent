from dataclasses import dataclass

from sqlalchemy import Engine, text

BY_EMAIL_SQL = text(
    """
    SELECT u.id, u.email, u.display_name, u.role, u.is_active,
           COALESCE(
               array_agg(ug.group_id ORDER BY ug.group_id) FILTER (WHERE ug.group_id IS NOT NULL),
               CAST('{}' AS bigint[])
           ) AS group_ids
    FROM users u
    LEFT JOIN user_groups ug ON ug.user_id = u.id
    WHERE u.email = lower(:email)
    GROUP BY u.id
    """
)


@dataclass(frozen=True)
class User:
    id: int
    email: str
    display_name: str
    role: str
    is_active: bool
    group_ids: tuple[int, ...]  # read from the database at the moment of the call. Never cached


def get_user_by_email(engine: Engine, email: str) -> User | None:
    with engine.connect() as conn:
        row = conn.execute(BY_EMAIL_SQL, {"email": email}).one_or_none()
    if row is None:
        return None
    return User(row.id, row.email, row.display_name, row.role, row.is_active, tuple(row.group_ids))