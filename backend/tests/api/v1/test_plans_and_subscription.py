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


def test_plan_catalog_is_public(client: TestClient) -> None:
    # O catálogo é público (página de preços pré-login) — sem header de auth.
    response = client.get("/api/v1/plans")
    assert response.status_code == 200
    tiers = [p["tier"] for p in response.json()["plans"]]
    assert tiers == ["starter", "professional", "business", "enterprise"]


def test_plan_catalog_has_prices_and_features(client: TestClient) -> None:
    plans = client.get("/api/v1/plans").json()["plans"]
    professional = next(p for p in plans if p["tier"] == "professional")
    assert professional["price_cents_monthly"] == 4900
    assert "advanced_ai" in professional["features"]
    assert professional["badge"] == "Mais popular"
    enterprise = next(p for p in plans if p["tier"] == "enterprise")
    assert enterprise["is_contact_sales"] is True
    assert enterprise["limits"]["max_members"] == -1


def test_new_company_defaults_to_starter(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    company_id = _create_company(client, owner)

    response = client.get(f"/api/v1/companies/{company_id}/subscription", headers=owner)
    assert response.status_code == 200
    body = response.json()
    assert body["tier"] == "starter"
    assert body["status"] == "active"
    assert body["usage"]["members"] == 1


def test_owner_can_change_plan(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    company_id = _create_company(client, owner)

    response = client.put(
        f"/api/v1/companies/{company_id}/subscription",
        json={"tier": "business", "billing_cycle": "monthly"},
        headers=owner,
    )
    assert response.status_code == 200
    assert response.json()["tier"] == "business"
    assert "white_label" in response.json()["features"]


def test_non_owner_cannot_change_plan(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    _register(client, "maria@example.com")
    company_id = _create_company(client, owner)
    client.post(
        f"/api/v1/companies/{company_id}/invitations",
        json={"email": "maria@example.com", "role": "admin"},
        headers=owner,
    )
    maria = _headers(_register(client, "maria@example.com"))

    response = client.put(
        f"/api/v1/companies/{company_id}/subscription",
        json={"tier": "business"},
        headers=maria,
    )
    assert response.status_code == 403


def test_start_trial_sets_trialing(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    company_id = _create_company(client, owner)

    response = client.put(
        f"/api/v1/companies/{company_id}/subscription",
        json={"tier": "professional", "start_trial": True},
        headers=owner,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "trialing"
    assert body["trial_ends_at"] is not None


def test_cancel_falls_back_to_starter_entitlements(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    company_id = _create_company(client, owner)
    client.put(
        f"/api/v1/companies/{company_id}/subscription",
        json={"tier": "business"},
        headers=owner,
    )

    canceled = client.delete(f"/api/v1/companies/{company_id}/subscription", headers=owner)
    assert canceled.status_code == 200
    # Cancelada => direitos caem para Starter (sem white_label).
    assert "white_label" not in canceled.json()["features"]


def test_member_limit_blocks_invite_on_starter(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    _register(client, "maria@example.com")
    _register(client, "joao@example.com")
    company_id = _create_company(client, owner)

    # 2º membro: dentro do limite Starter (2).
    first = client.post(
        f"/api/v1/companies/{company_id}/invitations",
        json={"email": "maria@example.com", "role": "employee"},
        headers=owner,
    )
    assert first.status_code == 201

    # 3º membro: excede o limite Starter => 402 com upgrade_required.
    second = client.post(
        f"/api/v1/companies/{company_id}/invitations",
        json={"email": "joao@example.com", "role": "employee"},
        headers=owner,
    )
    assert second.status_code == 402
    assert second.json()["details"]["upgrade_required"] is True


def test_upgrade_unblocks_invite(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    _register(client, "maria@example.com")
    _register(client, "joao@example.com")
    company_id = _create_company(client, owner)
    client.put(
        f"/api/v1/companies/{company_id}/subscription",
        json={"tier": "professional"},
        headers=owner,
    )

    client.post(
        f"/api/v1/companies/{company_id}/invitations",
        json={"email": "maria@example.com", "role": "employee"},
        headers=owner,
    )
    third = client.post(
        f"/api/v1/companies/{company_id}/invitations",
        json={"email": "joao@example.com", "role": "employee"},
        headers=owner,
    )
    assert third.status_code == 201  # Professional permite 5
