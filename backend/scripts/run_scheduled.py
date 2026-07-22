"""Executa as tarefas de manutenção periódicas (uma passada) contra o banco real.

Pensado para um cron externo — por exemplo, uma vez por dia:

    0 6 * * *  cd /app && python -m scripts.run_scheduled

Ou dentro do container em produção:

    docker compose -f infra/docker-compose.prod.yml exec \\
        backend python -m scripts.run_scheduled

Hoje materializa as recorrências vencidas de todas as empresas. É idempotente:
rodar de novo não duplica lançamentos."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from app.application.maintenance.run_scheduled import RunScheduledMaintenanceUseCase
from app.infrastructure.database.mongodb import (
    close_mongo_connection,
    connect_to_mongo,
)
from app.infrastructure.repositories.company_repository import BeanieCompanyRepository
from app.infrastructure.repositories.financial_transaction_repository import (
    BeanieFinancialTransactionRepository,
)
from app.infrastructure.repositories.recurring_transaction_repository import (
    BeanieRecurringTransactionRepository,
)


async def _run() -> None:
    await connect_to_mongo()
    try:
        use_case = RunScheduledMaintenanceUseCase(
            BeanieCompanyRepository(),
            BeanieRecurringTransactionRepository(),
            BeanieFinancialTransactionRepository(),
        )
        result = await use_case.execute(as_of=datetime.now(UTC))
    finally:
        await close_mongo_connection()

    print(
        f"Manutenção concluída: {result.companies} empresa(s) verificada(s), "
        f"{result.recurring_created} lançamento(s) recorrente(s) gerado(s)."
    )


def main() -> int:
    asyncio.run(_run())
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
