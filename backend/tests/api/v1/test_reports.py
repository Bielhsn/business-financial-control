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


def test_financial_report_returns_csv(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    company_id = _create_company(client, owner)

    response = client.get(f"/api/v1/companies/{company_id}/reports/financial.csv", headers=owner)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    assert "lancamentos.csv" in response.headers["content-disposition"]
    assert "Data,Tipo,Categoria" in response.text


def test_sales_report_returns_csv(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    company_id = _create_company(client, owner)

    response = client.get(f"/api/v1/companies/{company_id}/reports/sales.csv", headers=owner)
    assert response.status_code == 200
    assert "vendas.csv" in response.headers["content-disposition"]
    assert "Data,Plataforma,Produto" in response.text


def test_reports_require_membership(client: TestClient) -> None:
    _headers(_register(client, "dono@example.com"))
    outsider = _headers(_register(client, "outro@example.com"))
    # Empresa de outra pessoa não existe para quem não é membro (404).
    response = client.get("/api/v1/companies/nonexistent/reports/financial.csv", headers=outsider)
    assert response.status_code == 404
