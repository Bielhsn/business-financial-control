from datetime import UTC, datetime

import pytest

from app.application.platform_sales.analytics import GetSalesAnalyticsUseCase, compute_analytics
from app.domain.platform_sales.entities import PlatformSale

pytestmark = pytest.mark.anyio


def _sale(
    external_id: str,
    *,
    provider: str = "hotmart",
    product: str = "Curso A",
    cents: int = 10000,
    hour: int = 20,
    refund: bool = False,
    buyer: str | None = "cliente@x.com",
) -> PlatformSale:
    return PlatformSale(
        id=external_id,
        company_id="c1",
        provider=provider,
        external_id=external_id,
        product=product,
        amount_cents=cents,
        occurred_at=datetime(2026, 7, 1, hour, 0, tzinfo=UTC),
        is_refund=refund,
        buyer_name=None,
        buyer_email=buyer,
        created_at=datetime.now(UTC),
    )


def test_totals_and_average_ticket() -> None:
    analytics = compute_analytics([_sale("1", cents=10000), _sale("2", cents=20000)])
    assert analytics.total_gross_cents == 30000
    assert analytics.total_orders == 2
    assert analytics.avg_ticket_cents == 15000
    assert analytics.total_net_cents == 30000


def test_refunds_are_separated_from_gross() -> None:
    analytics = compute_analytics([_sale("1", cents=10000), _sale("2", cents=3000, refund=True)])
    assert analytics.total_gross_cents == 10000
    assert analytics.total_refunds == 1
    assert analytics.total_refunds_cents == 3000
    assert analytics.total_net_cents == 7000
    # Reembolso não conta como pedido nem entra no ticket médio.
    assert analytics.total_orders == 1
    assert analytics.avg_ticket_cents == 10000


def test_top_products_ranked_by_revenue() -> None:
    analytics = compute_analytics(
        [
            _sale("1", product="Curso A", cents=10000),
            _sale("2", product="Curso B", cents=5000),
            _sale("3", product="Curso B", cents=5000),
            _sale("4", product="Curso A", cents=10000),
        ]
    )
    assert analytics.top_products[0].product == "Curso A"
    assert analytics.top_products[0].quantity == 2
    assert analytics.top_products[0].revenue_cents == 20000


def test_peak_hours_ranked_by_order_count() -> None:
    analytics = compute_analytics([_sale("1", hour=20), _sale("2", hour=20), _sale("3", hour=9)])
    assert analytics.peak_hours[0].hour == 20
    assert analytics.peak_hours[0].orders == 2


def test_by_platform_breakdown_and_unique_buyers() -> None:
    analytics = compute_analytics(
        [
            _sale("1", provider="hotmart", cents=10000, buyer="a@x.com"),
            _sale("2", provider="shopify", cents=30000, buyer="b@x.com"),
            _sale("3", provider="shopify", cents=10000, buyer="a@x.com"),
        ]
    )
    # Ordenado por bruto: shopify (40k) antes de hotmart (10k).
    assert analytics.by_platform[0].provider == "shopify"
    assert analytics.by_platform[0].gross_cents == 40000
    assert analytics.by_platform[0].avg_ticket_cents == 20000
    assert analytics.unique_buyers == 2  # a@x.com e b@x.com


async def test_use_case_reads_from_repository() -> None:
    from tests.fakes import FakePlatformSaleRepository

    repo = FakePlatformSaleRepository()
    await repo.upsert(
        provider="hotmart",
        external_id="1",
        product="Curso A",
        amount_cents=10000,
        occurred_at=datetime(2026, 7, 1, 20, 0, tzinfo=UTC),
        is_refund=False,
        buyer_name=None,
        buyer_email="a@x.com",
    )
    analytics = await GetSalesAnalyticsUseCase(repo).execute(days=None)
    assert analytics.total_orders == 1
    assert analytics.total_gross_cents == 10000
