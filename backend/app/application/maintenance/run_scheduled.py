"""Job de manutenção agendável: roda tarefas periódicas para TODAS as empresas.

Hoje materializa as recorrências vencidas (Etapa 41) de cada empresa. É pensado
para ser chamado por um cron externo (system cron, CronJob do Kubernetes, etc.),
não por um scheduler embutido — assim evita-se a duplicação quando o backend roda
com múltiplos workers, e o job continua idempotente (rodar de novo não duplica).

Cross-tenant por natureza: itera os ids de todas as empresas e, para cada uma,
fixa o contexto de tenant antes de gerar — mantendo o isolamento que o resto do
sistema garante por empresa."""

from dataclasses import dataclass, field
from datetime import datetime

from app.application.recurring.generate_due import GenerateDueRecurringUseCase
from app.core.tenant import set_current_company_id
from app.domain.company.repository import CompanyRepository
from app.domain.financial.repository import FinancialTransactionRepository
from app.domain.recurring.repository import RecurringTransactionRepository

# `created_by` dos lançamentos gerados pelo sistema (não por um usuário).
SYSTEM_ACTOR = "system"


@dataclass
class MaintenanceResult:
    companies: int = 0
    recurring_created: int = 0
    per_company: dict[str, int] = field(default_factory=dict)


class RunScheduledMaintenanceUseCase:
    def __init__(
        self,
        company_repository: CompanyRepository,
        recurring_repository: RecurringTransactionRepository,
        transaction_repository: FinancialTransactionRepository,
    ) -> None:
        self._companies = company_repository
        self._generate = GenerateDueRecurringUseCase(recurring_repository, transaction_repository)

    async def execute(self, *, as_of: datetime) -> MaintenanceResult:
        company_ids = await self._companies.list_all_ids()
        result = MaintenanceResult(companies=len(company_ids))

        for company_id in company_ids:
            # Isola cada empresa antes de gerar — os repositórios leem o tenant
            # do contexto, então nada vaza entre empresas.
            set_current_company_id(company_id)
            generated = await self._generate.execute(as_of=as_of, created_by=SYSTEM_ACTOR)
            if generated.created:
                result.per_company[company_id] = generated.created
                result.recurring_created += generated.created

        return result
