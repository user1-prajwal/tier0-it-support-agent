
import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url

from app.auth.deps import get_login_limiter, get_settings
from app.auth.ratelimit import FailureLimiter
from app.config import Settings
from app.db.seed import seed_demo_users
from app.db.session import get_engine
from app.ingest.pipeline import ingest_file
from app.main import create_app
from app.retrieval.embedder import HashEmbedder

ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"
TEST_DB_NAME = "tier0_test"


def ensure_test_database(url: URL) -> None:
    """Create the test database if it does not exist yet (works locally and in CI)."""
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": TEST_DB_NAME},
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


@pytest.fixture
def clean_db(engine):
    """Empty the document tables before a test that writes rows (test database only)."""
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE users, documents RESTART IDENTITY CASCADE"))


@pytest.fixture
def auth_client(engine, clean_db):
    """A client for the real app on the test database, with the five demo users seeded."""
    seed_demo_users(engine, "password-for-tests")

    app = create_app()

    settings = Settings(
        _env_file=None,
        database_url="postgresql+psycopg://unused",
        jwt_secret="a-test-secret-that-is-at-least-32-characters-long",
    )

    limiter = FailureLimiter(max_failures=5, window_seconds=300)

    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_login_limiter] = lambda: limiter

    return TestClient(app)


DOC_TEMPLATE = """\
+++
title = "{title}"
classification = "{classification}"
synthetic = true
+++
# Topic
## Section
{body}
"""


@pytest.fixture
def add_document(engine, clean_db, tmp_path):
    """Ingest a one-section test document (with the test embedder)."""

    def add(name: str, title: str, classification: str, body: str) -> None:
        path = tmp_path / name
        path.write_text(
            DOC_TEMPLATE.format(
                title=title,
                classification=classification,
                body=body,
            )
        )
        ingest_file(engine, path, tmp_path, HashEmbedder())

    return add
