"""Create the demo users. Safe to run again: it only adds users that are missing.

    python -m app.db.seed        (needs DEMO_PASSWORD in .env: a demo-only password)
"""

from sqlalchemy import Engine, text

from app.auth.passwords import hash_password
from app.config import Settings
from app.db.demo_users import DEMO_USERS
from app.db.session import get_engine

INSERT_USER = text(
    """
    INSERT INTO users (email, display_name, password_hash, role, is_active)
    VALUES (:email, :display_name, :password_hash, :role, :is_active)
    ON CONFLICT (email) DO NOTHING
    RETURNING id
    """
)
INSERT_MEMBERSHIPS = text(
    """
    INSERT INTO user_groups (user_id, group_id)
    SELECT CAST(:user_id AS bigint), id FROM groups WHERE name = ANY(:names)
    """
)


def seed_demo_users(engine: Engine, password: str) -> int:
    """Returns how many users were created. An existing user is never modified."""
    created = 0
    with engine.begin() as conn:
        for user in DEMO_USERS:
            user_id = conn.execute(
                INSERT_USER,
                {
                    "email": user.email,
                    "display_name": user.display_name,
                    "password_hash": hash_password(password),
                    "role": user.role,
                    "is_active": user.is_active,
                },
            ).scalar_one_or_none()
            if user_id is None:
                continue  # already there
            result = conn.execute(
                INSERT_MEMBERSHIPS, {"user_id": user_id, "names": list(user.groups)}
            )
            if result.rowcount != len(user.groups):  # a missing group must stop the seed
                raise RuntimeError(f"could not add every group for {user.email}")
            created += 1
    return created


def main() -> int:
    password = Settings().demo_password
    if password is None:
        print("DEMO_PASSWORD is not set. Add a demo-only password to .env (see .env.example).")
        return 1
    created = seed_demo_users(get_engine(), password.get_secret_value())
    print(f"created {created} of {len(DEMO_USERS)} demo users")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())