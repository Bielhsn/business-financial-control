"""Adaptador de cobrança do Asaas.

Escolhido por encaixe com o público: assinatura recorrente nativa, Pix, boleto e
cartão, com taxas locais. Um dono de barbearia paga por Pix ou boleto; exigir
cartão internacional excluiria parte dos clientes.

**Sobre o mapeamento das respostas:** os nomes de campo seguem a documentação do
Asaas e ainda não foram confrontados com uma conta real. Foi exatamente aqui que
o iFood surpreendeu — endpoint inexistente, camelCase inesperado —, então todo o
parsing fica em funções puras, cobertas por teste e fáceis de ajustar. No dia em
que a chave existir, valida-se o formato sem tocar em caso de uso.

Verifiquei o que dava sem chave: `api.asaas.com/v3` e `api-sandbox.asaas.com/v3`
respondem 401 a `/customers`, então as bases e o caminho estão certos.
"""

import hmac
from datetime import datetime
from typing import Any

import httpx

from app.core.exceptions import ConnectorError
from app.core.logging import get_logger
from app.domain.billing.ports import BillingEvent, BillingEventType, CheckoutSession
from app.domain.subscription.entities import BillingCycle
from app.domain.subscription.plans import PlanTier
from app.infrastructure.http.retry import RetryTransport

logger = get_logger(__name__)

PRODUCTION_BASE_URL = "https://api.asaas.com/v3"
SANDBOX_BASE_URL = "https://api-sandbox.asaas.com/v3"

# Eventos do Asaas → vocabulário da aplicação. O provedor emite dezenas; só
# estes mudam o direito de acesso, e o resto é ignorado de propósito para o
# webhook não virar um switch gigante que ninguém entende.
_EVENT_MAP = {
    "PAYMENT_CONFIRMED": BillingEventType.PAID,
    "PAYMENT_RECEIVED": BillingEventType.PAID,
    "PAYMENT_OVERDUE": BillingEventType.OVERDUE,
    "SUBSCRIPTION_DELETED": BillingEventType.CANCELED,
    "PAYMENT_DELETED": BillingEventType.CANCELED,
    "PAYMENT_REFUNDED": BillingEventType.CANCELED,
}

_CYCLE_MAP = {BillingCycle.MONTHLY: "MONTHLY", BillingCycle.YEARLY: "YEARLY"}


class AsaasBillingProvider:
    def __init__(
        self,
        *,
        api_key: str,
        webhook_token: str | None = None,
        base_url: str = PRODUCTION_BASE_URL,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._api_key = api_key
        self._webhook_token = webhook_token
        self._base_url = base_url.rstrip("/")
        self._transport = transport

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=30.0,
            transport=self._transport or RetryTransport(),
            # O Asaas autentica por cabeçalho próprio, não por Bearer.
            headers={"access_token": self._api_key, "Content-Type": "application/json"},
        )

    async def _post(self, client: httpx.AsyncClient, path: str, body: dict[str, Any]) -> Any:
        try:
            response = await client.post(f"{self._base_url}{path}", json=body)
        except httpx.HTTPError as exc:
            raise ConnectorError("Não foi possível falar com o Asaas agora.") from exc
        if response.status_code >= 400:
            raise ConnectorError(_error_message(response))
        return response.json()

    async def create_subscription(
        self,
        *,
        company_id: str,
        company_name: str,
        cnpj: str,
        payer_email: str,
        tier: PlanTier,
        billing_cycle: BillingCycle,
        price_cents: int,
    ) -> CheckoutSession:
        async with self._client() as client:
            cliente = await self._post(
                client,
                "/customers",
                {
                    "name": company_name,
                    "cpfCnpj": cnpj,
                    "email": payer_email,
                    # Amarra o cliente do Asaas à empresa daqui: é por este
                    # campo que o webhook reencontra o dono do pagamento.
                    "externalReference": company_id,
                },
            )
            customer_id = cliente.get("id")
            if not isinstance(customer_id, str):
                raise ConnectorError("O Asaas não devolveu o identificador do cliente.")

            assinatura = await self._post(
                client,
                "/subscriptions",
                {
                    "customer": customer_id,
                    # UNDEFINED deixa o pagador escolher Pix, boleto ou cartão.
                    # Fixar um método excluiria quem não usa aquele.
                    "billingType": "UNDEFINED",
                    "value": round(price_cents / 100, 2),
                    "cycle": _CYCLE_MAP[billing_cycle],
                    "nextDueDate": datetime.now().date().isoformat(),
                    "description": f"Aurum OS — plano {tier.value}",
                    "externalReference": company_id,
                },
            )
            return _parse_checkout(assinatura)

    async def cancel_subscription(self, external_id: str) -> None:
        async with self._client() as client:
            try:
                response = await client.delete(f"{self._base_url}/subscriptions/{external_id}")
            except httpx.HTTPError as exc:
                raise ConnectorError("Não foi possível falar com o Asaas agora.") from exc
            # 404 é sucesso aqui: cancelar o que já não existe chegou ao mesmo
            # destino, e o usuário pode ter clicado duas vezes.
            if response.status_code == 404:
                logger.info("asaas_subscription_already_gone", external_id=external_id)
                return
            if response.status_code >= 400:
                raise ConnectorError(_error_message(response))

    def parse_webhook(self, payload: dict[str, object]) -> BillingEvent | None:
        return _parse_webhook(payload)

    def verify_webhook(self, *, token: str | None) -> bool:
        if not self._webhook_token:
            # Sem token configurado, recusa tudo. Aceitar seria transformar o
            # webhook numa porta aberta: qualquer um que descubra a URL marcaria
            # a própria assinatura como paga.
            logger.warning("asaas_webhook_token_missing")
            return False
        # Comparação de tempo constante: comparar com == vaza o prefixo correto
        # pelo tempo de resposta.
        return hmac.compare_digest(token or "", self._webhook_token)


def _parse_checkout(payload: dict[str, Any]) -> CheckoutSession:
    external_id = payload.get("id")
    if not isinstance(external_id, str):
        raise ConnectorError("O Asaas não devolveu o identificador da assinatura.")
    # O link aparece em campos diferentes conforme o tipo de cobrança; aceitar
    # os dois evita quebrar por uma variação de forma.
    url = payload.get("paymentLink") or payload.get("invoiceUrl")
    return CheckoutSession(external_id=external_id, payment_url=url if isinstance(url, str) else "")


def _parse_webhook(payload: dict[str, object]) -> BillingEvent | None:
    evento = payload.get("event")
    if not isinstance(evento, str):
        return None
    tipo = _EVENT_MAP.get(evento)
    if tipo is None:
        # Evento que não muda direito de acesso. Ignorar em silêncio é o certo:
        # o Asaas emite dezenas e reagir a todos seria ruído.
        return None

    pagamento = payload.get("payment")
    dados = pagamento if isinstance(pagamento, dict) else {}
    # A assinatura é o que identifica a recorrência; o pagamento avulso é uma
    # parcela dela.
    external_id = dados.get("subscription") or dados.get("id")
    if not isinstance(external_id, str):
        return None

    return BillingEvent(
        type=tipo, external_id=external_id, period_end=_parse_date(dados.get("dueDate"))
    )


def _parse_date(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _error_message(response: httpx.Response) -> str:
    """Repassa o motivo do Asaas em vez de um "falhou" genérico — a lição do
    iFood: sem o texto original, o erro parece uma coisa e é outra."""
    detalhe = ""
    try:
        corpo = response.json()
    except ValueError:
        corpo = None
    if isinstance(corpo, dict):
        erros = corpo.get("errors")
        if isinstance(erros, list) and erros and isinstance(erros[0], dict):
            descricao = erros[0].get("description")
            if isinstance(descricao, str):
                detalhe = f": {descricao}"
    return f"O Asaas recusou a operação (HTTP {response.status_code}){detalhe}"
