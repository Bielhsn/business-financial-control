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


def test_create_service_without_inventory(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)

    response = client.post(
        f"/api/v1/companies/{company_id}/catalog-items",
        json={"name": "Corte de cabelo", "price_cents": 3000, "kind": "service"},
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["kind"] == "service"
    assert body["stock_quantity"] is None


def test_create_product_with_inventory(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)

    response = client.post(
        f"/api/v1/companies/{company_id}/catalog-items",
        json={
            "name": "Shampoo",
            "price_cents": 2500,
            "kind": "product",
            "tracks_inventory": True,
            "stock_quantity": 10,
        },
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["stock_quantity"] == 10


def test_service_rejects_inventory_tracking(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)

    response = client.post(
        f"/api/v1/companies/{company_id}/catalog-items",
        json={
            "name": "Corte de cabelo",
            "price_cents": 3000,
            "kind": "service",
            "tracks_inventory": True,
        },
        headers=headers,
    )

    assert response.status_code == 422


def test_adjust_stock(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)
    item_id = client.post(
        f"/api/v1/companies/{company_id}/catalog-items",
        json={
            "name": "Shampoo",
            "price_cents": 2500,
            "kind": "product",
            "tracks_inventory": True,
            "stock_quantity": 10,
        },
        headers=headers,
    ).json()["id"]

    response = client.post(
        f"/api/v1/companies/{company_id}/catalog-items/{item_id}/adjust-stock",
        json={"delta": -3, "reason": "Venda"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["stock_quantity"] == 7


def test_adjust_stock_rejects_going_negative(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)
    item_id = client.post(
        f"/api/v1/companies/{company_id}/catalog-items",
        json={
            "name": "Shampoo",
            "price_cents": 2500,
            "kind": "product",
            "tracks_inventory": True,
            "stock_quantity": 2,
        },
        headers=headers,
    ).json()["id"]

    response = client.post(
        f"/api/v1/companies/{company_id}/catalog-items/{item_id}/adjust-stock",
        json={"delta": -3, "reason": "Venda"},
        headers=headers,
    )

    assert response.status_code == 422


def test_update_catalog_item(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)
    item_id = client.post(
        f"/api/v1/companies/{company_id}/catalog-items",
        json={"name": "Corte de cabelo", "price_cents": 3000, "kind": "service"},
        headers=headers,
    ).json()["id"]

    response = client.patch(
        f"/api/v1/companies/{company_id}/catalog-items/{item_id}",
        json={"price_cents": 3500},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["price_cents"] == 3500


def test_get_unknown_catalog_item_returns_404(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)

    response = client.get(
        f"/api/v1/companies/{company_id}/catalog-items/does-not-exist", headers=headers
    )

    assert response.status_code == 404
