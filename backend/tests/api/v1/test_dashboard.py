from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

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


def test_get_dashboard_returns_aggregated_summary(client: TestClient) -> None:
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
        f"/api/v1/companies/{company_id}/dashboard",
        params={
            "start": (now - timedelta(days=1)).isoformat(),
            "end": (now + timedelta(days=1)).isoformat(),
        },
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["revenue_cents"] == 15000
    assert body["expense_cents"] == 0
    assert body["profit_cents"] == 15000
    assert body["transaction_count"] == 1
    assert body["kpis"] == []


def test_get_dashboard_returns_not_found_without_company_membership(client: TestClient) -> None:
    owner_headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, owner_headers)
    now = datetime.now(UTC)

    outsider_headers = _auth_header(client, "estranho@example.com")

    response = client.get(
        f"/api/v1/companies/{company_id}/dashboard",
        params={
            "start": (now - timedelta(days=1)).isoformat(),
            "end": now.isoformat(),
        },
        headers=outsider_headers,
    )

    assert response.status_code == 404


def test_get_dashboard_rejects_end_before_start(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)
    now = datetime.now(UTC)

    response = client.get(
        f"/api/v1/companies/{company_id}/dashboard",
        params={
            "start": now.isoformat(),
            "end": (now - timedelta(days=1)).isoformat(),
        },
        headers=headers,
    )

    assert response.status_code == 422


def test_get_dashboard_rejects_months_out_of_range(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)
    now = datetime.now(UTC)

    response = client.get(
        f"/api/v1/companies/{company_id}/dashboard",
        params={
            "start": (now - timedelta(days=1)).isoformat(),
            "end": now.isoformat(),
            "months": 25,
        },
        headers=headers,
    )

    assert response.status_code == 422
