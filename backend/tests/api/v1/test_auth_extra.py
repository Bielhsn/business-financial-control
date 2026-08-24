"""Testes dos fluxos de autenticação da Etapa 27: verificação por e-mail,
recuperação/alteração de senha e login com Google."""

from fastapi.testclient import TestClient

from app.api.v1 import deps
from app.core.config import Settings, get_settings
from app.core.exceptions import NotFoundError
from app.domain.auth.google import GoogleIdentity
from app.domain.company.cnpj_lookup import CnpjInfo
from app.main import app
from tests.fakes import (
    FakeCnpjLookup,
    FakeEmailSender,
    FakeGoogleTokenVerifier,
    FakeVerificationCodeRepository,
)
from tests.registration import register_payload, valid_cnpj


def _register_and_token(client: TestClient, email: str = "ana@example.com") -> str:
    client.post(
        "/api/v1/auth/register",
        json=register_payload(email, "s3cr3t!!", "Ana"),
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
        FakeCnpjLookup,
        FakeCompanyMembershipRepository,
        FakeCompanyRepository,
        FakeFinancialCategoryRepository,
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
    # O cadastro cria a empresa junto com a conta, então precisa dos
    # repositórios de empresa e do consultor de CNPJ também.
    app.dependency_overrides[deps.get_company_repository] = lambda: FakeCompanyRepository()
    app.dependency_overrides[deps.get_company_membership_repository] = (
        lambda: FakeCompanyMembershipRepository()
    )
    app.dependency_overrides[deps.get_financial_category_repository] = (
        lambda: FakeFinancialCategoryRepository()
    )
    app.dependency_overrides[deps.get_cnpj_lookup] = lambda: FakeCnpjLookup()
    try:
        # Sem "with": não dispara o lifespan (que exigiria MongoDB real).
        isolated = TestClient(app)
        isolated.post(
            "/api/v1/auth/register",
            json=register_payload("b@example.com", "s3cr3t!!", "B"),
        )
        login = isolated.post(
            "/api/v1/auth/login", json={"email": "b@example.com", "password": "s3cr3t!!"}
        )
        assert login.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_register_stores_contact_and_role(client: TestClient) -> None:
    """Telefone e cargo têm propósito: contato de suporte e calibragem do
    contexto (produto e IA). Ambos opcionais — não travam o onboarding."""
    response = client.post(
        "/api/v1/auth/register",
        json=register_payload(
            "gestor@example.com",
            "s3cr3t!!",
            "Gabriel Henrique",
            phone="11999998888",
            job_role="Dono",
        ),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["phone"] == "11999998888"
    assert body["job_role"] == "Dono"


def test_register_without_optional_fields_still_works(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json=register_payload("simples@example.com", "s3cr3t!!", "Ana"),
    )

    assert response.status_code == 201
    assert response.json()["phone"] is None
    assert response.json()["job_role"] is None


# --- Cadastro em um passo: conta + primeira empresa ----------------------


def test_register_creates_the_first_company(client: TestClient) -> None:
    """A conta não nasce mais sem empresa. Antes, quem abandonasse o onboarding
    ficava com um login que não levava a lugar nenhum."""
    response = client.post(
        "/api/v1/auth/register",
        json=register_payload("dono@example.com", full_name="Gabriel", company_name="Barbearia X"),
    )
    assert response.status_code == 201

    token = client.post(
        "/api/v1/auth/login", json={"email": "dono@example.com", "password": "s3cr3t!!"}
    ).json()["access_token"]
    empresas = client.get("/api/v1/companies", headers={"Authorization": f"Bearer {token}"}).json()

    assert len(empresas) == 1
    assert empresas[0]["company"]["name"] == "Barbearia X"
    assert empresas[0]["role"] == "owner"


def test_register_rejects_mismatched_password_confirmation(client: TestClient) -> None:
    """A comparação do frontend é conveniência, não garantia: qualquer cliente
    pode enviar o par divergente direto na API."""
    payload = register_payload("ana@example.com")
    payload["password_confirmation"] = "outra-senha-bem-diferente"

    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 422
    assert "senhas não conferem" in response.text.lower()


def test_register_rejects_cnpj_already_used_by_another_account(client: TestClient) -> None:
    cnpj = valid_cnpj()
    primeiro = client.post(
        "/api/v1/auth/register", json=register_payload("um@example.com", cnpj=cnpj)
    )
    assert primeiro.status_code == 201

    segundo = client.post(
        "/api/v1/auth/register", json=register_payload("dois@example.com", cnpj=cnpj)
    )

    assert segundo.status_code == 409
    assert "já está cadastrado" in segundo.json()["message"]


def test_rejected_cnpj_leaves_no_orphan_account(
    client: TestClient, fake_cnpj_lookup: FakeCnpjLookup
) -> None:
    """A ordem das operações é a parte que importa: validar depois de gravar
    deixaria uma conta sem empresa toda vez que o CNPJ fosse recusado."""

    async def nao_encontrado(cnpj: str) -> CnpjInfo:
        raise NotFoundError("CNPJ não encontrado na base da Receita.")

    fake_cnpj_lookup.fetch = nao_encontrado  # type: ignore[method-assign]

    falhou = client.post("/api/v1/auth/register", json=register_payload("orfa@example.com"))
    assert falhou.status_code == 422

    # A conta não pode ter sobrado: o e-mail continua livre.
    fake_cnpj_lookup.fetch = FakeCnpjLookup().fetch  # type: ignore[method-assign]
    de_novo = client.post("/api/v1/auth/register", json=register_payload("orfa@example.com"))
    assert de_novo.status_code == 201


def test_register_prefills_company_from_the_receita(client: TestClient) -> None:
    """Cidade, estado e razão social vêm da consulta — o dono não redigita o que
    a Receita já informou."""
    client.post("/api/v1/auth/register", json=register_payload("dono@example.com"))
    token = client.post(
        "/api/v1/auth/login", json={"email": "dono@example.com", "password": "s3cr3t!!"}
    ).json()["access_token"]

    empresa = client.get("/api/v1/companies", headers={"Authorization": f"Bearer {token}"}).json()[
        0
    ]["company"]

    assert empresa["city"] == "São Paulo"
    assert empresa["state"] == "SP"
    assert empresa["legal_name"] == "Empresa Exemplo LTDA"
