from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.domain.company.roles import CompanyRole
from tests.fakes import FakeAIProvider, FakeCompanyMembershipRepository, FakeUserRepository

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


def _create_category(
    client: TestClient,
    headers: dict[str, str],
    company_id: str,
    name: str = "Vendas",
    type_: str = "income",
) -> str:
    response = client.post(
        f"/api/v1/companies/{company_id}/financial-categories",
        json={"name": name, "type": type_},
        headers=headers,
    )
    return response.json()["id"]


def test_create_and_list_financial_categories(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)

    create_response = client.post(
        f"/api/v1/companies/{company_id}/financial-categories",
        json={"name": "Venda de serviços", "type": "income"},
        headers=headers,
    )
    assert create_response.status_code == 201
    assert create_response.json()["name"] == "Venda de serviços"

    list_response = client.get(
        f"/api/v1/companies/{company_id}/financial-categories", headers=headers
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_create_category_rejects_duplicate_name_and_type(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)
    _create_category(client, headers, company_id)

    response = client.post(
        f"/api/v1/companies/{company_id}/financial-categories",
        json={"name": "Vendas", "type": "income"},
        headers=headers,
    )

    assert response.status_code == 409


@pytest.mark.anyio
async def test_create_category_forbidden_for_employee_role(
    client: TestClient,
    fake_user_repository: FakeUserRepository,
    fake_company_membership_repository: FakeCompanyMembershipRepository,
) -> None:
    owner_headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, owner_headers)

    employee_headers = _auth_header(client, "funcionario@example.com")
    employee = await fake_user_repository.get_by_email("funcionario@example.com")
    assert employee is not None
    await fake_company_membership_repository.create(
        company_id=company_id, user_id=employee.id, role=CompanyRole.EMPLOYEE
    )

    response = client.post(
        f"/api/v1/companies/{company_id}/financial-categories",
        json={"name": "Vendas", "type": "income"},
        headers=employee_headers,
    )

    assert response.status_code == 403


def test_update_category(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)
    category_id = _create_category(client, headers, company_id)

    response = client.patch(
        f"/api/v1/companies/{company_id}/financial-categories/{category_id}",
        json={"is_active": False},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_seed_categories_from_blueprint(
    client: TestClient, fake_ai_provider: FakeAIProvider
) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)
    client.post(f"/api/v1/companies/{company_id}/blueprint", json={}, headers=headers)

    response = client.post(
        f"/api/v1/companies/{company_id}/financial-categories/seed-from-blueprint",
        headers=headers,
    )

    assert response.status_code == 201
    names = {item["name"] for item in response.json()}
    assert names == {"Vendas"}


def test_seed_categories_returns_404_without_a_blueprint(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)

    response = client.post(
        f"/api/v1/companies/{company_id}/financial-categories/seed-from-blueprint",
        headers=headers,
    )

    assert response.status_code == 404


def test_create_and_list_transactions(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)
    category_id = _create_category(client, headers, company_id)

    response = client.post(
        f"/api/v1/companies/{company_id}/transactions",
        json={
            "category_id": category_id,
            "type": "income",
            "amount_cents": 15000,
            "description": "Corte de cabelo",
        },
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert body["amount_cents"] == 15000

    list_response = client.get(f"/api/v1/companies/{company_id}/transactions", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_create_transaction_rejects_mismatched_category_type(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)
    category_id = _create_category(client, headers, company_id, type_="expense")

    response = client.post(
        f"/api/v1/companies/{company_id}/transactions",
        json={
            "category_id": category_id,
            "type": "income",
            "amount_cents": 1000,
            "description": "X",
        },
        headers=headers,
    )

    assert response.status_code == 422


def test_mark_transaction_paid(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)
    category_id = _create_category(client, headers, company_id)
    transaction_id = client.post(
        f"/api/v1/companies/{company_id}/transactions",
        json={
            "category_id": category_id,
            "type": "income",
            "amount_cents": 15000,
            "description": "Corte de cabelo",
        },
        headers=headers,
    ).json()["id"]

    response = client.post(
        f"/api/v1/companies/{company_id}/transactions/{transaction_id}/mark-paid",
        json={},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "paid"


def test_cancel_transaction(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)
    category_id = _create_category(client, headers, company_id)
    transaction_id = client.post(
        f"/api/v1/companies/{company_id}/transactions",
        json={
            "category_id": category_id,
            "type": "income",
            "amount_cents": 15000,
            "description": "Corte de cabelo",
        },
        headers=headers,
    ).json()["id"]

    response = client.post(
        f"/api/v1/companies/{company_id}/transactions/{transaction_id}/cancel", headers=headers
    )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_cannot_cancel_a_paid_transaction(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)
    category_id = _create_category(client, headers, company_id)
    transaction_id = client.post(
        f"/api/v1/companies/{company_id}/transactions",
        json={
            "category_id": category_id,
            "type": "income",
            "amount_cents": 15000,
            "description": "Corte de cabelo",
        },
        headers=headers,
    ).json()["id"]
    client.post(
        f"/api/v1/companies/{company_id}/transactions/{transaction_id}/mark-paid",
        json={},
        headers=headers,
    )

    response = client.post(
        f"/api/v1/companies/{company_id}/transactions/{transaction_id}/cancel", headers=headers
    )

    assert response.status_code == 409


def test_update_transaction(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)
    category_id = _create_category(client, headers, company_id)
    transaction_id = client.post(
        f"/api/v1/companies/{company_id}/transactions",
        json={
            "category_id": category_id,
            "type": "income",
            "amount_cents": 15000,
            "description": "Corte de cabelo",
        },
        headers=headers,
    ).json()["id"]

    response = client.patch(
        f"/api/v1/companies/{company_id}/transactions/{transaction_id}",
        json={"description": "Corte + barba"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["description"] == "Corte + barba"


def test_update_unknown_transaction_returns_404(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)

    response = client.patch(
        f"/api/v1/companies/{company_id}/transactions/does-not-exist",
        json={"description": "X"},
        headers=headers,
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_transactions_forbidden_for_viewer_role(
    client: TestClient,
    fake_company_membership_repository: FakeCompanyMembershipRepository,
    fake_user_repository: FakeUserRepository,
) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)
    category_id = _create_category(client, headers, company_id)

    viewer_headers = _auth_header(client, "visitante@example.com")
    viewer = await fake_user_repository.get_by_email("visitante@example.com")
    assert viewer is not None
    await fake_company_membership_repository.create(
        company_id=company_id, user_id=viewer.id, role=CompanyRole.VIEWER
    )

    response = client.post(
        f"/api/v1/companies/{company_id}/transactions",
        json={
            "category_id": category_id,
            "type": "income",
            "amount_cents": 1000,
            "description": "X",
        },
        headers=viewer_headers,
    )

    assert response.status_code == 403


def test_get_cash_flow_summary(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)
    category_id = _create_category(client, headers, company_id)
    now = datetime.now(UTC)
    client.post(
        f"/api/v1/companies/{company_id}/transactions",
        json={
            "category_id": category_id,
            "type": "income",
            "amount_cents": 15000,
            "description": "Corte de cabelo",
            "paid_at": now.isoformat(),
        },
        headers=headers,
    )

    response = client.get(
        f"/api/v1/companies/{company_id}/cash-flow",
        params={
            "start": (now - timedelta(days=1)).isoformat(),
            "end": (now + timedelta(days=1)).isoformat(),
        },
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["income_cents"] == 15000
    assert body["balance_cents"] == 15000
