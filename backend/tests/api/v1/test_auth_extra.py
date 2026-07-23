"""Testes dos fluxos de autenticação da Etapa 27: verificação por e-mail,
recuperação/alteração de senha e login com Google."""

from fastapi.testclient import TestClient

from app.api.v1 import deps
from app.core.config import Settings, get_settings
from app.domain.auth.google import GoogleIdentity
from app.main import app
from tests.fakes import FakeEmailSender, FakeGoogleTokenVerifier, FakeVerificationCodeRepository


def _register_and_token(client: TestClient, email: str = "ana@example.com") -> str:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "s3cr3t!!", "full_name": "Ana"},
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "s3cr3t!!"})
    return login.json()["access_token"]


def _extract_token(email_sender: FakeEmailSender) -> str:
    """Extrai o parâmetro ?token=... do LINK presente no corpo do e-mail."""
    import re
    from urllib.parse import parse_qs, urlparse

    body = email_sender.sent[-1].body
    match = re.search(r"https?://\S+", body)
    assert match is not None, body
    query = parse_qs(urlparse(match.group(0)).query)
    return query["token"][0]


def test_request_and_verify_email(
    client: TestClient,
    fake_email_sender: FakeEmailSender,
    fake_user_repository: object,
) -> None:
    token = _register_and_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Força a conta a não-verificada para exercitar o fluxo.
    user = next(iter(fake_user_repository._users_by_id.values()))  # type: ignore[attr-defined]
    user.is_verified = False

    requested = client.post("/api/v1/auth/request-verification", headers=headers)
    assert requested.status_code == 204
    link_token = _extract_token(fake_email_sender)

    verified = client.post("/api/v1/auth/verify-email", json={"code": link_token}, headers=headers)
    assert verified.status_code == 204
    assert user.is_verified is True


def test_public_confirm_email_by_link(
    client: TestClient,
    fake_email_sender: FakeEmailSender,
    fake_user_repository: object,
) -> None:
    # Cadastra e força não-verificado; reenvia a confirmação de forma PÚBLICA
    # (sem login) e confirma pelo token do link — como quem clica no e-mail.
    _register_and_token(client, "leo@example.com")
    user = next(iter(fake_user_repository._users_by_id.values()))  # type: ignore[attr-defined]
    user.is_verified = False

    resent = client.post("/api/v1/auth/resend-verification", json={"email": "leo@example.com"})
    assert resent.status_code == 204
    link_token = _extract_token(fake_email_sender)

    confirmed = client.post(
        "/api/v1/auth/confirm-email",
        json={"email": "leo@example.com", "token": link_token},
    )
    assert confirmed.status_code == 204
    assert user.is_verified is True

    # Clicar de novo é idempotente (não dá erro).
    again = client.post(
        "/api/v1/auth/confirm-email",
        json={"email": "leo@example.com", "token": link_token},
    )
    assert again.status_code == 204


def test_confirm_email_rejects_bad_token(client: TestClient, fake_user_repository: object) -> None:
    _register_and_token(client, "mia@example.com")
    user = next(iter(fake_user_repository._users_by_id.values()))  # type: ignore[attr-defined]
    user.is_verified = False

    response = client.post(
        "/api/v1/auth/confirm-email",
        json={"email": "mia@example.com", "token": "token-invalido"},
    )
    assert response.status_code == 422
    assert user.is_verified is False


def test_resend_verification_unknown_email_is_silent(
    client: TestClient, fake_email_sender: FakeEmailSender
) -> None:
    response = client.post(
        "/api/v1/auth/resend-verification", json={"email": "ninguem@example.com"}
    )
    assert response.status_code == 204
    assert fake_email_sender.sent == []


def test_verify_email_rejects_wrong_code(client: TestClient) -> None:
    token = _register_and_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/api/v1/auth/verify-email", json={"code": "000000"}, headers=headers)
    assert response.status_code == 422


def test_forgot_and_reset_password(client: TestClient, fake_email_sender: FakeEmailSender) -> None:
    _register_and_token(client, "ana@example.com")

    forgot = client.post("/api/v1/auth/forgot-password", json={"email": "ana@example.com"})
    assert forgot.status_code == 200
    link_token = _extract_token(fake_email_sender)

    reset = client.post(
        "/api/v1/auth/reset-password",
        json={"email": "ana@example.com", "token": link_token, "new_password": "novaSenha123"},
    )
    assert reset.status_code == 204

    # Senha antiga não loga mais; a nova sim.
    old = client.post(
        "/api/v1/auth/login", json={"email": "ana@example.com", "password": "s3cr3t!!"}
    )
    assert old.status_code == 401
    new = client.post(
        "/api/v1/auth/login", json={"email": "ana@example.com", "password": "novaSenha123"}
    )
    assert new.status_code == 200


def test_forgot_password_unknown_email_is_silent(
    client: TestClient, fake_email_sender: FakeEmailSender
) -> None:
    response = client.post("/api/v1/auth/forgot-password", json={"email": "ninguem@example.com"})
    assert response.status_code == 200
    assert fake_email_sender.sent == []


def test_change_password(client: TestClient) -> None:
    token = _register_and_token(client, "ana@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    changed = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "s3cr3t!!", "new_password": "novaSenha123"},
        headers=headers,
    )
    assert changed.status_code == 204
    assert (
        client.post(
            "/api/v1/auth/login", json={"email": "ana@example.com", "password": "novaSenha123"}
        ).status_code
        == 200
    )


def test_change_password_rejects_wrong_current(client: TestClient) -> None:
    token = _register_and_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "errada", "new_password": "novaSenha123"},
        headers=headers,
    )
    assert response.status_code == 401


def test_google_login_creates_and_logs_in(
    client: TestClient, fake_google_verifier: FakeGoogleTokenVerifier
) -> None:
    fake_google_verifier.register(
        "tok-google",
        GoogleIdentity(email="novo@gmail.com", full_name="Novo Usuário", email_verified=True),
    )

    response = client.post("/api/v1/auth/google", json={"id_token": "tok-google"})

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_google_login_rejects_invalid_token(client: TestClient) -> None:
    response = client.post("/api/v1/auth/google", json={"id_token": "invalido"})
    assert response.status_code == 401


def test_login_blocked_when_verification_required_and_unverified(
    fake_verification_code_repository: FakeVerificationCodeRepository,
) -> None:
    # Sobrescreve settings com a política de verificação LIGADA.
    from tests.fakes import (
        FakeAuditLogRepository,
        FakePasswordHasher,
        FakeRefreshTokenRepository,
        FakeTokenService,
        FakeUserRepository,
    )

    user_repo = FakeUserRepository()
    app.dependency_overrides[get_settings] = lambda: Settings(
        _env_file=None, require_email_verification=True
    )
    app.dependency_overrides[deps.get_user_repository] = lambda: user_repo
    app.dependency_overrides[deps.get_password_hasher] = lambda: FakePasswordHasher()
    app.dependency_overrides[deps.get_token_service] = lambda: FakeTokenService()
    app.dependency_overrides[deps.get_refresh_token_repository] = (
        lambda: FakeRefreshTokenRepository()
    )
    app.dependency_overrides[deps.get_audit_log_repository] = lambda: FakeAuditLogRepository()
    app.dependency_overrides[deps.get_verification_code_repository] = (
        lambda: fake_verification_code_repository
    )
    app.dependency_overrides[deps.get_email_sender] = lambda: FakeEmailSender()
    try:
        # Sem "with": não dispara o lifespan (que exigiria MongoDB real).
        isolated = TestClient(app)
        isolated.post(
            "/api/v1/auth/register",
            json={"email": "b@example.com", "password": "s3cr3t!!", "full_name": "B"},
        )
        login = isolated.post(
            "/api/v1/auth/login", json={"email": "b@example.com", "password": "s3cr3t!!"}
        )
        assert login.status_code == 401
    finally:
        app.dependency_overrides.clear()
