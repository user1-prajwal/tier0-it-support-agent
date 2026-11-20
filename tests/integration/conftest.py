import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url

from app.config import Settings
from app.db.session import get_engine

ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"
TEST_DB_NAME = "tier0_test"


def ensure_test_database(url: URL) -> None:
    """Create the test database if it does not exist yet (works locally and in CI)."""
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": TEST_DB_NAME}
        ).scalar()
        if not exists:
            # CREATE DATABASE cannot take a bound parameter. The name is our own constant.
            conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    admin.dispose()


@pytest.fixture(scope="session", autouse=True)
def engine():
    """Run every integration test against a separate, migrated test database."""
    real_url = make_url(Settings().database_url.get_secret_value())
    ensure_test_database(real_url)

    previous = os.environ.get("DATABASE_URL")
    test_url = real_url.set(database=TEST_DB_NAME)
    # str(url) hides the password, so we must ask for it explicitly.
    os.environ["DATABASE_URL"] = test_url.render_as_string(hide_password=False)
    get_engine.cache_clear()

    # Safety net: a future test that empties tables must never reach the dev database.
    assert get_engine().url.database == TEST_DB_NAME

    command.upgrade(Config(str(ALEMBIC_INI)), "head")
    yield get_engine()

    get_engine.cache_clear()
    if previous is None:
        os.environ.pop("DATABASE_URL", None)
    else:
        os.environ["DATABASE_URL"] = previous