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


def test_fresh_company_is_neutral(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    company_id = _create_company(client, owner)
    response = client.get(f"/api/v1/companies/{company_id}/analytics/health", headers=owner)
    assert response.status_code == 200
    body = response.json()
    assert body["score"] == 50
    assert body["factors"] == []


def test_health_requires_membership(client: TestClient) -> None:
    outsider = _headers(_register(client, "outro@example.com"))
    response = client.get("/api/v1/companies/nonexistent/analytics/health", headers=outsider)
    assert response.status_code == 404
