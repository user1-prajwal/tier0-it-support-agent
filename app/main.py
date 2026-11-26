from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.auth.deps import get_settings
from app.auth.tokens import require_secret


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Refuse to start with a missing or weak signing secret, not fail later at the first login.
    require_secret(get_settings().jwt_secret)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Tier0 - Permission-Aware IT Support Agent (demo)", lifespan=lifespan)
    app.include_router(health_router)
    app.include_router(auth_router)
    return app


app = create_app()