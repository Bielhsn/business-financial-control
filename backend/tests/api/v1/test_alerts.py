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


def test_fresh_company_has_no_alerts(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    company_id = _create_company(client, owner)
    response = client.get(f"/api/v1/companies/{company_id}/alerts", headers=owner)
    assert response.status_code == 200
    assert response.json() == []


def test_unreachable_goal_produces_off_track_alert(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    company_id = _create_company(client, owner)
    # Meta de faturamento sem nenhuma receita no mês → projeção 0 < meta → fora do ritmo.
    client.put(
        f"/api/v1/companies/{company_id}/goals/monthly_income",
        json={"target_cents": 500000},
        headers=owner,
    )
    response = client.get(f"/api/v1/companies/{company_id}/alerts", headers=owner)
    assert response.status_code == 200
    codes = {alert["code"] for alert in response.json()}
    assert "goal_off_track_monthly_income" in codes


def test_alerts_require_membership(client: TestClient) -> None:
    outsider = _headers(_register(client, "outro@example.com"))
    response = client.get("/api/v1/companies/nonexistent/alerts", headers=outsider)
    assert response.status_code == 404
