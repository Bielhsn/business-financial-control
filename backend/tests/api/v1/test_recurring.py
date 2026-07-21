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


def _new_recurring(company_id: str, client: TestClient, headers: dict[str, str]) -> dict:
    payload = {
        "category_id": "cat-1",
        "type": "expense",
        "amount_cents": 250000,
        "description": "Aluguel",
        "frequency": "monthly",
        "start_date": "2026-07-05T00:00:00Z",
        "notes": "Contrato anual",
    }
    return client.post(
        f"/api/v1/companies/{company_id}/recurring", json=payload, headers=headers
    ).json()


def test_recurring_starts_empty(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    company_id = _create_company(client, owner)
    response = client.get(f"/api/v1/companies/{company_id}/recurring", headers=owner)
    assert response.status_code == 200
    assert response.json() == []


def test_create_recurring_derives_anchor_day(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    company_id = _create_company(client, owner)

    created = _new_recurring(company_id, client, owner)
    assert created["anchor_day"] == 5
    assert created["active"] is True
    assert created["amount_cents"] == 250000
    assert created["next_run_date"].startswith("2026-07-05")


def test_create_rejects_non_positive_amount(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    company_id = _create_company(client, owner)
    response = client.post(
        f"/api/v1/companies/{company_id}/recurring",
        json={
            "category_id": "c",
            "type": "expense",
            "amount_cents": 0,
            "description": "X",
            "frequency": "monthly",
            "start_date": "2026-07-05T00:00:00Z",
        },
        headers=owner,
    )
    assert response.status_code == 422


def test_update_and_delete_recurring(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    company_id = _create_company(client, owner)
    created = _new_recurring(company_id, client, owner)
    recurring_id = created["id"]

    updated = client.put(
        f"/api/v1/companies/{company_id}/recurring/{recurring_id}",
        json={"amount_cents": 300000, "active": False},
        headers=owner,
    )
    assert updated.status_code == 200
    assert updated.json()["amount_cents"] == 300000
    assert updated.json()["active"] is False

    deleted = client.delete(
        f"/api/v1/companies/{company_id}/recurring/{recurring_id}", headers=owner
    )
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/companies/{company_id}/recurring", headers=owner).json() == []


def test_run_generates_pending_transactions(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    company_id = _create_company(client, owner)
    _new_recurring(company_id, client, owner)

    response = client.post(f"/api/v1/companies/{company_id}/recurring/run", headers=owner)
    assert response.status_code == 200
    # start_date (05/07/2026) já venceu em relação a "agora" (2026+), então gera.
    assert response.json()["created"] >= 1


def test_update_missing_returns_404(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    company_id = _create_company(client, owner)
    response = client.put(
        f"/api/v1/companies/{company_id}/recurring/000000000000000000000000",
        json={"amount_cents": 1000},
        headers=owner,
    )
    assert response.status_code == 404
