"""Calcula as métricas de vendas por plataforma a partir das vendas guardadas.

Toda a matemática (ticket médio, produtos mais vendidos, horários de pico,
reembolsos, indicadores por plataforma) é feita em Python puro sobre a lista de
vendas — fácil de testar. As consultas ao banco ficam no repositório.
"""

from collections import defaultdict
from datetime import UTC, datetime, timedelta

from app.domain.platform_sales.entities import (
    PeakHour,
    PlatformMetric,
    PlatformSale,
    SalesAnalytics,
    TopProduct,
)
from app.domain.platform_sales.repository import PlatformSaleRepository

_TOP_PRODUCTS_LIMIT = 5
_PEAK_HOURS_LIMIT = 5


def _avg(total_cents: int, count: int) -> int:
    return round(total_cents / count) if count else 0


def compute_analytics(sales: list[PlatformSale]) -> SalesAnalytics:
    gross = refunds_cents = orders = refunds = 0
    buyers: set[str] = set()

    by_provider_gross: dict[str, int] = defaultdict(int)
    by_provider_refunds_cents: dict[str, int] = defaultdict(int)
    by_provider_orders: dict[str, int] = defaultdict(int)
    by_provider_refunds: dict[str, int] = defaultdict(int)

    product_qty: dict[str, int] = defaultdict(int)
    product_rev: dict[str, int] = defaultdict(int)
    hour_orders: dict[int, int] = defaultdict(int)

    for sale in sales:
        buyer_key = sale.buyer_email or sale.buyer_name
        if buyer_key:
            buyers.add(buyer_key.strip().lower())

        if sale.is_refund:
            refunds += 1
            refunds_cents += sale.amount_cents
            by_provider_refunds[sale.provider] += 1
            by_provider_refunds_cents[sale.provider] += sale.amount_cents
            continue

        orders += 1
        gross += sale.amount_cents
        by_provider_orders[sale.provider] += 1
        by_provider_gross[sale.provider] += sale.amount_cents
        product_qty[sale.product] += 1
        product_rev[sale.product] += sale.amount_cents
        hour_orders[_as_utc(sale.occurred_at).hour] += 1

    providers = sorted(
        set(by_provider_orders) | set(by_provider_refunds),
        key=lambda p: by_provider_gross[p],
        reverse=True,
    )
    by_platform = [
        PlatformMetric(
            provider=provider,
            gross_cents=by_provider_gross[provider],
            refunds_cents=by_provider_refunds_cents[provider],
            net_cents=by_provider_gross[provider] - by_provider_refunds_cents[provider],
            orders=by_provider_orders[provider],
            refunds=by_provider_refunds[provider],
            avg_ticket_cents=_avg(by_provider_gross[provider], by_provider_orders[provider]),
        )
        for provider in providers
    ]

    top_products = [
        TopProduct(product=name, quantity=product_qty[name], revenue_cents=product_rev[name])
        for name in sorted(
            product_qty, key=lambda n: (product_rev[n], product_qty[n]), reverse=True
        )[:_TOP_PRODUCTS_LIMIT]
    ]

    peak_hours = [
        PeakHour(hour=hour, orders=count)
        for hour, count in sorted(hour_orders.items(), key=lambda kv: kv[1], reverse=True)[
            :_PEAK_HOURS_LIMIT
        ]
    ]

    return SalesAnalytics(
        total_gross_cents=gross,
        total_refunds_cents=refunds_cents,
        total_net_cents=gross - refunds_cents,
        total_orders=orders,
        total_refunds=refunds,
        avg_ticket_cents=_avg(gross, orders),
        unique_buyers=len(buyers),
        by_platform=by_platform,
        top_products=top_products,
        peak_hours=peak_hours,
    )


class GetSalesAnalyticsUseCase:
    def __init__(self, platform_sale_repository: PlatformSaleRepository) -> None:
        self._repository = platform_sale_repository

    async def execute(
        self, *, days: int | None = 30, now: datetime | None = None
    ) -> SalesAnalytics:
        since: datetime | None = None
        if days is not None:
            since = (now or datetime.now(UTC)) - timedelta(days=days)
        sales = await self._repository.list_since(since)
        return compute_analytics(sales)


def _as_utc(moment: datetime) -> datetime:
    return moment if moment.tzinfo else moment.replace(tzinfo=UTC)
