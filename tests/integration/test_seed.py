from sqlalchemy import text

from app.auth.passwords import verify_password
from app.db.seed import seed_demo_users
from app.db.users import get_user_by_email

# Written out by hand on purpose: it must not share code with the seed it checks.
EXPECTED = {
    "alice@demo.local": ("employee", True, {"everyone"}),
    "bob@demo.local": ("helpdesk", True, {"everyone", "helpdesk"}),
    "carol@demo.local": ("security_admin", True, {"everyone", "security"}),
    "dave@demo.local": ("hr", True, {"everyone", "hr"}),
    "erin@demo.local": ("employee", False, {"everyone"}),  # deactivated
}


def test_seed_creates_the_demo_users_once_with_the_right_groups(engine, clean_db):
    assert seed_demo_users(engine, "password-for-tests") == 5
    assert seed_demo_users(engine, "password-for-tests") == 0  # running again changes nothing

    with engine.connect() as conn:
        names = dict(conn.execute(text("SELECT id, name FROM groups")).all())
        assert conn.execute(text("SELECT count(*) FROM users")).scalar_one() == 5
        stored = conn.execute(
            text("SELECT password_hash FROM users WHERE email = 'alice@demo.local'")
        ).scalar_one()

    for email, (role, active, groups) in EXPECTED.items():
        user = get_user_by_email(engine, email)
        assert (user.role, user.is_active) == (role, active), email
        assert {names[g] for g in user.group_ids} == groups, email

    assert get_user_by_email(engine, "Alice@Demo.Local").email == "alice@demo.local"
    assert get_user_by_email(engine, "nobody@demo.local") is None
    assert stored != "password-for-tests" and verify_password(stored, "password-for-tests")