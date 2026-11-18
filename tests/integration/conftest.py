from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from app.db.session import get_engine

ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"


@pytest.fixture(scope="session")
def engine():
    """Migrate the database to the latest version, then hand out the engine.

    Tests run on the real migrated schema, the same path a fresh machine takes.
    """
    command.upgrade(Config(str(ALEMBIC_INI)), "head")
    return get_engine()