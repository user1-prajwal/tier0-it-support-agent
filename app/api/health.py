import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_engine

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness only: 'the process is up'. It must not touch the database."""
    return {"status": "ok"}


@router.get("/health/ready")
def ready(
    response: Response,
    engine: Annotated[Engine, Depends(get_engine)],
) -> dict[str, str]:
    """Readiness: 'I can do useful work', which here means the database answers."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.warning("database not ready: %s", exc)
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable"}
    return {"status": "ready"}