from datetime import UTC, datetime

from app.domain.subscription.entities import BillingCycle, Subscription, SubscriptionStatus
from app.domain.subscription.plans import PlanTier
from app.infrastructure.database.models.subscription import SubscriptionDocument


def _to_entity(document: SubscriptionDocument) -> Subscription:
    return Subscription(
        id=str(document.id),
        company_id=document.company_id,
        tier=PlanTier(document.tier),
        status=SubscriptionStatus(document.status),
        billing_cycle=BillingCycle(document.billing_cycle),
        started_at=document.started_at,
        updated_at=document.updated_at,
        trial_ends_at=document.trial_ends_at,
        current_period_end=document.current_period_end,
        cancel_at_period_end=document.cancel_at_period_end,
        external_id=document.external_id,
        trial_used=document.trial_used,
    )


class BeanieSubscriptionRepository:
    async def get_by_company(self, company_id: str) -> Subscription | None:
        document = await SubscriptionDocument.find_one(
            SubscriptionDocument.company_id == company_id
        )
        return _to_entity(document) if document else None

    async def upsert(
        self,
        *,
        company_id: str,
        tier: PlanTier,
        status: SubscriptionStatus,
        billing_cycle: BillingCycle,
        trial_ends_at: datetime | None,
        current_period_end: datetime | None,
        cancel_at_period_end: bool,
        external_id: str | None = None,
        trial_used: bool = False,
    ) -> Subscription:
        now = datetime.now(UTC)
        document = await SubscriptionDocument.find_one(
            SubscriptionDocument.company_id == company_id
        )
        if document is None:
            document = SubscriptionDocument(
                company_id=company_id,
                tier=tier.value,
                status=status.value,
                billing_cycle=billing_cycle.value,
                started_at=now,
                updated_at=now,
                trial_ends_at=trial_ends_at,
                current_period_end=current_period_end,
                cancel_at_period_end=cancel_at_period_end,
                external_id=external_id,
                trial_used=trial_used,
            )
            await document.insert()
        else:
            document.tier = tier.value
            document.status = status.value
            document.billing_cycle = billing_cycle.value
            document.updated_at = now
            document.trial_ends_at = trial_ends_at
            document.current_period_end = current_period_end
            document.cancel_at_period_end = cancel_at_period_end
            # Só sobrescreve quando veio: uma troca de plano interna não pode
            # apagar o vínculo com a cobrança já criada no provedor.
            if external_id is not None:
                document.external_id = external_id
            # Só liga, nunca desliga: quem já usou o teste continua tendo usado
            # depois de cancelar e voltar para o Starter.
            document.trial_used = document.trial_used or trial_used
            await document.save()
        return _to_entity(document)

    async def get_by_external_id(self, external_id: str) -> Subscription | None:
        document = await SubscriptionDocument.find_one(
            SubscriptionDocument.external_id == external_id
        )
        return _to_entity(document) if document else None

    async def list_all(self) -> list[Subscription]:
        documents = await SubscriptionDocument.find_all().to_list()
        return [_to_entity(document) for document in documents]
