from functools import lru_cache

from sqlalchemy import Engine, create_engine

from app.config import Settings


@lru_cache
def get_engine() -> Engine:
    """One engine (one connection pool) per process, built from Settings."""
    return create_engine(Settings().database_url.get_secret_value(), pool_pre_ping=True)