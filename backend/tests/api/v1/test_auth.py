import pytest
from fastapi.testclient import TestClient

from tests.fakes import FakeUserRepository

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
REFRESH_URL = "/api/v1/auth/refresh"
LOGOUT_URL = "/api/v1/auth/logout"
ME_URL = "/api/v1/auth/me"


def _register(
    client: TestClient, email: str = "ana@example.com", password: str = "s3cr3t!!"
) -> None:
    response = client.post(
        REGISTER_URL,
        json={"email": email, "password": password, "full_name": "Ana Silva"},
    )
    assert response.status_code == 201


def test_register_creates_a_user_and_hides_the_password(client: TestClient) -> None:
    response = client.post(
        REGISTER_URL,
        json={"email": "ana@example.com", "password": "s3cr3t!!", "full_name": "Ana Silva"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "ana@example.com"
    assert body["full_name"] == "Ana Silva"
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_rejects_short_password(client: TestClient) -> None:
    response = client.post(
        REGISTER_URL,
        json={"email": "ana@example.com", "password": "short", "full_name": "Ana Silva"},
    )

    assert response.status_code == 422


def test_register_rejects_duplicate_email(client: TestClient) -> None:
    _register(client)

    response = client.post(
        REGISTER_URL,
        json={"email": "ana@example.com", "password": "outrasenha", "full_name": "Ana 2"},
    )

    assert response.status_code == 409
    assert response.json()["error"] == "ConflictError"


def test_login_returns_tokens_for_valid_credentials(client: TestClient) -> None:
    _register(client)

    response = client.post(LOGIN_URL, json={"email": "ana@example.com", "password": "s3cr3t!!"})

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


def test_login_rejects_wrong_password(client: TestClient) -> None:
    _register(client)

    response = client.post(LOGIN_URL, json={"email": "ana@example.com", "password": "errada123"})

    assert response.status_code == 401


def test_refresh_rotates_the_refresh_token(client: TestClient) -> None:
    _register(client)
    login_response = client.post(
        LOGIN_URL, json={"email": "ana@example.com", "password": "s3cr3t!!"}
    )
    old_refresh_token = login_response.json()["refresh_token"]

    refresh_response = client.post(REFRESH_URL, json={"refresh_token": old_refresh_token})

    assert refresh_response.status_code == 200
    assert refresh_response.json()["refresh_token"] != old_refresh_token

    reuse_response = client.post(REFRESH_URL, json={"refresh_token": old_refresh_token})
    assert reuse_response.status_code == 401


def test_refresh_rejects_unknown_token(client: TestClient) -> None:
    response = client.post(REFRESH_URL, json={"refresh_token": "does-not-exist"})

    assert response.status_code == 401


def test_logout_revokes_the_refresh_token(client: TestClient) -> None:
    _register(client)
    login_response = client.post(
        LOGIN_URL, json={"email": "ana@example.com", "password": "s3cr3t!!"}
    )
    refresh_token = login_response.json()["refresh_token"]

    logout_response = client.post(LOGOUT_URL, json={"refresh_token": refresh_token})
    assert logout_response.status_code == 204

    refresh_after_logout = client.post(REFRESH_URL, json={"refresh_token": refresh_token})
    assert refresh_after_logout.status_code == 401


def test_me_requires_authentication(client: TestClient) -> None:
    response = client.get(ME_URL)

    assert response.status_code == 401


def test_me_rejects_an_invalid_token(client: TestClient) -> None:
    response = client.get(ME_URL, headers={"Authorization": "Bearer not-a-real-token"})

    assert response.status_code == 401


def test_me_returns_the_authenticated_user(client: TestClient) -> None:
    _register(client)
    login_response = client.post(
        LOGIN_URL, json={"email": "ana@example.com", "password": "s3cr3t!!"}
    )
    access_token = login_response.json()["access_token"]

    response = client.get(ME_URL, headers={"Authorization": f"Bearer {access_token}"})

    assert response.status_code == 200
    assert response.json()["email"] == "ana@example.com"


@pytest.mark.anyio
async def test_me_rejects_a_deactivated_user(
    client: TestClient, fake_user_repository: FakeUserRepository
) -> None:
    _register(client)
    login_response = client.post(
        LOGIN_URL, json={"email": "ana@example.com", "password": "s3cr3t!!"}
    )
    access_token = login_response.json()["access_token"]

    user = await fake_user_repository.get_by_email("ana@example.com")
    assert user is not None
    user.is_active = False

    response = client.get(ME_URL, headers={"Authorization": f"Bearer {access_token}"})

    assert response.status_code == 401


def test_login_is_rate_limited(client: TestClient) -> None:
    for _ in range(5):
        client.post(LOGIN_URL, json={"email": "ana@example.com", "password": "errada"})

    response = client.post(LOGIN_URL, json={"email": "ana@example.com", "password": "errada"})

    assert response.status_code == 429
