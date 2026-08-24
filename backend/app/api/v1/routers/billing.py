"""Cobrança: iniciar assinatura paga e receber avisos do provedor.

O webhook fica **fora** do escopo de empresa e sem autenticação de usuário — quem
chama é o Asaas, não uma pessoa logada. Em troca, ele exige o token combinado:
sem essa verificação, qualquer um que descubra a URL marca a própria assinatura
como paga.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request, status

from app.api.v1.deps import (
    get_billing_provider,
    get_company_repository,
    get_current_user,
    get_subscription_repository,
    require_role,
)
from app.application.subscription.apply_billing_event import ApplyBillingEventUseCase
from app.core.exceptions import NotFoundError, UnauthorizedError, ValidationError
from app.core.logging import get_logger
from app.core.rate_limit import limiter
from app.core.tenant import CompanyContext
from app.domain.billing.ports import BillingProvider
from app.domain.company.repository import CompanyRepository
from app.domain.company.roles import CompanyRole
from app.domain.subscription.entities import BillingCycle, SubscriptionStatus
from app.domain.subscription.plans import PlanTier, get_plan
from app.domain.subscription.repository import SubscriptionRepository
from app.domain.user.entities import User
from app.schemas.billing import CheckoutRequest, CheckoutResponse

logger = get_logger(__name__)

router = APIRouter(tags=["billing"])


@router.post("/companies/{company_id}/billing/checkout", response_model=CheckoutResponse)
async def start_checkout(
    payload: CheckoutRequest,
    # Só o dono contrata: mudar o que a empresa paga não é decisão de qualquer
    # membro da equipe.
    company_context: Annotated[CompanyContext, Depends(require_role(CompanyRole.OWNER))],
    current_user: Annotated[User, Depends(get_current_user)],
    company_repository: Annotated[CompanyRepository, Depends(get_company_repository)],
    subscription_repository: Annotated[
        SubscriptionRepository, Depends(get_subscription_repository)
    ],
    billing: Annotated[BillingProvider, Depends(get_billing_provider)],
) -> CheckoutResponse:
    if payload.tier == PlanTier.STARTER:
        raise ValidationError("O plano gratuito não precisa de cobrança.")

    company = await company_repository.get_by_id(company_context.company_id)
    if company is None:
        raise NotFoundError("Empresa não encontrada.")
    if not company.cnpj:
        # O Asaas exige CPF/CNPJ do pagador. Empresas antigas foram criadas sem
        # ele — a mensagem precisa dizer onde resolver.
        raise ValidationError(
            "Informe o CNPJ da empresa nas configurações antes de contratar um plano."
        )

    plan = get_plan(payload.tier)
    price_cents = (
        plan.price_cents_yearly
        if payload.billing_cycle == BillingCycle.YEARLY
        else plan.price_cents_monthly
    )

    anterior = await subscription_repository.get_by_company(company.id)
    if anterior is not None and anterior.external_id:
        # Trocar de plano cria uma assinatura nova no Asaas. Sem encerrar a
        # antiga, quem faz upgrade passa a ser cobrado duas vezes por mês — e
        # descobre pela fatura, não pelo sistema.
        await billing.cancel_subscription(anterior.external_id)

    sessao = await billing.create_subscription(
        company_id=company.id,
        company_name=company.name,
        cnpj=company.cnpj,
        payer_email=current_user.email,
        tier=payload.tier,
        billing_cycle=payload.billing_cycle,
        price_cents=price_cents,
    )

    # Guarda o vínculo ANTES de o pagamento acontecer: se o webhook chegasse
    # primeiro e não encontrasse a assinatura, o pagamento não viraria acesso.
    # O status só muda quando o dinheiro entra — quem decide é o webhook.
    await subscription_repository.upsert(
        company_id=company.id,
        tier=payload.tier,
        status=SubscriptionStatus.PAST_DUE,
        billing_cycle=payload.billing_cycle,
        trial_ends_at=None,
        current_period_end=None,
        cancel_at_period_end=False,
        external_id=sessao.external_id,
        trial_used=anterior.trial_used if anterior else False,
    )
    return CheckoutResponse(payment_url=sessao.payment_url)


@router.post("/billing/webhook", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("120/minute")
async def billing_webhook(
    request: Request,
    subscription_repository: Annotated[
        SubscriptionRepository, Depends(get_subscription_repository)
    ],
    billing: Annotated[BillingProvider, Depends(get_billing_provider)],
    asaas_access_token: Annotated[str | None, Header(alias="asaas-access-token")] = None,
) -> None:
    if not billing.verify_webhook(token=asaas_access_token):
        logger.warning("billing_webhook_rejected")
        raise UnauthorizedError("Webhook não autenticado.")

    payload = await request.json()
    evento = billing.parse_webhook(payload)
    if evento is None:
        # Evento que não muda direito de acesso. Responder 204 encerra a
        # entrega; devolver erro faria o provedor reenviar para sempre.
        return

    await ApplyBillingEventUseCase(subscription_repository).execute(evento)
