"""Adaptador de cobrança do Asaas.

O caso perigoso aqui não é o pagamento falhar — é o webhook aceitar um aviso
falso. Sem verificação, qualquer um que descubra a URL marca a própria
assinatura como paga e usa o produto de graça. Por isso a maior parte destes
testes é sobre recusar, não sobre aceitar.
"""

import httpx
import pytest

from app.core.exceptions import ConnectorError
from app.domain.billing.ports import BillingEventType
from app.domain.subscription.entities import BillingCycle
from app.domain.subscription.plans import PlanTier
from app.infrastructure.billing.asaas import AsaasBillingProvider

pytestmark = pytest.mark.anyio

_BASE = "https://asaas.test/v3"


def _provider(handler: object = None, *, webhook_token: str | None = "token-secreto"):
    transport = httpx.MockTransport(handler) if handler else None  # type: ignore[arg-type]
    return AsaasBillingProvider(
        api_key="chave",
        webhook_token=webhook_token,
        base_url=_BASE,
        transport=transport,
    )


# --- Verificação do webhook ----------------------------------------------


def test_webhook_rejects_wrong_token() -> None:
    assert _provider().verify_webhook(token="token-errado") is False


def test_webhook_rejects_missing_token() -> None:
    assert _provider().verify_webhook(token=None) is False


def test_webhook_rejects_everything_when_not_configured() -> None:
    """Sem token configurado, aceitar seria transformar o webhook numa porta
    aberta — é mais seguro recusar tudo e o dono perceber que faltou configurar
    do que liberar acesso pago em silêncio."""
    assert _provider(webhook_token=None).verify_webhook(token="qualquer") is False


def test_webhook_accepts_the_configured_token() -> None:
    assert _provider().verify_webhook(token="token-secreto") is True


# --- Tradução dos eventos -------------------------------------------------


def test_confirmed_payment_becomes_paid() -> None:
    evento = _provider().parse_webhook(
        {
            "event": "PAYMENT_CONFIRMED",
            "payment": {"subscription": "sub_123", "dueDate": "2026-09-24"},
        }
    )

    assert evento is not None
    assert evento.type == BillingEventType.PAID
    assert evento.external_id == "sub_123"
    assert evento.period_end is not None


def test_overdue_and_cancellation_are_mapped() -> None:
    atrasado = _provider().parse_webhook(
        {"event": "PAYMENT_OVERDUE", "payment": {"subscription": "sub_1"}}
    )
    cancelado = _provider().parse_webhook(
        {"event": "SUBSCRIPTION_DELETED", "payment": {"subscription": "sub_1"}}
    )

    assert atrasado is not None and atrasado.type == BillingEventType.OVERDUE
    assert cancelado is not None and cancelado.type == BillingEventType.CANCELED


def test_irrelevant_events_are_ignored() -> None:
    """O Asaas emite dezenas de eventos. Reagir a todos seria ruído, e forçar o
    chamador a conhecer o vocabulário do provedor vazaria detalhe para dentro."""
    assert _provider().parse_webhook({"event": "PAYMENT_CREATED", "payment": {}}) is None
    assert _provider().parse_webhook({"nada": "aqui"}) is None


def test_event_without_subscription_is_ignored() -> None:
    # Sem identificador não há como saber de quem é o pagamento.
    assert _provider().parse_webhook({"event": "PAYMENT_CONFIRMED", "payment": {}}) is None


# --- Criação e cancelamento ----------------------------------------------


async def test_creates_customer_then_subscription() -> None:
    chamadas: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        chamadas.append(request.url.path)
        if request.url.path.endswith("/customers"):
            return httpx.Response(200, json={"id": "cus_1"})
        return httpx.Response(200, json={"id": "sub_1", "invoiceUrl": "https://asaas.test/i/sub_1"})

    sessao = await _provider(handler).create_subscription(
        company_id="empresa-1",
        company_name="Barbearia do Zé",
        cnpj="19131243000197",
        payer_email="dono@example.com",
        tier=PlanTier.PROFESSIONAL,
        billing_cycle=BillingCycle.MONTHLY,
        price_cents=4900,
    )

    assert chamadas == ["/v3/customers", "/v3/subscriptions"]
    assert sessao.external_id == "sub_1"
    assert sessao.payment_url == "https://asaas.test/i/sub_1"


async def test_price_is_sent_in_reais_not_cents() -> None:
    """O sistema guarda centavos inteiros; o Asaas espera reais decimais.
    Mandar 4900 cobraria R$ 4.900,00 de quem contratou um plano de R$ 49,00."""
    corpos: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        import json as _json

        corpos.append(_json.loads(request.content))
        if request.url.path.endswith("/customers"):
            return httpx.Response(200, json={"id": "cus_1"})
        return httpx.Response(200, json={"id": "sub_1", "invoiceUrl": "x"})

    await _provider(handler).create_subscription(
        company_id="empresa-1",
        company_name="Barbearia",
        cnpj="19131243000197",
        payer_email="dono@example.com",
        tier=PlanTier.PROFESSIONAL,
        billing_cycle=BillingCycle.MONTHLY,
        price_cents=4900,
    )

    assert corpos[1]["value"] == 49.0
    assert corpos[1]["cycle"] == "MONTHLY"


async def test_error_carries_the_reason_given_by_asaas() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"errors": [{"description": "CPF/CNPJ inválido"}]})

    with pytest.raises(ConnectorError, match="CPF/CNPJ inválido"):
        await _provider(handler).create_subscription(
            company_id="empresa-1",
            company_name="Barbearia",
            cnpj="00000000000000",
            payer_email="dono@example.com",
            tier=PlanTier.PROFESSIONAL,
            billing_cycle=BillingCycle.MONTHLY,
            price_cents=4900,
        )


async def test_cancelling_something_already_gone_is_not_an_error() -> None:
    """O usuário pode clicar duas vezes; a segunda não pode virar erro na tela."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={})

    await _provider(handler).cancel_subscription("sub_inexistente")
