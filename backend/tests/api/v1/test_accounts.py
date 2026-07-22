from datetime import UTC, datetime, timedelta

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


def test_accounts_empty(client: TestClient) -> None:
    headers = _auth(client, "dono@example.com")
    company_id = _company(client, headers)
    response = client.get(f"/api/v1/companies/{company_id}/accounts", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["payable"]["total_cents"] == 0
    assert body["receivable"]["total_cents"] == 0


def test_accounts_classifies_pending_transactions(client: TestClient) -> None:
    headers = _auth(client, "dono@example.com")
    company_id = _company(client, headers)
    expense_cat = _category(client, headers, company_id, "expense")
    income_cat = _category(client, headers, company_id, "income")
    now = datetime.now(UTC)

    # Despesa vencida (a pagar).
    client.post(
        f"/api/v1/companies/{company_id}/transactions",
        json={
            "category_id": expense_cat,
            "type": "expense",
            "amount_cents": 5000,
            "description": "Aluguel atrasado",
            "due_date": (now - timedelta(days=3)).isoformat(),
        },
        headers=headers,
    )
    # Receita a vencer em breve (a receber).
    client.post(
        f"/api/v1/companies/{company_id}/transactions",
        json={
            "category_id": income_cat,
            "type": "income",
            "amount_cents": 8000,
            "description": "Cliente a pagar",
            "due_date": (now + timedelta(days=2)).isoformat(),
        },
        headers=headers,
    )

    body = client.get(f"/api/v1/companies/{company_id}/accounts", headers=headers).json()

    assert body["payable"]["overdue_cents"] == 5000
    assert body["payable"]["total_cents"] == 5000
    assert body["payable"]["items"][0]["is_overdue"] is True
    assert body["receivable"]["due_soon_cents"] == 8000
    assert body["receivable"]["total_cents"] == 8000
