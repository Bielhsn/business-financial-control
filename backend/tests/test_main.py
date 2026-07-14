from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_returns_ok() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"name": "business-financial-control-api", "status": "ok"}


@patch("app.api.v1.routers.health.ping_database", new_callable=AsyncMock)
def test_health_check_ok_when_database_reachable(mock_ping: AsyncMock) -> None:
    mock_ping.return_value = True

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


@patch("app.api.v1.routers.health.ping_database", new_callable=AsyncMock)
def test_health_check_reports_unavailable_database(mock_ping: AsyncMock) -> None:
    mock_ping.return_value = False

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "unavailable"}
