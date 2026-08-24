"""Monta a sincronização agendada fora do ciclo de requisição.

O FastAPI resolve dependências por requisição; o agendador roda sem nenhuma.
Este módulo faz a montagem à mão, num lugar só, para o agendador não conhecer
repositórios nem cifra e para o `main.py` não virar um injetor improvisado.
"""

from datetime import timedelta

from app.application.connector.scheduled_sync import (
    SCHEDULER_ACTOR,
    ScheduledSyncReport,
    SyncDueConnectionsUseCase,
)
from app.application.connector.sync_connection import SyncConnectionUseCase
from app.core.config import Settings
from app.domain.connector.registry import get_connector_definition
from app.infrastructure.connectors.factory import build_connector, build_oauth_provider
from app.infrastructure.repositories.connection_repository import BeanieConnectionRepository
from app.infrastructure.repositories.financial_category_repository import (
    BeanieFinancialCategoryRepository,
)
from app.infrastructure.repositories.financial_transaction_repository import (
    BeanieFinancialTransactionRepository,
)
from app.infrastructure.repositories.platform_sale_repository import BeaniePlatformSaleRepository
from app.infrastructure.security.crypto import FernetSecretCipher


def build_scheduled_sync(settings: Settings) -> SyncDueConnectionsUseCase:
    connections = BeanieConnectionRepository()

    async def sync_for_company(_company_id: str, provider: str) -> None:
        # O contexto da empresa já foi definido por quem chamou — os
        # repositórios Beanie leem dele. Recebemos o id só para deixar a
        # dependência explícita na assinatura.
        definition = get_connector_definition(provider)
        oauth_provider = (
            build_oauth_provider(provider, settings)
            if definition is not None and definition.auth_type == "oauth"
            else None
        )
        await SyncConnectionUseCase(
            connections,
            BeanieFinancialCategoryRepository(),
            BeanieFinancialTransactionRepository(),
            FernetSecretCipher(settings),
            build_connector(provider, settings),
            BeaniePlatformSaleRepository(),
            oauth_provider,
        ).execute(provider=provider, created_by=SCHEDULER_ACTOR)

    return SyncDueConnectionsUseCase(
        connections,
        sync_for_company,
        # Uma conexão é considerada vencida depois de um intervalo inteiro sem
        # sincronizar. Reusar o mesmo número evita a rodada seguinte tentar de
        # novo o que acabou de rodar.
        stale_after=timedelta(minutes=settings.sync_interval_minutes),
    )


async def run_scheduled_sync(settings: Settings) -> ScheduledSyncReport:
    return await build_scheduled_sync(settings).execute()
