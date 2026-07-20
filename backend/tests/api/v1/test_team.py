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


def test_owner_is_listed_as_member(client: TestClient) -> None:
    headers = _headers(_register(client, "dono@example.com"))
    company_id = _create_company(client, headers)

    members = client.get(f"/api/v1/companies/{company_id}/members", headers=headers).json()
    assert len(members) == 1
    assert members[0]["role"] == "owner"
    assert members[0]["email"] == "dono@example.com"


def test_invite_existing_user_adds_member_directly(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    _register(client, "maria@example.com")  # já tem conta
    company_id = _create_company(client, owner)

    response = client.post(
        f"/api/v1/companies/{company_id}/invitations",
        json={"email": "maria@example.com", "role": "manager"},
        headers=owner,
    )
    assert response.status_code == 201
    assert response.json() is None  # virou membro direto, sem convite pendente

    members = client.get(f"/api/v1/companies/{company_id}/members", headers=owner).json()
    assert {m["email"] for m in members} == {"dono@example.com", "maria@example.com"}


def test_invite_new_email_creates_pending_invitation_then_accept(
    client: TestClient, fake_email_sender: object
) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    company_id = _create_company(client, owner)

    invite = client.post(
        f"/api/v1/companies/{company_id}/invitations",
        json={"email": "novo@example.com", "role": "employee"},
        headers=owner,
    )
    assert invite.status_code == 201
    body = invite.json()
    assert body is not None and body["status"] == "pending"

    pending = client.get(f"/api/v1/companies/{company_id}/invitations", headers=owner).json()
    assert len(pending) == 1

    # O token é enviado por e-mail (não vem na resposta da API, por segurança).
    invite_body = fake_email_sender.sent[-1].body  # type: ignore[attr-defined]
    token = invite_body.rsplit(":", 1)[1].strip()

    invited = _headers(_register(client, "novo@example.com"))
    accept = client.post("/api/v1/invitations/accept", json={"token": token}, headers=invited)
    assert accept.status_code == 200
    assert accept.json()["role"] == "employee"

    members = client.get(f"/api/v1/companies/{company_id}/members", headers=owner).json()
    assert "novo@example.com" in {m["email"] for m in members}


def test_change_role_and_remove_member(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    _register(client, "maria@example.com")
    company_id = _create_company(client, owner)
    client.post(
        f"/api/v1/companies/{company_id}/invitations",
        json={"email": "maria@example.com", "role": "employee"},
        headers=owner,
    )
    members = client.get(f"/api/v1/companies/{company_id}/members", headers=owner).json()
    maria_id = next(m["user_id"] for m in members if m["email"] == "maria@example.com")

    changed = client.patch(
        f"/api/v1/companies/{company_id}/members/{maria_id}",
        json={"role": "admin"},
        headers=owner,
    )
    assert changed.status_code == 200
    assert changed.json()["role"] == "admin"

    removed = client.delete(f"/api/v1/companies/{company_id}/members/{maria_id}", headers=owner)
    assert removed.status_code == 204
    members = client.get(f"/api/v1/companies/{company_id}/members", headers=owner).json()
    assert "maria@example.com" not in {m["email"] for m in members}


def test_cannot_remove_last_owner(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    company_id = _create_company(client, owner)
    members = client.get(f"/api/v1/companies/{company_id}/members", headers=owner).json()
    owner_id = members[0]["user_id"]

    response = client.delete(f"/api/v1/companies/{company_id}/members/{owner_id}", headers=owner)
    assert response.status_code == 422


def test_export_company_data(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    company_id = _create_company(client, owner)

    response = client.get(f"/api/v1/companies/{company_id}/export", headers=owner)
    assert response.status_code == 200
    assert "company" in response.json()


def test_delete_company_requires_owner_and_erases(
    client: TestClient, fake_company_data_service: object
) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    company_id = _create_company(client, owner)

    response = client.delete(f"/api/v1/companies/{company_id}", headers=owner)
    assert response.status_code == 204
    assert company_id in fake_company_data_service.erased  # type: ignore[attr-defined]


def test_export_forbidden_for_non_owner(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    manager = _register(client, "maria@example.com")
    company_id = _create_company(client, owner)
    client.post(
        f"/api/v1/companies/{company_id}/invitations",
        json={"email": "maria@example.com", "role": "manager"},
        headers=owner,
    )

    response = client.get(f"/api/v1/companies/{company_id}/export", headers=_headers(manager))
    assert response.status_code == 403
