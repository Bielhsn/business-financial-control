from fastapi.testclient import TestClient

from app.api.v1 import deps
from app.main import app
from tests.fakes import FakeAIProvider

VALID_COMPANY_PAYLOAD = {
    "name": "Barbearia do Zé",
    "segment": "Barbearia",
    "employee_count": 3,
    "average_customer_count": 120,
    "city": "São Paulo",
    "state": "SP",
    "country": "Brasil",
    "size": "Pequena",
    "tax_regime": "Simples Nacional",
    "additional_info": "Atende só com hora marcada.",
}


def _auth_header(client: TestClient, email: str, password: str = "s3cr3t!!") -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Usuário Teste"},
    )
    login_response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    access_token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


def _create_company(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post("/api/v1/companies", json=VALID_COMPANY_PAYLOAD, headers=headers)
    return response.json()["id"]


def _blueprint_url(company_id: str) -> str:
    return f"/api/v1/companies/{company_id}/blueprint"


def test_generate_blueprint_persists_and_returns_the_suggestion(
    client: TestClient, fake_ai_provider: FakeAIProvider
) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)

    response = client.post(
        _blueprint_url(company_id),
        json={"additional_context": "Atende só com hora marcada."},
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["company_id"] == company_id
    assert body["modules"] == ["financial_core", "clients"]
    assert body["ai_provider"] == "anthropic"
    assert len(fake_ai_provider.calls) == 1


def test_generate_blueprint_forbidden_for_non_owner_admin(client: TestClient) -> None:
    owner_headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, owner_headers)

    outsider_headers = _auth_header(client, "estranho@example.com")
    response = client.post(_blueprint_url(company_id), json={}, headers=outsider_headers)

    assert response.status_code == 404


def test_get_blueprint_returns_404_before_generation(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)

    response = client.get(_blueprint_url(company_id), headers=headers)

    assert response.status_code == 404


def test_get_blueprint_returns_the_generated_blueprint(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)
    client.post(_blueprint_url(company_id), json={}, headers=headers)

    response = client.get(_blueprint_url(company_id), headers=headers)

    assert response.status_code == 200
    assert response.json()["company_id"] == company_id


def test_generate_blueprint_returns_503_when_ai_provider_not_configured(
    client: TestClient,
) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)
    del app.dependency_overrides[deps.get_ai_provider]

    response = client.post(_blueprint_url(company_id), json={}, headers=headers)

    assert response.status_code == 503
