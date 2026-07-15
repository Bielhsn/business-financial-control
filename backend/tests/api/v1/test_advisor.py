from fastapi.testclient import TestClient

VALID_COMPANY_PAYLOAD = {
    "name": "Loja da Ana",
    "segment": "Loja de roupas",
    "employee_count": 2,
    "average_customer_count": 80,
    "city": "Curitiba",
    "state": "PR",
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


def test_signals_empty_for_new_company(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)

    response = client.get(f"/api/v1/companies/{company_id}/advisor/signals", headers=headers)

    assert response.status_code == 200
    assert response.json() == {"signals": []}


def test_signals_flag_zero_stock_product(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)
    client.post(
        f"/api/v1/companies/{company_id}/catalog-items",
        json={
            "name": "Camiseta",
            "price_cents": 7990,
            "kind": "product",
            "tracks_inventory": True,
            "stock_quantity": 0,
        },
        headers=headers,
    )

    response = client.get(f"/api/v1/companies/{company_id}/advisor/signals", headers=headers)

    assert response.status_code == 200
    signals = response.json()["signals"]
    assert len(signals) == 1
    assert signals[0]["kind"] == "stock_zero"
    assert signals[0]["severity"] == "critical"
    assert "Camiseta" in signals[0]["title"]


def test_recommendations_return_ai_narrative_with_signals(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)
    client.post(
        f"/api/v1/companies/{company_id}/catalog-items",
        json={
            "name": "Camiseta",
            "price_cents": 7990,
            "kind": "product",
            "tracks_inventory": True,
            "stock_quantity": 0,
        },
        headers=headers,
    )

    response = client.post(
        f"/api/v1/companies/{company_id}/advisor/recommendations", headers=headers
    )

    assert response.status_code == 200
    body = response.json()
    assert "Reponha o estoque" in body["recommendations"]
    assert body["signals"][0]["kind"] == "stock_zero"


def test_signals_require_management_role(client: TestClient) -> None:
    owner_headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, owner_headers)
    outsider_headers = _auth_header(client, "outra@example.com")

    response = client.get(
        f"/api/v1/companies/{company_id}/advisor/signals", headers=outsider_headers
    )

    # Não-membros recebem 404 (não 403) para não revelar que a empresa existe.
    assert response.status_code == 404
