from pathlib import Path

from fastapi.testclient import TestClient

import app as app_module

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "incidents_100.csv"


def test_analyze_golden_fixture(client: TestClient) -> None:
    with FIXTURE_PATH.open("rb") as handle:
        response = client.post(
            "/api/incidents/analyze",
            files={"file": ("incidents-brasaland.csv", handle, "text/csv")},
        )

    assert response.status_code == 200
    data = response.json()

    assert data["result_id"]
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
        analyze = client.post(
            "/api/incidents/analyze",
            files={"file": ("incidents-brasaland.csv", handle, "text/csv")},
        )

    result_id = analyze.json()["result_id"]
    response = client.get(f"/api/incidents/results/{result_id}/export")

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


def test_export_unknown_result_returns_404(client: TestClient) -> None:
    response = client.get(
        "/api/incidents/results/00000000-0000-0000-0000-000000000000/export"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == app_module.RESULT_NOT_FOUND


def test_analyze_without_file_returns_400(client: TestClient) -> None:
    response = client.post("/api/incidents/analyze")

    assert response.status_code == 400
    assert response.json()["detail"] == "No file uploaded"
