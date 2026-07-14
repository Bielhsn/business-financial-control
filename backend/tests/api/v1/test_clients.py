import pytest
from fastapi.testclient import TestClient

from app.domain.company.roles import CompanyRole
from tests.fakes import FakeCompanyMembershipRepository, FakeUserRepository

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
    "additional_info": None,
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


def test_create_and_list_clients(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)

    response = client.post(
        f"/api/v1/companies/{company_id}/clients",
        json={"name": "Ana Silva", "email": "ana@example.com"},
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Ana Silva"
    assert response.json()["custom_fields"] == {}

    list_response = client.get(f"/api/v1/companies/{company_id}/clients", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_create_client_rejects_unknown_custom_field(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)

    response = client.post(
        f"/api/v1/companies/{company_id}/clients",
        json={"name": "Ana", "custom_fields": {"unknown": "x"}},
        headers=headers,
    )

    assert response.status_code == 422


def test_get_client_returns_404_for_unknown_id(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)

    response = client.get(f"/api/v1/companies/{company_id}/clients/does-not-exist", headers=headers)

    assert response.status_code == 404


def test_update_client(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)
    client_id = client.post(
        f"/api/v1/companies/{company_id}/clients", json={"name": "Ana"}, headers=headers
    ).json()["id"]

    response = client.patch(
        f"/api/v1/companies/{company_id}/clients/{client_id}",
        json={"notes": "Cliente frequente"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["notes"] == "Cliente frequente"


def test_client_summary_reflects_paid_transactions(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)
    client_id = client.post(
        f"/api/v1/companies/{company_id}/clients", json={"name": "Ana"}, headers=headers
    ).json()["id"]
    category_id = client.post(
        f"/api/v1/companies/{company_id}/financial-categories",
        json={"name": "Vendas", "type": "income"},
        headers=headers,
    ).json()["id"]
    client.post(
        f"/api/v1/companies/{company_id}/transactions",
        json={
            "category_id": category_id,
            "type": "income",
            "amount_cents": 15000,
            "description": "Corte",
            "client_id": client_id,
            "paid_at": "2026-01-01T10:00:00Z",
        },
        headers=headers,
    )

    response = client.get(
        f"/api/v1/companies/{company_id}/clients/{client_id}/summary", headers=headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_spent_cents"] == 15000
    assert body["purchase_count"] == 1


@pytest.mark.anyio
async def test_create_client_forbidden_for_viewer_role(
    client: TestClient,
    fake_user_repository: FakeUserRepository,
    fake_company_membership_repository: FakeCompanyMembershipRepository,
) -> None:
    owner_headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, owner_headers)

    viewer_headers = _auth_header(client, "visitante@example.com")
    viewer = await fake_user_repository.get_by_email("visitante@example.com")
    assert viewer is not None
    await fake_company_membership_repository.create(
        company_id=company_id, user_id=viewer.id, role=CompanyRole.VIEWER
    )

    response = client.post(
        f"/api/v1/companies/{company_id}/clients",
        json={"name": "Ana"},
        headers=viewer_headers,
    )

    assert response.status_code == 403
