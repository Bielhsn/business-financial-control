from datetime import UTC, datetime

from fastapi.testclient import TestClient

COMPANY = {
    "name": "Empresa X",
    "segment": "Serviços",
    "employee_count": 3,
    "average_customer_count": 50,
    "city": "São Paulo",
    "state": "SP",
    "country": "Brasil",
    "size": "Pequena",
    "tax_regime": None,
    "additional_info": None,
}


def _auth(client: TestClient, email: str) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "s3cr3t!!", "full_name": "Dono"},
    )
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "s3cr3t!!"}).json()[
        "access_token"
    ]
    return {"Authorization": f"Bearer {token}"}


def _company(client: TestClient, headers: dict[str, str]) -> str:
    return client.post("/api/v1/companies", json=COMPANY, headers=headers).json()["id"]


def _category(client: TestClient, headers: dict[str, str], company_id: str, type_: str) -> str:
    return client.post(
        f"/api/v1/companies/{company_id}/financial-categories",
        json={"name": f"Cat {type_}", "type": type_},
        headers=headers,
    ).json()["id"]


def test_income_statement_empty_month(client: TestClient) -> None:
    headers = _auth(client, "dono@example.com")
    company_id = _company(client, headers)
    response = client.get(f"/api/v1/companies/{company_id}/income-statement", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["current"]["net_result_cents"] == 0
    assert body["income_change_pct"] is None


def test_income_statement_aggregates_current_month(client: TestClient) -> None:
    headers = _auth(client, "dono@example.com")
    company_id = _company(client, headers)
    income_cat = _category(client, headers, company_id, "income")
    expense_cat = _category(client, headers, company_id, "expense")
    now = datetime.now(UTC)

    client.post(
        f"/api/v1/companies/{company_id}/transactions",
        json={
            "category_id": income_cat,
            "type": "income",
            "amount_cents": 20000,
            "description": "Venda",
            "paid_at": now.isoformat(),
        },
        headers=headers,
    )
    client.post(
        f"/api/v1/companies/{company_id}/transactions",
        json={
            "category_id": expense_cat,
            "type": "expense",
            "amount_cents": 7000,
            "description": "Aluguel",
            "paid_at": now.isoformat(),
        },
        headers=headers,
    )

    body = client.get(
        f"/api/v1/companies/{company_id}/income-statement",
        params={"year": now.year, "month": now.month},
        headers=headers,
    ).json()

    assert body["current"]["total_income_cents"] == 20000
    assert body["current"]["total_expense_cents"] == 7000
    assert body["current"]["net_result_cents"] == 13000
    assert body["current"]["income_lines"][0]["amount_cents"] == 20000
