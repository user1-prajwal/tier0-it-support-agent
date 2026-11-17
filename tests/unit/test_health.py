from app.main import create_app
from fastapi.testclient import TestClient


def test_health_is_ok_without_a_database(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}