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


def test_goals_start_empty(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    company_id = _create_company(client, owner)
    response = client.get(f"/api/v1/companies/{company_id}/goals", headers=owner)
    assert response.status_code == 200
    assert response.json() == []


def test_set_and_list_goal(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    company_id = _create_company(client, owner)

    response = client.put(
        f"/api/v1/companies/{company_id}/goals/monthly_income",
        json={"target_cents": 500000},
        headers=owner,
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["metric"] == "monthly_income"
    assert body[0]["target_cents"] == 500000
    assert body[0]["actual_cents"] == 0


def test_set_goal_rejects_non_positive_target(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    company_id = _create_company(client, owner)
    response = client.put(
        f"/api/v1/companies/{company_id}/goals/monthly_net",
        json={"target_cents": 0},
        headers=owner,
    )
    assert response.status_code == 422


def test_delete_goal(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    company_id = _create_company(client, owner)
    client.put(
        f"/api/v1/companies/{company_id}/goals/monthly_net",
        json={"target_cents": 100000},
        headers=owner,
    )
    deleted = client.delete(f"/api/v1/companies/{company_id}/goals/monthly_net", headers=owner)
    assert deleted.status_code == 204
    remaining = client.get(f"/api/v1/companies/{company_id}/goals", headers=owner).json()
    assert remaining == []


def test_viewer_cannot_set_goal(client: TestClient) -> None:
    owner = _headers(_register(client, "dono@example.com"))
    _register(client, "leitor@example.com")
    company_id = _create_company(client, owner)
    client.post(
        f"/api/v1/companies/{company_id}/invitations",
        json={"email": "leitor@example.com", "role": "viewer"},
        headers=owner,
    )
    viewer = _headers(_register(client, "leitor@example.com"))

    response = client.put(
        f"/api/v1/companies/{company_id}/goals/monthly_income",
        json={"target_cents": 100000},
        headers=viewer,
    )
    assert response.status_code == 403
