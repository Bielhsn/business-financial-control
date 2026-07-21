from datetime import UTC, datetime

import pytest

from app.application.connector.connect_provider import ConnectProviderUseCase
from app.application.connector.sync_connection import SyncConnectionUseCase
from app.core.exceptions import ConnectorError, ValidationError
from app.domain.connector.entities import ConnectionStatus, NormalizedSale
from app.domain.financial.entities import FinancialCategoryType, TransactionStatus
from tests.fakes import (
    FakeConnectionRepository,
    FakeConnector,
    FakeFinancialCategoryRepository,
    FakeFinancialTransactionRepository,
    FakePlatformSaleRepository,
    FakeSecretCipher,
)

pytestmark = pytest.mark.anyio


def _sale(external_id: str, amount_cents: int, *, refund: bool = False) -> NormalizedSale:
    return NormalizedSale(
        external_id=external_id,
        description="Curso de Python",
        amount_cents=amount_cents,
        occurred_at=datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
        is_refund=refund,
        buyer_name="Maria",
        buyer_email="maria@example.com",
    )


async def _connect(
    connections: FakeConnectionRepository, connector: FakeConnector, cipher: FakeSecretCipher
) -> None:
    await ConnectProviderUseCase(connections, cipher, connector).execute(
        provider="hotmart",
        credentials={"client_id": "cid", "client_secret": "secret"},
    )


async def test_connect_validates_required_fields() -> None:
    with pytest.raises(ValidationError, match="Client Secret"):
        await ConnectProviderUseCase(
            FakeConnectionRepository(), FakeSecretCipher(), FakeConnector()
        ).execute(provider="hotmart", credentials={"client_id": "cid"})


async def test_connect_rejects_unknown_provider() -> None:
    with pytest.raises(ValidationError, match="não é suportado"):
        await ConnectProviderUseCase(
            FakeConnectionRepository(), FakeSecretCipher(), FakeConnector()
        ).execute(provider="inexistente", credentials={})


async def test_connect_encrypts_only_secret_fields() -> None:
    connections = FakeConnectionRepository()
    cipher = FakeSecretCipher()
    await _connect(connections, FakeConnector(), cipher)

    connection = await connections.get_by_provider("hotmart")
    assert connection is not None
    # client_id não é secreto → fica em config em texto puro.
    assert connection.config == {"client_id": "cid"}
    # client_secret é secreto → só existe criptografado.
    encrypted = await connections.get_encrypted_secrets("hotmart")
    assert encrypted is not None
    assert "secret" not in connection.config.values()
    assert "secret" in cipher.decrypt(encrypted)


async def test_sync_imports_sales_and_refunds_into_financial() -> None:
    connections = FakeConnectionRepository()
    cipher = FakeSecretCipher()
    connector = FakeConnector(sales=[_sale("HP1", 10000), _sale("HP2", 5000, refund=True)])
    await _connect(connections, connector, cipher)

    categories = FakeFinancialCategoryRepository()
    transactions = FakeFinancialTransactionRepository()
    result = await SyncConnectionUseCase(
        connections, categories, transactions, cipher, connector, FakePlatformSaleRepository()
    ).execute(provider="hotmart", created_by="user-1")

    assert result.imported == 2
    assert result.details == {"sales": 1, "refunds": 1}

    all_tx = await transactions.list_all()
    sale = next(t for t in all_tx if t.external_ref == "hotmart:HP1")
    assert sale.type == FinancialCategoryType.INCOME
    assert sale.status == TransactionStatus.PAID
    assert sale.amount_cents == 10000
    assert "Maria" in (sale.notes or "")
    refund = next(t for t in all_tx if t.external_ref == "hotmart:HP2")
    assert refund.type == FinancialCategoryType.EXPENSE


async def test_sync_is_idempotent() -> None:
    connections = FakeConnectionRepository()
    cipher = FakeSecretCipher()
    connector = FakeConnector(sales=[_sale("HP1", 10000)])
    await _connect(connections, connector, cipher)
    categories = FakeFinancialCategoryRepository()
    transactions = FakeFinancialTransactionRepository()
    use_case = SyncConnectionUseCase(
        connections, categories, transactions, cipher, connector, FakePlatformSaleRepository()
    )

    first = await use_case.execute(provider="hotmart", created_by="u")
    second = await use_case.execute(provider="hotmart", created_by="u")

    assert first.imported == 1
    assert second.imported == 0
    assert second.skipped == 1
    assert len(await transactions.list_all()) == 1


async def test_sync_marks_connection_error_on_connector_failure() -> None:
    connections = FakeConnectionRepository()
    cipher = FakeSecretCipher()
    connector = FakeConnector()
    await _connect(connections, connector, cipher)

    async def _boom(credentials: dict[str, str], *, since: object = None) -> list[NormalizedSale]:
        raise ConnectorError("Hotmart fora do ar.")

    connector.fetch_sales = _boom  # type: ignore[method-assign]
    categories = FakeFinancialCategoryRepository()
    transactions = FakeFinancialTransactionRepository()

    with pytest.raises(ConnectorError):
        await SyncConnectionUseCase(
            connections, categories, transactions, cipher, connector, FakePlatformSaleRepository()
        ).execute(provider="hotmart", created_by="u")

    connection = await connections.get_by_provider("hotmart")
    assert connection is not None
    assert connection.status == ConnectionStatus.ERROR
    assert connection.last_error == "Hotmart fora do ar."


async def test_sync_reuses_category_across_runs() -> None:
    connections = FakeConnectionRepository()
    cipher = FakeSecretCipher()
    connector = FakeConnector(sales=[_sale("HP1", 10000)])
    await _connect(connections, connector, cipher)
    categories = FakeFinancialCategoryRepository()
    transactions = FakeFinancialTransactionRepository()
    use_case = SyncConnectionUseCase(
        connections, categories, transactions, cipher, connector, FakePlatformSaleRepository()
    )

    await use_case.execute(provider="hotmart", created_by="u")
    connector._sales = [_sale("HP9", 20000)]  # nova venda, mesma categoria
    await use_case.execute(provider="hotmart", created_by="u")

    income_categories = [
        c for c in await categories.list_all() if c.type == FinancialCategoryType.INCOME
    ]
    assert sum(1 for c in income_categories if c.name == "Vendas Hotmart") == 1
