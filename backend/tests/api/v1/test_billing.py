"""Contratação e cobrança pela API.

O fluxo inteiro do dinheiro passa por aqui: contratar cria a cobrança lá fora e
o vínculo aqui dentro, o webhook transforma pagamento em acesso, e cancelar
precisa parar a cobrança de verdade — não só mudar a cor de um selo na tela.
"""

from fastapi.testclient import TestClient

from app.domain.subscription.plans import PlanTier
from tests.fakes import FakeBillingProvider, FakeSubscriptionRepository
from tests.registration import register_payload, valid_cnpj
from tests.subscriptions import activate_paid_plan_sync

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


def _register(client: TestClient, email: str) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json=register_payload(email, "s3cr3t!!", email.split("@")[0]),
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "s3cr3t!!"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _company_with_cnpj(client: TestClient, headers: dict[str, str]) -> str:
    return client.post(
        "/api/v1/companies", json={**COMPANY, "cnpj": valid_cnpj()}, headers=headers
    ).json()["id"]


# --- Contratação ----------------------------------------------------------


def test_checkout_returns_the_payment_link_and_records_the_link(
    client: TestClient,
    fake_billing_provider: FakeBillingProvider,
    fake_subscription_repository: FakeSubscriptionRepository,
) -> None:
    owner = _register(client, "dono@example.com")
    company_id = _company_with_cnpj(client, owner)

    response = client.post(
        f"/api/v1/companies/{company_id}/billing/checkout",
        json={"tier": "professional", "billing_cycle": "monthly"},
        headers=owner,
    )

    assert response.status_code == 200
    assert response.json()["payment_url"].startswith("https://pagar.test/")
    cobranca = fake_billing_provider.created[0]
    assert cobranca["price_cents"] == 4900

    # O vínculo é gravado ANTES do pagamento: se o webhook chegasse primeiro e
    # não achasse a assinatura, o dinheiro não viraria acesso.
    sub = client.get(f"/api/v1/companies/{company_id}/subscription", headers=owner).json()
    assert sub["payment_pending"] is True
    assert sub["pending_tier"] == "professional"
    # E o plano ainda NÃO foi liberado — contratar não é pagar.
    assert sub["tier"] == "starter"


def test_checkout_cancels_the_previous_charge_before_creating_another(
    client: TestClient,
    fake_billing_provider: FakeBillingProvider,
) -> None:
    """Sem isto, quem faz upgrade passa a ser cobrado duas vezes por mês e
    descobre pela fatura, não pelo sistema."""
    owner = _register(client, "dono@example.com")
    company_id = _company_with_cnpj(client, owner)

    client.post(
        f"/api/v1/companies/{company_id}/billing/checkout",
        json={"tier": "professional"},
        headers=owner,
    )
    primeira = fake_billing_provider.created[0]["external_id"]

    client.post(
        f"/api/v1/companies/{company_id}/billing/checkout",
        json={"tier": "business"},
        headers=owner,
    )

    assert fake_billing_provider.canceled == [primeira]
    assert len(fake_billing_provider.created) == 2


def test_checkout_requires_cnpj(client: TestClient) -> None:
    owner = _register(client, "dono@example.com")
    company_id = client.post("/api/v1/companies", json=COMPANY, headers=owner).json()["id"]

    response = client.post(
        f"/api/v1/companies/{company_id}/billing/checkout",
        json={"tier": "professional"},
        headers=owner,
    )

    assert response.status_code == 422
    assert "CNPJ" in response.json()["message"]


def test_checkout_refuses_the_free_plan(client: TestClient) -> None:
    owner = _register(client, "dono@example.com")
    company_id = _company_with_cnpj(client, owner)

    response = client.post(
        f"/api/v1/companies/{company_id}/billing/checkout",
        json={"tier": "starter"},
        headers=owner,
    )

    assert response.status_code == 422


def test_only_the_owner_can_contract(client: TestClient) -> None:
    owner = _register(client, "dono@example.com")
    _register(client, "maria@example.com")
    company_id = _company_with_cnpj(client, owner)
    client.post(
        f"/api/v1/companies/{company_id}/invitations",
        json={"email": "maria@example.com", "role": "admin"},
        headers=owner,
    )
    maria = _register(client, "maria@example.com")

    response = client.post(
        f"/api/v1/companies/{company_id}/billing/checkout",
        json={"tier": "professional"},
        headers=maria,
    )

    assert response.status_code == 403


# --- Webhook --------------------------------------------------------------


def test_payment_confirmation_releases_the_plan(
    client: TestClient, fake_billing_provider: FakeBillingProvider
) -> None:
    owner = _register(client, "dono@example.com")
    company_id = _company_with_cnpj(client, owner)
    client.post(
        f"/api/v1/companies/{company_id}/billing/checkout",
        json={"tier": "business"},
        headers=owner,
    )
    external_id = fake_billing_provider.created[0]["external_id"]

    aviso = client.post(
        "/api/v1/billing/webhook",
        json={"event": "paid", "subscription": external_id},
        headers={"asaas-access-token": "token-de-teste"},
    )
    assert aviso.status_code == 204

    sub = client.get(f"/api/v1/companies/{company_id}/subscription", headers=owner).json()
    assert sub["tier"] == "business"
    assert sub["payment_pending"] is False
    assert "white_label" in sub["features"]


def test_webhook_without_the_token_changes_nothing(
    client: TestClient, fake_billing_provider: FakeBillingProvider
) -> None:
    """A porta dos fundos: sem verificação, quem descobrir a URL libera o
    próprio plano de graça."""
    owner = _register(client, "dono@example.com")
    company_id = _company_with_cnpj(client, owner)
    client.post(
        f"/api/v1/companies/{company_id}/billing/checkout",
        json={"tier": "business"},
        headers=owner,
    )
    external_id = fake_billing_provider.created[0]["external_id"]

    recusado = client.post(
        "/api/v1/billing/webhook",
        json={"event": "paid", "subscription": external_id},
        headers={"asaas-access-token": "token-errado"},
    )
    assert recusado.status_code == 401

    sub = client.get(f"/api/v1/companies/{company_id}/subscription", headers=owner).json()
    assert sub["tier"] == "starter"


def test_irrelevant_webhook_is_accepted_and_ignored(client: TestClient) -> None:
    # Responder erro faria o provedor reenviar para sempre.
    response = client.post(
        "/api/v1/billing/webhook",
        json={"event": "algo_que_nao_conhecemos", "subscription": "sub_1"},
        headers={"asaas-access-token": "token-de-teste"},
    )
    assert response.status_code == 204


# --- Cancelamento ---------------------------------------------------------


def test_cancelling_stops_the_charge_at_the_provider(
    client: TestClient,
    fake_billing_provider: FakeBillingProvider,
    fake_subscription_repository: FakeSubscriptionRepository,
) -> None:
    """Cancelar só na nossa base deixaria a fatura chegando todo mês."""
    owner = _register(client, "dono@example.com")
    company_id = _company_with_cnpj(client, owner)
    activate_paid_plan_sync(
        fake_subscription_repository,
        company_id=company_id,
        tier=PlanTier.BUSINESS,
        external_id="asaas_externo",
    )

    response = client.delete(f"/api/v1/companies/{company_id}/subscription", headers=owner)

    assert response.status_code == 200
    assert fake_billing_provider.canceled == ["asaas_externo"]


def test_cancelling_a_free_plan_does_not_touch_the_provider(
    client: TestClient, fake_billing_provider: FakeBillingProvider
) -> None:
    owner = _register(client, "dono@example.com")
    company_id = _company_with_cnpj(client, owner)

    client.delete(f"/api/v1/companies/{company_id}/subscription", headers=owner)

    assert fake_billing_provider.canceled == []
