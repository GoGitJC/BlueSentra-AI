from unittest.mock import patch

from backend.app.database.session import check_database_connection


def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "bluesentra-api"
    assert "version" in body
    assert "environment" in body


def test_ready_endpoint_unavailable_returns_503(client):
    with patch(
        "backend.app.api.v1.health.check_database_connection",
        return_value=False,
    ):
        response = client.get("/api/v1/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["database"] == "unavailable"


def test_ready_endpoint_connected_returns_200(client):
    if not check_database_connection():
        import pytest

        pytest.skip("PostgreSQL is not available")

    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["database"] == "connected"
