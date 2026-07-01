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
