from app.domain.admin.metrics import CompanySummary, ConnectionSummary, FinancialTotals
from app.domain.financial.entities import FinancialCategoryType, TransactionStatus
from app.infrastructure.database.models.company import CompanyDocument
from app.infrastructure.database.models.connection import ConnectionDocument
from app.infrastructure.database.models.financial_transaction import (
    FinancialTransactionDocument,
)
from app.infrastructure.database.models.user import UserDocument


class BeanieAdminMetricsRepository:
    """Consultas cross-tenant do painel administrativo. Não aplica escopo de
    empresa — pressupõe que o chamador já validou ser super-admin."""

    async def list_companies(self) -> list[CompanySummary]:
        documents = await CompanyDocument.find_all().to_list()
        return [
            CompanySummary(
                id=str(doc.id),
                name=doc.name,
                segment=doc.segment,
                is_active=doc.is_active,
                created_at=doc.created_at,
            )
            for doc in documents
        ]

    async def count_users(self) -> int:
        return await UserDocument.find_all().count()

    async def list_connections(self) -> list[ConnectionSummary]:
        documents = await ConnectionDocument.find_all().to_list()
        return [ConnectionSummary(provider=doc.provider, status=doc.status) for doc in documents]

    async def financial_totals(self) -> FinancialTotals:
        # Considera apenas lançamentos realizados (pagos) — caixa efetivo.
        pipeline = [
            {"$match": {"status": TransactionStatus.PAID.value}},
            {"$group": {"_id": "$type", "total": {"$sum": "$amount_cents"}}},
        ]
        rows = await FinancialTransactionDocument.aggregate(pipeline).to_list()
        totals = {row["_id"]: row["total"] for row in rows}
        return FinancialTotals(
            income_cents=int(totals.get(FinancialCategoryType.INCOME.value, 0)),
            expense_cents=int(totals.get(FinancialCategoryType.EXPENSE.value, 0)),
        )
