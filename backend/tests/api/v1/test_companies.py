import pytest
from fastapi.testclient import TestClient

from app.core.exceptions import ConnectorError, NotFoundError
from app.domain.company.cnpj_lookup import CnpjInfo
from app.domain.company.roles import CompanyRole
from tests.fakes import FakeCnpjLookup, FakeCompanyMembershipRepository, FakeUserRepository

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


def test_new_company_is_seeded_with_segment_categories(client: TestClient) -> None:
    # A empresa nasce com o plano de contas do segmento, sem depender de IA.
    headers = _auth_header(client, "dono@example.com")
    company_id = client.post(
        "/api/v1/companies", json=VALID_COMPANY_PAYLOAD, headers=headers
    ).json()["id"]

    categories = client.get(
        f"/api/v1/companies/{company_id}/financial-categories", headers=headers
    ).json()

    names = {item["name"] for item in categories}
    # Barbearia: receitas e despesas típicas do negócio.
    assert "Serviços" in names
    assert "Comissões" in names
    assert {item["type"] for item in categories} == {"income", "expense"}


def test_seeded_categories_match_the_segment(client: TestClient) -> None:
    headers = _auth_header(client, "dono@example.com")
    payload = {**VALID_COMPANY_PAYLOAD, "name": "Adega Central", "segment": "Loja de bebidas"}
    company_id = client.post("/api/v1/companies", json=payload, headers=headers).json()["id"]

    names = {
        item["name"]
        for item in client.get(
            f"/api/v1/companies/{company_id}/financial-categories", headers=headers
        ).json()
    }

    assert "Compra de mercadorias" in names
    assert "Comissões" not in names  # categoria de barbearia não vaza para cá


# --- Integridade do CNPJ -------------------------------------------------
#
# Dígito verificador prova só que o número é bem formado. Sem consultar a fonte
# externa, o cadastro aceita CNPJ inventado; sem restrição no banco, duas contas
# reivindicam a mesma empresa.

_CNPJ_VALIDO = "19131243000197"  # dígitos verificadores corretos


def test_create_company_rejects_cnpj_that_does_not_exist(
    client: TestClient, fake_cnpj_lookup: FakeCnpjLookup
) -> None:
    async def nao_encontrado(cnpj: str) -> CnpjInfo:
        raise NotFoundError("CNPJ não encontrado na base da Receita.")

    fake_cnpj_lookup.fetch = nao_encontrado  # type: ignore[method-assign]
    headers = _auth_header(client, "dono@example.com")

    response = client.post(
        COMPANIES_URL, json={**VALID_COMPANY_PAYLOAD, "cnpj": _CNPJ_VALIDO}, headers=headers
    )

    assert response.status_code == 422
    assert "não foi encontrado" in response.json()["message"]


def test_create_company_rejects_inactive_cnpj(
    client: TestClient, fake_cnpj_lookup: FakeCnpjLookup
) -> None:
    """Empresa baixada não deve virar conta nova."""

    async def baixada(cnpj: str) -> CnpjInfo:
        return CnpjInfo(
            cnpj=cnpj,
            legal_name="Empresa Baixada LTDA",
            trade_name=None,
            status="BAIXADA",
            is_active=False,
            city="São Paulo",
            state="SP",
            email=None,
            phone=None,
            main_activity=None,
        )

    fake_cnpj_lookup.fetch = baixada  # type: ignore[method-assign]
    headers = _auth_header(client, "dono@example.com")

    response = client.post(
        COMPANIES_URL, json={**VALID_COMPANY_PAYLOAD, "cnpj": _CNPJ_VALIDO}, headers=headers
    )

    assert response.status_code == 422
    assert "BAIXADA" in response.json()["message"]


def test_outage_of_the_source_is_not_reported_as_invalid_cnpj(
    client: TestClient, fake_cnpj_lookup: FakeCnpjLookup
) -> None:
    """Indisponibilidade da Receita é problema temporário. Dizer "CNPJ inválido"
    faria a pessoa conferir números que estão certos."""

    async def fora_do_ar(cnpj: str) -> CnpjInfo:
        raise ConnectorError("Não foi possível consultar a Receita agora.")

    fake_cnpj_lookup.fetch = fora_do_ar  # type: ignore[method-assign]
    headers = _auth_header(client, "dono@example.com")

    response = client.post(
        COMPANIES_URL, json={**VALID_COMPANY_PAYLOAD, "cnpj": _CNPJ_VALIDO}, headers=headers
    )

    assert response.status_code != 422
    assert "inválido" not in response.text.lower()


def test_same_cnpj_cannot_belong_to_two_companies(client: TestClient) -> None:
    primeiro = _auth_header(client, "primeiro@example.com")
    criada = client.post(
        COMPANIES_URL, json={**VALID_COMPANY_PAYLOAD, "cnpj": _CNPJ_VALIDO}, headers=primeiro
    )
    assert criada.status_code == 201

    # Outra conta, mesmo CNPJ.
    segundo = _auth_header(client, "segundo@example.com")
    duplicada = client.post(
        COMPANIES_URL,
        json={**VALID_COMPANY_PAYLOAD, "name": "Outra", "cnpj": _CNPJ_VALIDO},
        headers=segundo,
    )

    assert duplicada.status_code == 409
    assert "já está cadastrado" in duplicada.json()["message"]


def test_companies_without_cnpj_do_not_collide(client: TestClient) -> None:
    """O índice é parcial de propósito: sem o filtro, todas as empresas sem CNPJ
    colidiriam entre si no valor nulo."""
    headers = _auth_header(client, "dono@example.com")

    primeira = client.post(COMPANIES_URL, json=VALID_COMPANY_PAYLOAD, headers=headers)
    segunda = client.post(
        COMPANIES_URL, json={**VALID_COMPANY_PAYLOAD, "name": "Segunda"}, headers=headers
    )

    assert primeira.status_code == 201
    assert segunda.status_code == 201
