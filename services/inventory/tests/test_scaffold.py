from fastapi.testclient import TestClient

from app import app


def test_root_returns_service_name() -> None:
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"service": "inventory"}
