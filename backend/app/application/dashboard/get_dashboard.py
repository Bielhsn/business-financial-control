from datetime import datetime

from app.core.exceptions import ValidationError
from app.domain.blueprint.repository import CompanyBlueprintRepository
from app.domain.dashboard.entities import (
    CategoryBreakdown,
    ComputedKPI,
    DashboardSummary,
    MonthlyBreakdown,
    PeriodComparison,
)
from app.domain.dashboard.kpi_registry import KPIMetric, get_kpi_metric_unit
from app.domain.financial.entities import FinancialCategoryType, FinancialTransaction
from app.domain.financial.repository import (
    FinancialCategoryRepository,
    FinancialTransactionRepository,
)


def _sum_by_type(transactions: list[FinancialTransaction], type_: FinancialCategoryType) -> int:
    return sum(t.amount_cents for t in transactions if t.type == type_)


def _pct_change(old: int, new: int) -> float | None:
    if old == 0:
        return None
    return ((new - old) / abs(old)) * 100


def _month_start(value: datetime) -> datetime:
    return value.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _add_months(value: datetime, delta_months: int) -> datetime:
    month_index = value.month - 1 + delta_months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    return value.replace(year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0)


class GetDashboardUseCase:
    """Busca os lançamentos pagos uma única vez (maior janela necessária) e deriva
    todos os agregados em memória — suficiente para o volume de uma única empresa
    nesta etapa; migrar para um pipeline de agregação do MongoDB é a otimização
    natural quando o volume de lançamentos crescer."""

    def __init__(
        self,
        transaction_repository: FinancialTransactionRepository,
        category_repository: FinancialCategoryRepository,
        blueprint_repository: CompanyBlueprintRepository,
    ) -> None:
        self._transaction_repository = transaction_repository
        self._category_repository = category_repository
        self._blueprint_repository = blueprint_repository

    async def execute(
        self, *, company_id: str, start: datetime, end: datetime, months: int = 6
    ) -> DashboardSummary:
        if end <= start:
            raise ValidationError("A data final deve ser posterior à data inicial.")
        if months < 1:
            raise ValidationError("A janela de evolução mensal deve ter ao menos 1 mês.")

        duration = end - start
        previous_start = start - duration
        previous_end = start
        monthly_window_start = _add_months(_month_start(end), -(months - 1))

        fetch_start = min(previous_start, monthly_window_start)
        all_transactions = await self._transaction_repository.list_paid_between(
            start=fetch_start, end=end
        )

        current = [t for t in all_transactions if start <= _paid_at(t) <= end]
        previous = [t for t in all_transactions if previous_start <= _paid_at(t) < previous_end]
        monthly_source = [t for t in all_transactions if monthly_window_start <= _paid_at(t) <= end]

        revenue_cents = _sum_by_type(current, FinancialCategoryType.INCOME)
        expense_cents = _sum_by_type(current, FinancialCategoryType.EXPENSE)
        profit_cents = revenue_cents - expense_cents
        profit_margin_pct = (profit_cents / revenue_cents * 100) if revenue_cents else None

        income_transactions = [t for t in current if t.type == FinancialCategoryType.INCOME]
        average_ticket_cents = (
            round(sum(t.amount_cents for t in income_transactions) / len(income_transactions))
            if income_transactions
            else 0
        )
        transaction_count = len(current)
        active_clients = len({t.client_id for t in current if t.client_id})

        categories = await self._category_repository.list_all(only_active=False)
        category_names = {category.id: category.name for category in categories}

        prev_revenue = _sum_by_type(previous, FinancialCategoryType.INCOME)
        prev_expense = _sum_by_type(previous, FinancialCategoryType.EXPENSE)
        comparison = PeriodComparison(
            revenue_change_pct=_pct_change(prev_revenue, revenue_cents),
            expense_change_pct=_pct_change(prev_expense, expense_cents),
            profit_change_pct=_pct_change(prev_revenue - prev_expense, profit_cents),
        )

        computed_values: dict[KPIMetric, float] = {
            KPIMetric.TOTAL_REVENUE: float(revenue_cents),
            KPIMetric.TOTAL_EXPENSES: float(expense_cents),
            KPIMetric.PROFIT: float(profit_cents),
            KPIMetric.PROFIT_MARGIN: profit_margin_pct or 0.0,
            KPIMetric.AVERAGE_TICKET: float(average_ticket_cents),
            KPIMetric.TRANSACTION_COUNT: float(transaction_count),
            KPIMetric.ACTIVE_CLIENTS: float(active_clients),
        }

        blueprint = await self._blueprint_repository.get_by_company_id(company_id)
        kpis = (
            [
                ComputedKPI(
                    key=kpi_def.key,
                    name=kpi_def.name,
                    description=kpi_def.description,
                    metric=kpi_def.metric,
                    unit=get_kpi_metric_unit(kpi_def.metric),
                    value=computed_values[kpi_def.metric],
                )
                for kpi_def in blueprint.kpis
            ]
            if blueprint is not None
            else []
        )

        return DashboardSummary(
            start=start,
            end=end,
            revenue_cents=revenue_cents,
            expense_cents=expense_cents,
            profit_cents=profit_cents,
            profit_margin_pct=profit_margin_pct,
            average_ticket_cents=average_ticket_cents,
            transaction_count=transaction_count,
            active_clients=active_clients,
            monthly_breakdown=_build_monthly_breakdown(monthly_source, monthly_window_start, end),
            top_income_categories=_top_categories(
                current, FinancialCategoryType.INCOME, category_names
            ),
            top_expense_categories=_top_categories(
                current, FinancialCategoryType.EXPENSE, category_names
            ),
            comparison=comparison,
            kpis=kpis,
        )


def _paid_at(transaction: FinancialTransaction) -> datetime:
    assert transaction.paid_at is not None
    return transaction.paid_at


def _build_monthly_breakdown(
    transactions: list[FinancialTransaction], window_start: datetime, end: datetime
) -> list[MonthlyBreakdown]:
    buckets: dict[tuple[int, int], MonthlyBreakdown] = {}
    cursor = window_start
    end_month = _month_start(end)
    while cursor <= end_month:
        buckets[(cursor.year, cursor.month)] = MonthlyBreakdown(
            year=cursor.year,
            month=cursor.month,
            revenue_cents=0,
            expense_cents=0,
            profit_cents=0,
        )
        cursor = _add_months(cursor, 1)

    for transaction in transactions:
        key = (_paid_at(transaction).year, _paid_at(transaction).month)
        bucket = buckets.get(key)
        if bucket is None:
            continue
        if transaction.type == FinancialCategoryType.INCOME:
            bucket.revenue_cents += transaction.amount_cents
        else:
            bucket.expense_cents += transaction.amount_cents
        bucket.profit_cents = bucket.revenue_cents - bucket.expense_cents

    return [buckets[key] for key in sorted(buckets)]


def _top_categories(
    transactions: list[FinancialTransaction],
    type_: FinancialCategoryType,
    category_names: dict[str, str],
    limit: int = 5,
) -> list[CategoryBreakdown]:
    totals: dict[str, int] = {}
    for transaction in transactions:
        if transaction.type != type_:
            continue
        totals[transaction.category_id] = totals.get(transaction.category_id, 0) + (
            transaction.amount_cents
        )

    breakdown = [
        CategoryBreakdown(
            category_id=category_id,
            category_name=category_names.get(category_id, "Categoria removida"),
            total_cents=total_cents,
        )
        for category_id, total_cents in totals.items()
    ]
    breakdown.sort(key=lambda item: item.total_cents, reverse=True)
    return breakdown[:limit]
