from dataclasses import dataclass
from datetime import datetime

from app.domain.financial.entities import (
    FinancialCategory,
    FinancialCategoryType,
    FinancialTransaction,
    TransactionStatus,
)
from app.domain.financial.repository import (
    FinancialCategoryRepository,
    FinancialTransactionRepository,
)

_DEFAULT_CATEGORY_NAME = "Importados"


@dataclass
class ImportRow:
    """Linha normalizada de importação (extrato bancário, planilha, export de app).

    `amount_cents` é assinado: positivo vira receita, negativo vira despesa —
    convenção universal de extratos.
    """

    date: datetime
    description: str
    amount_cents: int
    category_name: str | None = None
    paid: bool = True


@dataclass
class ImportResult:
    imported: int
    categories_created: int


class ImportTransactionsUseCase:
    """Importa lançamentos em lote, criando categorias sob demanda.

    Categorias são resolvidas por (nome, tipo) sem diferenciar maiúsculas — a
    mesma categoria de planilhas diferentes ("Vendas" / "vendas") não duplica.
    Linhas sem categoria caem em uma categoria padrão de importação, que o
    usuário pode renomear depois.
    """

    def __init__(
        self,
        category_repository: FinancialCategoryRepository,
        transaction_repository: FinancialTransactionRepository,
    ) -> None:
        self._category_repository = category_repository
        self._transaction_repository = transaction_repository

    async def execute(self, *, rows: list[ImportRow], created_by: str) -> ImportResult:
        existing = await self._category_repository.list_all(only_active=False)
        by_key: dict[tuple[str, FinancialCategoryType], FinancialCategory] = {
            (category.name.casefold(), category.type): category for category in existing
        }
        categories_created = 0
        imported = 0

        for row in rows:
            type_ = (
                FinancialCategoryType.INCOME
                if row.amount_cents > 0
                else FinancialCategoryType.EXPENSE
            )
            name = (row.category_name or _DEFAULT_CATEGORY_NAME).strip() or _DEFAULT_CATEGORY_NAME
            key = (name.casefold(), type_)
            category = by_key.get(key)
            if category is None:
                category = await self._category_repository.create(name=name, type=type_)
                by_key[key] = category
                categories_created += 1

            await self._create_transaction(row, category, type_, created_by)
            imported += 1

        return ImportResult(imported=imported, categories_created=categories_created)

    async def _create_transaction(
        self,
        row: ImportRow,
        category: FinancialCategory,
        type_: FinancialCategoryType,
        created_by: str,
    ) -> FinancialTransaction:
        return await self._transaction_repository.create(
            category_id=category.id,
            type=type_,
            amount_cents=abs(row.amount_cents),
            description=row.description.strip(),
            status=TransactionStatus.PAID if row.paid else TransactionStatus.PENDING,
            due_date=None if row.paid else row.date,
            paid_at=row.date if row.paid else None,
            notes=None,
            client_id=None,
            created_by=created_by,
        )
