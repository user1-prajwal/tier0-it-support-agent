from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness only: 'the process is up'. It must not touch the database."""
    return {"status": "ok"}