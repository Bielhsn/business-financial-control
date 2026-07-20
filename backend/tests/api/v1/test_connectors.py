from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.domain.connector.entities import NormalizedSale
from tests.fakes import FakeConnector

VALID_COMPANY_PAYLOAD = {
    "name": "Cursos Online",
    "segment": "Infoprodutos",
    "employee_count": 2,
    "average_customer_count": 500,
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
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _create_company(client: TestClient, headers: dict[str, str]) -> str:
    return client.post("/api/v1/companies", json=VALID_COMPANY_PAYLOAD, headers=headers).json()[
        "id"
    ]


def test_available_connectors_lists_hotmart(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)

    response = client.get(f"/api/v1/companies/{company_id}/connectors/available", headers=headers)

    assert response.status_code == 200
    providers = [c["provider"] for c in response.json()["connectors"]]
    assert "hotmart" in providers
    hotmart = next(c for c in response.json()["connectors"] if c["provider"] == "hotmart")
    assert {f["key"] for f in hotmart["credential_fields"]} == {"client_id", "client_secret"}


def test_connect_and_list_connection(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)

    connect = client.post(
        f"/api/v1/companies/{company_id}/connectors/connect",
        json={
            "provider": "hotmart",
            "credentials": {"client_id": "cid", "client_secret": "secret"},
        },
        headers=headers,
    )
    assert connect.status_code == 201
    assert connect.json()["provider"] == "hotmart"
    assert connect.json()["status"] == "connected"

    listing = client.get(f"/api/v1/companies/{company_id}/connectors/connections", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1
    # Segredos nunca voltam na resposta.
    assert "secret" not in listing.text


def test_connect_rejects_missing_credential(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)

    response = client.post(
        f"/api/v1/companies/{company_id}/connectors/connect",
        json={"provider": "hotmart", "credentials": {"client_id": "cid"}},
        headers=headers,
    )

    assert response.status_code == 422


def test_sync_imports_sales_into_financial(
    client: TestClient, fake_connector: FakeConnector
) -> None:
    fake_connector._sales = [
        NormalizedSale(
            external_id="HP1",
            description="Curso de Python",
            amount_cents=19700,
            occurred_at=datetime(2026, 7, 1, tzinfo=UTC),
        )
    ]
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)
    client.post(
        f"/api/v1/companies/{company_id}/connectors/connect",
        json={
            "provider": "hotmart",
            "credentials": {"client_id": "cid", "client_secret": "secret"},
        },
        headers=headers,
    )

    sync = client.post(f"/api/v1/companies/{company_id}/connectors/hotmart/sync", headers=headers)
    assert sync.status_code == 200
    assert sync.json()["imported"] == 1

    transactions = client.get(
        f"/api/v1/companies/{company_id}/transactions", headers=headers
    ).json()
    assert any(t["amount_cents"] == 19700 and t["status"] == "paid" for t in transactions)


def test_disconnect_removes_connection(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, headers)
    client.post(
        f"/api/v1/companies/{company_id}/connectors/connect",
        json={
            "provider": "hotmart",
            "credentials": {"client_id": "cid", "client_secret": "secret"},
        },
        headers=headers,
    )

    delete = client.delete(f"/api/v1/companies/{company_id}/connectors/hotmart", headers=headers)
    assert delete.status_code == 204

    listing = client.get(f"/api/v1/companies/{company_id}/connectors/connections", headers=headers)
    assert listing.json() == []


def test_connectors_require_company_membership(client: TestClient) -> None:
    owner_headers = _auth_header(client, "dono@example.com")
    company_id = _create_company(client, owner_headers)
    outsider_headers = _auth_header(client, "outra@example.com")

    response = client.get(
        f"/api/v1/companies/{company_id}/connectors/connections", headers=outsider_headers
    )
    assert response.status_code == 404
