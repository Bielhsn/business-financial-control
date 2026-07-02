from datetime import UTC, datetime, timedelta

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


def test_generate_insights_returns_ai_insights(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)
    now = datetime.now(UTC)

    response = client.post(
        f"/api/v1/companies/{company_id}/insights",
        json={
            "start": (now - timedelta(days=30)).isoformat(),
            "end": now.isoformat(),
        },
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["insights"]) == 2
    assert body["insights"][0]["kind"] == "highlight"
    assert body["insights"][1]["kind"] == "warning"


@pytest.mark.anyio
async def test_generate_insights_forbidden_for_employee_role(
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
    now = datetime.now(UTC)

    response = client.post(
        f"/api/v1/companies/{company_id}/insights",
        json={
            "start": (now - timedelta(days=30)).isoformat(),
            "end": now.isoformat(),
        },
        headers=employee_headers,
    )

    assert response.status_code == 403


def test_generate_insights_rejects_invalid_period(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)
    now = datetime.now(UTC)

    response = client.post(
        f"/api/v1/companies/{company_id}/insights",
        json={
            "start": now.isoformat(),
            "end": (now - timedelta(days=1)).isoformat(),
        },
        headers=headers,
    )

    assert response.status_code == 422
