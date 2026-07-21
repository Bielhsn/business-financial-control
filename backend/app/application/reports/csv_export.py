"""Geração de relatórios em CSV (puro, sem I/O).

Recebe as entidades já carregadas e devolve uma string CSV pronta para download.
Usa o dialeto padrão do módulo `csv` (aspas quando necessário), com cabeçalho em
português e valores monetários formatados com vírgula decimal (pt-BR).
"""

import csv
import io
from collections.abc import Iterable

from app.domain.financial.entities import FinancialCategoryType, FinancialTransaction
from app.domain.platform_sales.entities import PlatformSale

_TYPE_LABEL = {
    FinancialCategoryType.INCOME: "Receita",
    FinancialCategoryType.EXPENSE: "Despesa",
}


def _reais(amount_cents: int) -> str:
    return f"{amount_cents / 100:.2f}".replace(".", ",")


def _date(value: object) -> str:
    # value é datetime | None; formata como AAAA-MM-DD.
    return value.strftime("%Y-%m-%d") if value is not None else ""  # type: ignore[attr-defined]


def financial_transactions_csv(
    transactions: Iterable[FinancialTransaction], *, category_names: dict[str, str]
) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["Data", "Tipo", "Categoria", "Descrição", "Valor (R$)", "Status", "Observações"]
    )
    for tx in transactions:
        writer.writerow(
            [
                _date(tx.paid_at or tx.due_date or tx.created_at),
                _TYPE_LABEL.get(tx.type, tx.type),
                category_names.get(tx.category_id, ""),
                tx.description,
                _reais(tx.amount_cents),
                tx.status,
                tx.notes or "",
            ]
        )
    return buffer.getvalue()


def platform_sales_csv(sales: Iterable[PlatformSale]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Data", "Plataforma", "Produto", "Valor (R$)", "Tipo", "Cliente", "E-mail"])
    for sale in sales:
        writer.writerow(
            [
                _date(sale.occurred_at),
                sale.provider,
                sale.product,
                _reais(sale.amount_cents),
                "Reembolso" if sale.is_refund else "Venda",
                sale.buyer_name or "",
                sale.buyer_email or "",
            ]
        )
    return buffer.getvalue()
