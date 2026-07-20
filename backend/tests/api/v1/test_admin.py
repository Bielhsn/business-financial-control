from fastapi.testclient import TestClient

from app.api.v1.deps import get_settings
from app.core.config import Settings
from app.main import app


def _register(client: TestClient, email: str) -> str:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "s3cr3t!!", "full_name": email.split("@")[0]},
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "s3cr3t!!"})
    return login.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _make_admin(email: str) -> None:
    app.dependency_overrides[get_settings] = lambda: Settings(
        _env_file=None, platform_admin_emails=email
    )


def test_admin_status_false_for_regular_user(client: TestClient) -> None:
    token = _register(client, "user@example.com")
    response = client.get("/api/v1/admin/me", headers=_headers(token))
    assert response.status_code == 200
    assert response.json()["is_platform_admin"] is False


def test_admin_status_true_for_configured_admin(client: TestClient) -> None:
    token = _register(client, "boss@aurum.com")
    _make_admin("boss@aurum.com")
    response = client.get("/api/v1/admin/me", headers=_headers(token))
    assert response.json()["is_platform_admin"] is True


def test_overview_hidden_from_non_admin(client: TestClient) -> None:
    token = _register(client, "user@example.com")
    response = client.get("/api/v1/admin/overview", headers=_headers(token))
    # 404 (não 403): não revela a existência do painel.
    assert response.status_code == 404


def test_overview_accessible_to_admin(client: TestClient) -> None:
    token = _register(client, "boss@aurum.com")
    _make_admin("boss@aurum.com")
    response = client.get("/api/v1/admin/overview", headers=_headers(token))
    assert response.status_code == 200
    body = response.json()
    assert "revenue" in body
    assert "customers" in body
    assert "subscriptions" in body
    assert "system" in body
    assert body["revenue"]["mrr_cents"] == 0  # sem assinaturas seedadas


def test_overview_requires_auth(client: TestClient) -> None:
    response = client.get("/api/v1/admin/overview")
    assert response.status_code == 401
