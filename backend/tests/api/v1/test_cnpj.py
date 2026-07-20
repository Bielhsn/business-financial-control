from fastapi.testclient import TestClient


def _auth_header(client: TestClient, email: str = "dono@example.com") -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "s3cr3t!!", "full_name": "Usuário Teste"},
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "s3cr3t!!"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_lookup_valid_cnpj_returns_autofill_data(client: TestClient) -> None:
    headers = _auth_header(client)

    # O cliente envia apenas dígitos (o frontend normaliza antes de chamar).
    response = client.get("/api/v1/cnpj/11222333000181", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["legal_name"] == "Empresa Exemplo LTDA"
    assert body["is_active"] is True
    assert body["state"] == "SP"


def test_lookup_invalid_cnpj_returns_422_without_calling_source(client: TestClient) -> None:
    headers = _auth_header(client)

    response = client.get("/api/v1/cnpj/11222333000180", headers=headers)

    assert response.status_code == 422


def test_lookup_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/cnpj/11222333000181")
    assert response.status_code == 401


def test_create_company_with_valid_cnpj(client: TestClient) -> None:
    headers = _auth_header(client)

    response = client.post(
        "/api/v1/companies",
        json={
            "name": "Minha Empresa",
            "segment": "Infoprodutos",
            "employee_count": 1,
            "average_customer_count": 10,
            "city": "São Paulo",
            "state": "SP",
            "country": "Brasil",
            "size": "Pequena",
            "tax_regime": "Simples Nacional",
            "additional_info": None,
            "legal_name": "Minha Empresa LTDA",
            "cnpj": "11.222.333/0001-81",
            "monthly_revenue_cents": 5000000,
            "phone": "1133224455",
        },
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    # CNPJ é normalizado (só dígitos) ao persistir.
    assert body["cnpj"] == "11222333000181"
    assert body["legal_name"] == "Minha Empresa LTDA"
    assert body["monthly_revenue_cents"] == 5000000


def test_create_company_rejects_invalid_cnpj(client: TestClient) -> None:
    headers = _auth_header(client)

    response = client.post(
        "/api/v1/companies",
        json={
            "name": "Minha Empresa",
            "segment": "Infoprodutos",
            "employee_count": 1,
            "average_customer_count": 10,
            "city": "São Paulo",
            "state": "SP",
            "country": "Brasil",
            "size": "Pequena",
            "tax_regime": None,
            "additional_info": None,
            "cnpj": "11222333000180",
        },
        headers=headers,
    )

    assert response.status_code == 422
