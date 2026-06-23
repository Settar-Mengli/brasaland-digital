from fastapi.testclient import TestClient

import app as app_module


def test_root_serves_index_html() -> None:
    with TestClient(app_module.app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Centralized Incident Manager" in response.text


def test_static_styles_served() -> None:
    with TestClient(app_module.app) as client:
        response = client.get("/static/styles.css")

    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]
    assert "--ember:" in response.text
