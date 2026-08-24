"""Contrato de cobrança recorrente.

O domínio não conhece Asaas. Ele conhece "criar uma assinatura para esta empresa
neste plano" e "esta assinatura foi paga / atrasou / foi cancelada". Trocar de
provedor — ou atender um cliente que use outro — vira escrever um adaptador,
sem tocar em regra de negócio.

É o mesmo desenho dos conectores de venda, e pela mesma razão: o provedor é
detalhe de infraestrutura, e detalhe de infraestrutura vazado para dentro do
domínio é o que torna a troca cara depois.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from app.domain.subscription.entities import BillingCycle
from app.domain.subscription.plans import PlanTier


class BillingEventType(StrEnum):
    """O que o provedor avisa. Vocabulário fechado de propósito: cada provedor
    tem dezenas de eventos, e só estes mudam o direito de acesso."""

    PAID = "paid"  # pagamento confirmado — renova o período
    OVERDUE = "overdue"  # venceu sem pagar — vira inadimplente
    CANCELED = "canceled"  # assinatura encerrada


@dataclass(frozen=True)
class CheckoutSession:
    """Para onde mandar o lojista pagar."""

    # Identificador da assinatura no provedor. Guardado para casar o webhook
    # com a empresa depois — sem isso, um aviso de pagamento chega sem dono.
    external_id: str
    payment_url: str


@dataclass(frozen=True)
class BillingEvent:
    """Aviso do provedor, já traduzido para o vocabulário da aplicação."""

    type: BillingEventType
    external_id: str
    # Até quando o acesso está pago. None quando o evento não define período
    # (cancelamento, por exemplo).
    period_end: datetime | None = None


class BillingProvider(Protocol):
    """Cobrança recorrente. Implementado por adaptador de infraestrutura."""

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
        """Cria a assinatura no provedor e devolve o link de pagamento."""
        ...

    async def cancel_subscription(self, external_id: str) -> None:
        """Encerra a cobrança. Idempotente: cancelar o que já foi cancelado não
        pode virar erro, porque o usuário pode clicar duas vezes."""
        ...

    def parse_webhook(self, payload: dict[str, object]) -> BillingEvent | None:
        """Traduz o aviso do provedor. Devolve None para evento que não muda o
        direito de acesso — a maioria — em vez de forçar o chamador a conhecer
        o vocabulário do provedor."""
        ...

    def verify_webhook(self, *, token: str | None) -> bool:
        """Confere se o aviso veio mesmo do provedor.

        Sem isto, qualquer um que descubra a URL marca a própria assinatura como
        paga. É a checagem que separa um webhook de uma porta aberta.
        """
        ...
