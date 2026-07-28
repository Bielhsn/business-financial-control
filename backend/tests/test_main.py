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


@patch("app.api.v1.routers.health.ping_database", new_callable=AsyncMock)
def test_probes_accept_head(mock_ping: AsyncMock) -> None:
    """Balanceadores e monitores de uptime sondam com HEAD — o health check da
    Render entre eles. O `@app.get` do FastAPI não registra HEAD sozinho (uma
    rota Starlette pura registra), então a sonda levava 405 e enchia o log de
    "Method Not Allowed" num serviço saudável."""
    mock_ping.return_value = True

    assert client.head("/").status_code == 200
    assert client.head("/api/v1/health").status_code == 200


def test_root_still_rejects_methods_that_do_not_apply() -> None:
    """Aceitar HEAD não é abrir a rota: escrever na raiz continua sendo 405."""
    assert client.post("/").status_code == 405
