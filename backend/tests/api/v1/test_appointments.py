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


def test_create_and_list_appointment(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)

    create = client.post(
        f"/api/v1/companies/{company_id}/appointments",
        json={
            "title": "Corte masculino",
            "starts_at": "2026-08-01T14:00:00Z",
            "duration_minutes": 30,
            "price_cents": 4000,
        },
        headers=headers,
    )
    assert create.status_code == 201
    assert create.json()["status"] == "scheduled"

    listing = client.get(
        f"/api/v1/companies/{company_id}/appointments",
        params={"start": "2026-07-31T00:00:00Z", "end": "2026-08-02T00:00:00Z"},
        headers=headers,
    )
    assert listing.status_code == 200
    assert len(listing.json()) == 1


def test_completing_appointment_creates_revenue_transaction(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)
    appointment_id = client.post(
        f"/api/v1/companies/{company_id}/appointments",
        json={
            "title": "Corte + barba",
            "starts_at": "2026-08-01T14:00:00Z",
            "duration_minutes": 45,
            "price_cents": 6000,
        },
        headers=headers,
    ).json()["id"]

    response = client.post(
        f"/api/v1/companies/{company_id}/appointments/{appointment_id}/status",
        json={"status": "completed"},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["revenue_transaction_id"] is not None

    transactions = client.get(
        f"/api/v1/companies/{company_id}/transactions", headers=headers
    ).json()
    assert any(t["amount_cents"] == 6000 and t["status"] == "paid" for t in transactions)


def test_reschedule_appointment(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)
    appointment_id = client.post(
        f"/api/v1/companies/{company_id}/appointments",
        json={
            "title": "Corte",
            "starts_at": "2026-08-01T14:00:00Z",
            "duration_minutes": 30,
        },
        headers=headers,
    ).json()["id"]

    response = client.patch(
        f"/api/v1/companies/{company_id}/appointments/{appointment_id}",
        json={"starts_at": "2026-08-02T10:00:00Z", "duration_minutes": 60},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["starts_at"].startswith("2026-08-02T10:00:00")
    assert body["duration_minutes"] == 60


def test_appointments_require_company_membership(client: TestClient) -> None:
    owner_headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, owner_headers)
    outsider_headers = _auth_header(client, "outra@example.com")

    response = client.get(f"/api/v1/companies/{company_id}/appointments", headers=outsider_headers)

    assert response.status_code == 404
