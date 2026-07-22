from datetime import UTC, datetime

from app.application.financial.accounts import compute_accounts
from app.application.financial.income_statement import (
    IncomeStatementComparison,
    compute_income_statement,
)
from app.application.reports.csv_export import (
    accounts_csv,
    financial_transactions_csv,
    income_statement_csv,
    platform_sales_csv,
)
from app.domain.financial.entities import (
    FinancialCategoryType,
    FinancialTransaction,
    TransactionStatus,
)
from app.domain.platform_sales.entities import PlatformSale


def _tx() -> FinancialTransaction:
    now = datetime(2026, 7, 1, tzinfo=UTC)
    return FinancialTransaction(
        id="1",
        company_id="c1",
        category_id="cat1",
        type=FinancialCategoryType.INCOME,
        amount_cents=123456,
        description="Venda de curso",
        status=TransactionStatus.PAID,
        due_date=None,
        paid_at=now,
        notes="cliente vip",
        client_id=None,
        created_by="u",
        created_at=now,
        updated_at=now,
        external_ref=None,
    )


def test_financial_csv_has_header_and_formatted_values() -> None:
    csv_text = financial_transactions_csv([_tx()], category_names={"cat1": "Vendas"})
    lines = csv_text.strip().splitlines()
    assert lines[0] == "Data,Tipo,Categoria,Descrição,Valor (R$),Status,Observações"
    assert "2026-07-01" in lines[1]
    assert "Receita" in lines[1]
    assert "Vendas" in lines[1]
    assert "1234,56" in lines[1]  # vírgula decimal pt-BR


def test_financial_csv_quotes_values_with_commas() -> None:
    tx = _tx()
    tx.description = "Curso A, B e C"
    csv_text = financial_transactions_csv([tx], category_names={})
    assert '"Curso A, B e C"' in csv_text


def _paid(category_id: str, type: FinancialCategoryType, amount_cents: int) -> FinancialTransaction:
    now = datetime(2026, 7, 1, tzinfo=UTC)
    return FinancialTransaction(
        id=f"{category_id}-{amount_cents}",
        company_id="c1",
        category_id=category_id,
        type=type,
        amount_cents=amount_cents,
        description="x",
        status=TransactionStatus.PAID,
        due_date=None,
        paid_at=now,
        notes=None,
        client_id=None,
        created_by="u",
        created_at=now,
        updated_at=now,
    )


def test_income_statement_csv_has_totals_and_comparison() -> None:
    statement = compute_income_statement(
        [
            _paid("c1", FinancialCategoryType.INCOME, 20000),
            _paid("e1", FinancialCategoryType.EXPENSE, 7000),
        ],
        {"c1": "Vendas", "e1": "Aluguel"},
    )
    comparison = IncomeStatementComparison(
        year=2026,
        month=7,
        current=statement,
        previous_income_cents=10000,
        previous_expense_cents=5000,
        previous_net_result_cents=5000,
        income_change_pct=100.0,
        expense_change_pct=40.0,
        net_change_pct=160.0,
    )
    csv_text = income_statement_csv(comparison)
    assert "DRE 07/2026" in csv_text
    # Valores com vírgula decimal saem entre aspas no CSV.
    assert 'Total Receitas,,"200,00"' in csv_text
    assert 'Resultado,,"130,00"' in csv_text
    assert "Comparativo com o mês anterior" in csv_text


def test_accounts_csv_lists_payable_and_receivable() -> None:
    summary = compute_accounts(
        [
            _tx_pending("A pagar atrasado", FinancialCategoryType.EXPENSE, 5000, days=-3),
            _tx_pending("A receber futuro", FinancialCategoryType.INCOME, 8000, days=10),
        ],
        today=datetime(2026, 7, 20, tzinfo=UTC),
    )
    csv_text = accounts_csv(summary)
    lines = csv_text.strip().splitlines()
    assert lines[0] == "Tipo,Descrição,Vencimento,Situação,Valor (R$)"
    assert any(line.startswith("A pagar,") and "Vencido" in line for line in lines)
    assert any(line.startswith("A receber,") and "A vencer" in line for line in lines)


def _tx_pending(
    description: str, type: FinancialCategoryType, amount_cents: int, *, days: int
) -> FinancialTransaction:
    from datetime import timedelta

    today = datetime(2026, 7, 20, tzinfo=UTC)
    return FinancialTransaction(
        id=description,
        company_id="c1",
        category_id="cat",
        type=type,
        amount_cents=amount_cents,
        description=description,
        status=TransactionStatus.PENDING,
        due_date=today + timedelta(days=days),
        paid_at=None,
        notes=None,
        client_id=None,
        created_by="u",
        created_at=today,
        updated_at=today,
    )


def test_platform_sales_csv() -> None:
    sale = PlatformSale(
        id="1",
        company_id="c1",
        provider="hotmart",
        external_id="HP1",
        product="Curso X",
        amount_cents=9900,
        occurred_at=datetime(2026, 7, 2, tzinfo=UTC),
        is_refund=True,
        buyer_name="Maria",
        buyer_email="maria@x.com",
        created_at=datetime.now(UTC),
    )
    csv_text = platform_sales_csv([sale])
    lines = csv_text.strip().splitlines()
    assert lines[0].startswith("Data,Plataforma,Produto")
    assert "hotmart" in lines[1]
    assert "Reembolso" in lines[1]
    assert "99,00" in lines[1]
