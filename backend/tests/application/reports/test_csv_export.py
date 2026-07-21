from datetime import UTC, datetime

from app.application.reports.csv_export import (
    financial_transactions_csv,
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
