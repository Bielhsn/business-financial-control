from fastapi.testclient import TestClient

from app.api.v1.deps import get_settings
from app.core.config import Settings
from app.main import app

COMPANY = {
    "name": "Loja X",
    "segment": "E-commerce",
    "employee_count": 2,
    "average_customer_count": 100,
    "city": "São Paulo",
    "state": "SP",
    "country": "Brasil",
    "size": "Pequena",
    "tax_regime": None,
    "additional_info": None,
}


def _register(client: TestClient, email: str) -> str:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "s3cr3t!!", "full_name": email.split("@")[0]},
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "s3cr3t!!"})
    return login.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_company(client: TestClient, headers: dict[str, str]) -> str:
    return client.post("/api/v1/companies", json=COMPANY, headers=headers).json()["id"]


def _with_ml_credentials() -> None:
    app.dependency_overrides[get_settings] = lambda: Settings(
        _env_file=None,
        mercadolivre_client_id="ml-id",
        mercadolivre_client_secret="ml-secret",
        public_base_url="https://api.test",
    )


def test_oauth_provider_listed_with_auth_type(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    company_id = _create_company(client, owner)
    available = client.get(
        f"/api/v1/companies/{company_id}/connectors/available", headers=owner
    ).json()["connectors"]
    ml = next(c for c in available if c["provider"] == "mercadolivre")
    assert ml["auth_type"] == "oauth"


def test_authorize_returns_503_without_credentials(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    company_id = _create_company(client, owner)
    response = client.get(
        f"/api/v1/companies/{company_id}/connectors/mercadolivre/oauth/authorize",
        headers=owner,
    )
    assert response.status_code == 503


def test_authorize_returns_url_with_credentials(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    company_id = _create_company(client, owner)
    _with_ml_credentials()

    response = client.get(
        f"/api/v1/companies/{company_id}/connectors/mercadolivre/oauth/authorize",
        headers=owner,
    )
    assert response.status_code == 200
    url = response.json()["authorize_url"]
    assert url.startswith("https://auth.mercadolivre.com.br/authorization?")
    assert "client_id=ml-id" in url
    assert "redirect_uri=https%3A%2F%2Fapi.test%2Fapi%2Fv1%2Fconnectors%2Foauth%2Fcallback" in url
    assert "state=" in url


def test_callback_without_code_redirects_with_error(client: TestClient) -> None:
    response = client.get(
        "/api/v1/connectors/oauth/callback?error=access_denied", follow_redirects=False
    )
    assert response.status_code in (302, 307)
    assert "integration_error=1" in response.headers["location"]


def test_callback_with_invalid_state_redirects_with_error(client: TestClient) -> None:
    response = client.get(
        "/api/v1/connectors/oauth/callback?code=abc&state=forged.state",
        follow_redirects=False,
    )
    assert response.status_code in (302, 307)
    assert "integration_error=1" in response.headers["location"]
