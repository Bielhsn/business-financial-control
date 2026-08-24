from datetime import datetime

from beanie import Document, Indexed
from pymongo import IndexModel


class SubscriptionDocument(Document):
    company_id: Indexed(str, unique=True)  # type: ignore[valid-type]
    tier: str
    status: str
    billing_cycle: str = "monthly"
    started_at: datetime
    updated_at: datetime
    trial_ends_at: datetime | None = None
    current_period_end: datetime | None = None
    cancel_at_period_end: bool = False
    # Assinatura no provedor de pagamento; único para o webhook casar sem
    # ambiguidade. Índice parcial porque o campo é opcional (plano grátis não
    # tem cobrança).
    external_id: str | None = None
    # Marca de que o teste gratuito já foi consumido. Fica fora do ciclo de
    # vida da assinatura de propósito: é histórico da empresa, não estado.
    trial_used: bool = False

    class Settings:
        name = "subscriptions"
        indexes = [
            IndexModel(
                [("external_id", 1)],
                unique=True,
                name="uniq_subscription_external_id",
                partialFilterExpression={"external_id": {"$type": "string"}},
            ),
        ]
