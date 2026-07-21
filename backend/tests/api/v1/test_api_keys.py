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


def _upgrade_enterprise(client: TestClient, company_id: str, headers: dict[str, str]) -> None:
    client.put(
        f"/api/v1/companies/{company_id}/subscription",
        json={"tier": "enterprise"},
        headers=headers,
    )


def test_create_requires_api_access_feature(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    company_id = _create_company(client, owner)
    # Starter não inclui API → 402.
    response = client.post(
        f"/api/v1/companies/{company_id}/api-keys",
        json={"name": "Minha chave"},
        headers=owner,
    )
    assert response.status_code == 402


def test_create_list_and_revoke_on_enterprise(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    company_id = _create_company(client, owner)
    _upgrade_enterprise(client, company_id, owner)

    created = client.post(
        f"/api/v1/companies/{company_id}/api-keys",
        json={"name": "Integração externa"},
        headers=owner,
    )
    assert created.status_code == 201
    body = created.json()
    assert body["raw_key"].startswith("aur_")
    assert body["prefix"].startswith("aur_")
    key_id = body["id"]

    listed = client.get(f"/api/v1/companies/{company_id}/api-keys", headers=owner).json()
    assert len(listed) == 1
    assert "raw_key" not in listed[0]  # a chave crua nunca reaparece

    revoked = client.delete(f"/api/v1/companies/{company_id}/api-keys/{key_id}", headers=owner)
    assert revoked.status_code == 204


def test_public_summary_authenticated_by_key(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    company_id = _create_company(client, owner)
    _upgrade_enterprise(client, company_id, owner)
    raw_key = client.post(
        f"/api/v1/companies/{company_id}/api-keys",
        json={"name": "k"},
        headers=owner,
    ).json()["raw_key"]

    response = client.get("/api/v1/public/v1/summary", headers={"X-API-Key": raw_key})
    assert response.status_code == 200
    body = response.json()
    assert "health_score" in body
    assert "month_net_cents" in body


def test_public_summary_rejects_missing_or_bad_key(client: TestClient) -> None:
    assert client.get("/api/v1/public/v1/summary").status_code == 401
    assert (
        client.get("/api/v1/public/v1/summary", headers={"X-API-Key": "aur_invalida"}).status_code
        == 401
    )


def test_revoked_key_stops_working(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    company_id = _create_company(client, owner)
    _upgrade_enterprise(client, company_id, owner)
    created = client.post(
        f"/api/v1/companies/{company_id}/api-keys", json={"name": "k"}, headers=owner
    ).json()
    raw_key = created["raw_key"]

    client.delete(f"/api/v1/companies/{company_id}/api-keys/{created['id']}", headers=owner)

    response = client.get("/api/v1/public/v1/summary", headers={"X-API-Key": raw_key})
    assert response.status_code == 401
