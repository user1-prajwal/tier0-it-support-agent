from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from app.db.session import get_engine
from app.main import create_app


def test_ready_is_200_when_the_database_answers():
    response = TestClient(create_app()).get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_ready_is_503_when_the_database_is_down():
    app = create_app()
    # A real engine pointed at a port nothing listens on: a real failure, not a mock.
    dead_engine = create_engine(
        "postgresql+psycopg://nobody:nothing@127.0.0.1:1/none",
        connect_args={"connect_timeout": 2},
    )
    app.dependency_overrides[get_engine] = lambda: dead_engine

    response = TestClient(app).get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}