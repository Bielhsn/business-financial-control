import pytest
from fastapi.testclient import TestClient

from app.domain.company.roles import CompanyRole
from tests.fakes import FakeCompanyMembershipRepository, FakeUserRepository

COMPANIES_URL = "/api/v1/companies"

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
    "additional_info": "Atende só com hora marcada.",
}


def _auth_header(client: TestClient, email: str, password: str = "s3cr3t!!") -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Usuário Teste"},
    )
    login_response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    access_token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


def test_create_company_makes_the_creator_the_owner(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")

    response = client.post(COMPANIES_URL, json=VALID_COMPANY_PAYLOAD, headers=headers)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Barbearia do Zé"
    assert body["segment"] == "Barbearia"

    list_response = client.get(COMPANIES_URL, headers=headers)
    assert list_response.status_code == 200
    companies = list_response.json()
    assert len(companies) == 1
    assert companies[0]["role"] == "owner"
    assert companies[0]["company"]["id"] == body["id"]


def test_create_company_rejects_invalid_payload(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    invalid_payload = {**VALID_COMPANY_PAYLOAD, "employee_count": -1}

    response = client.post(COMPANIES_URL, json=invalid_payload, headers=headers)

    assert response.status_code == 422


def test_get_company_returns_data_for_a_member(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = client.post(COMPANIES_URL, json=VALID_COMPANY_PAYLOAD, headers=headers).json()[
        "id"
    ]

    response = client.get(f"{COMPANIES_URL}/{company_id}", headers=headers)

    assert response.status_code == 200
    assert response.json()["id"] == company_id


def test_get_company_hides_existence_from_non_members(client: TestClient) -> None:
    owner_headers = _auth_header(client, "dono@example.com")
    company_id = client.post(
        COMPANIES_URL, json=VALID_COMPANY_PAYLOAD, headers=owner_headers
    ).json()["id"]

    outsider_headers = _auth_header(client, "estranho@example.com")
    response = client.get(f"{COMPANIES_URL}/{company_id}", headers=outsider_headers)

    assert response.status_code == 404


def test_get_unknown_company_returns_404(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")

    response = client.get(f"{COMPANIES_URL}/does-not-exist", headers=headers)

    assert response.status_code == 404


def test_update_company_allowed_for_owner(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = client.post(COMPANIES_URL, json=VALID_COMPANY_PAYLOAD, headers=headers).json()[
        "id"
    ]

    response = client.patch(
        f"{COMPANIES_URL}/{company_id}", json={"name": "Novo Nome"}, headers=headers
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Novo Nome"


@pytest.mark.anyio
async def test_update_company_forbidden_for_insufficient_role(
    client: TestClient,
    fake_user_repository: FakeUserRepository,
    fake_company_membership_repository: FakeCompanyMembershipRepository,
) -> None:
    owner_headers = _auth_header(client, "dono@example.com")
    company_id = client.post(
        COMPANIES_URL, json=VALID_COMPANY_PAYLOAD, headers=owner_headers
    ).json()["id"]

    viewer_headers = _auth_header(client, "visitante@example.com")
    viewer_user = await fake_user_repository.get_by_email("visitante@example.com")
    assert viewer_user is not None
    await fake_company_membership_repository.create(
        company_id=company_id, user_id=viewer_user.id, role=CompanyRole.VIEWER
    )

    response = client.patch(
        f"{COMPANIES_URL}/{company_id}", json={"name": "Tentativa"}, headers=viewer_headers
    )

    assert response.status_code == 403


def test_create_company_with_onboarding_v2_fields(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")

    response = client.post(
        "/api/v1/companies",
        json={
            **VALID_COMPANY_PAYLOAD,
            "currency": "usd",
            "sales_channels": ["Loja física", "Delivery/apps", " "],
            "sales_mode": "Agendamento",
            "main_offerings": "Cortes, barba e venda de pomadas",
        },
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["currency"] == "USD"  # normalizada para maiúsculas
    assert body["sales_channels"] == ["Loja física", "Delivery/apps"]  # vazios descartados
    assert body["sales_mode"] == "Agendamento"
    assert body["main_offerings"] == "Cortes, barba e venda de pomadas"


def test_create_company_defaults_to_brl_currency(client: TestClient) -> None:
    headers = _auth_header(client, "dono2@example.com")

    response = client.post("/api/v1/companies", json=VALID_COMPANY_PAYLOAD, headers=headers)

    assert response.status_code == 201
    assert response.json()["currency"] == "BRL"
    assert response.json()["sales_channels"] == []


def test_update_company_branding(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = client.post(
        "/api/v1/companies", json=VALID_COMPANY_PAYLOAD, headers=headers
    ).json()["id"]

    response = client.patch(
        f"/api/v1/companies/{company_id}",
        json={
            "brand_logo": "data:image/png;base64,iVBORw0KGgo=",
            "brand_primary_color": "#B45309",
            "brand_theme": "dark",
        },
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["brand_primary_color"] == "#B45309"
    assert body["brand_theme"] == "dark"
    assert body["brand_logo"].startswith("data:image/")


def test_update_company_client_return_message(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = client.post(
        "/api/v1/companies", json=VALID_COMPANY_PAYLOAD, headers=headers
    ).json()["id"]

    # Nova empresa começa sem mensagem própria (o frontend usa o texto padrão).
    created = client.get(f"/api/v1/companies/{company_id}", headers=headers).json()
    assert created["client_return_message"] is None

    response = client.patch(
        f"/api/v1/companies/{company_id}",
        json={"client_return_message": "Fala {nome}! Bora dar um trato no visual?"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["client_return_message"] == "Fala {nome}! Bora dar um trato no visual?"


def test_update_company_branding_rejects_invalid_values(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = client.post(
        "/api/v1/companies", json=VALID_COMPANY_PAYLOAD, headers=headers
    ).json()["id"]

    bad_color = client.patch(
        f"/api/v1/companies/{company_id}",
        json={"brand_primary_color": "dourado"},
        headers=headers,
    )
    assert bad_color.status_code == 422

    not_an_image = client.patch(
        f"/api/v1/companies/{company_id}",
        json={"brand_logo": "data:text/html;base64,PGh0bWw+"},
        headers=headers,
    )
    assert not_an_image.status_code == 422


def test_segment_profile_adapts_to_business(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    company_id = client.post(
        "/api/v1/companies", json=VALID_COMPANY_PAYLOAD, headers=headers
    ).json()["id"]

    response = client.get(f"/api/v1/companies/{company_id}/segment-profile", headers=headers)

    assert response.status_code == 200
    body = response.json()
    # VALID_COMPANY_PAYLOAD é uma barbearia.
    assert body["id"] == "barbershop"
    assert body["terminology"]["employees"] == "Profissionais"
    assert "appointments" in body["modules"]
    # Barbearia não deve pedir SKU num corte de cabelo.
    assert body["catalog_fields"]["sku"] is False
    assert "Corte de cabelo" in body["service_examples"]


def test_segment_profile_differs_for_another_segment(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    payload = {**VALID_COMPANY_PAYLOAD, "name": "Adega Central", "segment": "Loja de bebidas"}
    company_id = client.post("/api/v1/companies", json=payload, headers=headers).json()["id"]

    body = client.get(f"/api/v1/companies/{company_id}/segment-profile", headers=headers).json()

    assert body["id"] == "beverage_store"
    assert body["sells_services"] is False
    # Nada de agenda de barbeiro numa loja de bebidas.
    assert "appointments" not in body["modules"]
    assert "Cervejas" in body["catalog_categories"]
