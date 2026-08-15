from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app as app_module

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "incidents_100.csv"


@pytest.fixture
def client(auth_headers: dict[str, str]) -> TestClient:
    app_module._last_analysis = None
    with TestClient(app_module.app, headers=auth_headers) as test_client:
        yield test_client


def test_analyze_golden_fixture(client: TestClient) -> None:
    with FIXTURE_PATH.open("rb") as handle:
        response = client.post(
            "/api/incidents/analyze",
            files={"file": ("incidents-brasaland.csv", handle, "text/csv")},
        )

    assert response.status_code == 200
    data = response.json()

    assert data["totals"]["total"] == 100
    assert data["totals"]["valid"] == 96
    assert data["totals"]["invalid"] == 4
    assert data["average_satisfaction_closed"] == 3.46
    assert data["satisfaction_distribution"] == {
        "1": 4,
        "2": 6,
        "3": 12,
        "4": 19,
        "5": 9,
    }


def test_export_after_analyze(client: TestClient) -> None:
    with FIXTURE_PATH.open("rb") as handle:
        client.post(
            "/api/incidents/analyze",
            files={"file": ("incidents-brasaland.csv", handle, "text/csv")},
        )

    response = client.get("/api/incidents/results/export")

    assert response.status_code == 200
    assert response.headers["content-disposition"].startswith("attachment")
    assert response.text.startswith("metric,value,percentage")


def test_analyze_empty_file_returns_400(client: TestClient) -> None:
    response = client.post(
        "/api/incidents/analyze",
        files={"file": ("empty.csv", b"", "text/csv")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "The CSV file is empty"


def test_export_before_analyze_returns_404(client: TestClient) -> None:
    response = client.get("/api/incidents/results/export")

    assert response.status_code == 404
    assert response.json()["detail"] == "No analysis available yet"


def test_analyze_without_file_returns_400(client: TestClient) -> None:
    response = client.post("/api/incidents/analyze")

    assert response.status_code == 400
    assert response.json()["detail"] == "No file uploaded"
