from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.domain.company.roles import CompanyRole
from tests.fakes import (
    FakeAuditLogRepository,
    FakeCompanyMembershipRepository,
    FakeUserRepository,
)

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
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _create_company(client: TestClient, headers: dict[str, str]) -> str:
    return client.post("/api/v1/companies", json=VALID_COMPANY_PAYLOAD, headers=headers).json()[
        "id"
    ]


def _create_category(client: TestClient, headers: dict[str, str], company_id: str) -> str:
    return client.post(
        f"/api/v1/companies/{company_id}/financial-categories",
        json={"name": "Vendas", "type": "income"},
        headers=headers,
    ).json()["id"]


def test_sensitive_actions_are_persisted_in_audit_trail(
    client: TestClient, fake_audit_log_repository: FakeAuditLogRepository
) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)
    category_id = _create_category(client, headers, company_id)

    client.post(
        f"/api/v1/companies/{company_id}/transactions",
        json={
            "category_id": category_id,
            "type": "income",
            "amount_cents": 15000,
            "description": "Corte",
        },
        headers=headers,
    )

    actions = [entry.action for entry in fake_audit_log_repository.entries]
    assert "transaction_created" in actions

    listing = client.get(f"/api/v1/companies/{company_id}/audit-logs", headers=headers)
    assert listing.status_code == 200
    assert any(item["action"] == "transaction_created" for item in listing.json())


@pytest.mark.anyio
async def test_audit_logs_forbidden_for_manager_role(
    client: TestClient,
    fake_user_repository: FakeUserRepository,
    fake_company_membership_repository: FakeCompanyMembershipRepository,
) -> None:
    owner_headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, owner_headers)

    manager_headers = _auth_header(client, "gerente@example.com")
    manager = await fake_user_repository.get_by_email("gerente@example.com")
    assert manager is not None
    await fake_company_membership_repository.create(
        company_id=company_id, user_id=manager.id, role=CompanyRole.MANAGER
    )

    response = client.get(f"/api/v1/companies/{company_id}/audit-logs", headers=manager_headers)

    assert response.status_code == 403


def test_notifications_lists_overdue_and_due_soon(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)
    category_id = _create_category(client, headers, company_id)
    now = datetime.now(UTC)

    client.post(
        f"/api/v1/companies/{company_id}/transactions",
        json={
            "category_id": category_id,
            "type": "income",
            "amount_cents": 5000,
            "description": "Boleto vencendo",
            "due_date": (now + timedelta(days=3)).isoformat(),
        },
        headers=headers,
    )

    response = client.get(f"/api/v1/companies/{company_id}/notifications", headers=headers)

    assert response.status_code == 200
    [notification] = response.json()
    assert notification["kind"] == "due_soon"
    assert notification["description"] == "Boleto vencendo"
