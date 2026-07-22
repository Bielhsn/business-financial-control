"""Geração de relatórios em CSV (puro, sem I/O).

Recebe as entidades já carregadas e devolve uma string CSV pronta para download.
Usa o dialeto padrão do módulo `csv` (aspas quando necessário), com cabeçalho em
português e valores monetários formatados com vírgula decimal (pt-BR).
"""

import csv
import io
from collections.abc import Iterable

from app.application.financial.accounts import AccountsSummary
from app.application.financial.income_statement import IncomeStatementComparison
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


def income_statement_csv(comparison: IncomeStatementComparison) -> str:
    """DRE do mês em CSV (Seção, Categoria, Valor) para o contador."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([f"DRE {comparison.month:02d}/{comparison.year}"])
    writer.writerow(["Seção", "Categoria", "Valor (R$)"])

    statement = comparison.current
    for line in statement.income_lines:
        writer.writerow(["Receita", line.category_name, _reais(line.amount_cents)])
    writer.writerow(["Total Receitas", "", _reais(statement.total_income_cents)])
    for line in statement.expense_lines:
        writer.writerow(["Despesa", line.category_name, _reais(line.amount_cents)])
    writer.writerow(["Total Despesas", "", _reais(statement.total_expense_cents)])
    writer.writerow(["Resultado", "", _reais(statement.net_result_cents)])

    writer.writerow([])
    writer.writerow(["Comparativo com o mês anterior", "Mês atual", "Mês anterior"])
    writer.writerow(
        ["Receitas", _reais(statement.total_income_cents), _reais(comparison.previous_income_cents)]
    )
    writer.writerow(
        [
            "Despesas",
            _reais(statement.total_expense_cents),
            _reais(comparison.previous_expense_cents),
        ]
    )
    writer.writerow(
        [
            "Resultado",
            _reais(statement.net_result_cents),
            _reais(comparison.previous_net_result_cents),
        ]
    )
    return buffer.getvalue()


def accounts_csv(summary: AccountsSummary) -> str:
    """Contas a pagar e a receber em CSV (para conferência/cobrança)."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Tipo", "Descrição", "Vencimento", "Situação", "Valor (R$)"])
    groups = (("A pagar", summary.payable.items), ("A receber", summary.receivable.items))
    for label, items in groups:
        for item in items:
            writer.writerow(
                [
                    label,
                    item.description,
                    _date(item.due_date),
                    "Vencido" if item.is_overdue else "A vencer",
                    _reais(item.amount_cents),
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
