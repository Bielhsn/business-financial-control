from datetime import UTC, datetime

from app.application.dashboard.get_dashboard import GetDashboardUseCase
from app.domain.advisor.entities import BusinessSignal, SignalKind, SignalSeverity
from app.domain.catalog.entities import CatalogItemKind
from app.domain.catalog.repository import CatalogItemRepository
from app.domain.financial.entities import TransactionStatus
from app.domain.financial.repository import FinancialTransactionRepository

# Limites deliberadamente simples e explicáveis — o usuário precisa entender
# por que um sinal apareceu. Sofisticação estatística fica para depois.
_LOW_MARGIN_PCT = 15.0
_REVENUE_DROP_RATIO = 0.7
_MAX_SIGNALS_PER_KIND = 5
_HISTORY_MONTHS = 6


def _month_start(reference: datetime, months_back: int) -> datetime:
    year = reference.year
    month = reference.month - months_back
    while month <= 0:
        month += 12
        year -= 1
    return datetime(year, month, 1, tzinfo=UTC)


class ComputeBusinessSignalsUseCase:
    """Sinais de negócio 100% determinísticos, calculados dos dados da empresa.

    Nenhuma chamada de IA aqui: o endpoint de sinais é barato e pode ser
    consultado à vontade; só a narração de recomendações (use case separado)
    consome tokens."""

    def __init__(
        self,
        item_repository: CatalogItemRepository,
        transaction_repository: FinancialTransactionRepository,
        dashboard_use_case: GetDashboardUseCase,
    ) -> None:
        self._item_repository = item_repository
        self._transaction_repository = transaction_repository
        self._dashboard_use_case = dashboard_use_case

    async def execute(self, *, company_id: str) -> list[BusinessSignal]:
        signals: list[BusinessSignal] = []
        signals.extend(await self._stock_signals())
        signals.extend(await self._margin_signals())
        signals.extend(await self._revenue_signals(company_id))
        signals.extend(await self._overdue_signals())
        return signals

    async def _stock_signals(self) -> list[BusinessSignal]:
        items = await self._item_repository.list_all(only_active=True)
        zero: list[BusinessSignal] = []
        low: list[BusinessSignal] = []
        for item in items:
            if item.kind != CatalogItemKind.PRODUCT or not item.tracks_inventory:
                continue
            stock = item.stock_quantity or 0
            if stock <= 0:
                zero.append(
                    BusinessSignal(
                        kind=SignalKind.STOCK_ZERO,
                        severity=SignalSeverity.CRITICAL,
                        title=f"Estoque zerado: {item.name}",
                        detail="Produto ativo sem nenhuma unidade em estoque — vendas "
                        "deste item estão paradas até a reposição.",
                    )
                )
            elif item.min_stock is not None and stock <= item.min_stock:
                low.append(
                    BusinessSignal(
                        kind=SignalKind.STOCK_LOW,
                        severity=SignalSeverity.WARNING,
                        title=f"Estoque abaixo do mínimo: {item.name}",
                        detail=f"Restam {stock} unidades (mínimo configurado: "
                        f"{item.min_stock}). Considere repor antes de faltar.",
                    )
                )
        return zero[:_MAX_SIGNALS_PER_KIND] + low[:_MAX_SIGNALS_PER_KIND]

    async def _margin_signals(self) -> list[BusinessSignal]:
        items = await self._item_repository.list_all(only_active=True)
        signals: list[BusinessSignal] = []
        for item in items:
            if item.cost_price_cents is None:
                continue
            effective_price = item.promo_price_cents or item.price_cents
            if effective_price <= 0:
                continue
            margin_pct = (effective_price - item.cost_price_cents) / effective_price * 100
            if margin_pct < _LOW_MARGIN_PCT:
                signals.append(
                    BusinessSignal(
                        kind=SignalKind.LOW_MARGIN,
                        severity=SignalSeverity.WARNING,
                        title=f"Margem apertada: {item.name}",
                        detail=f"Margem de {margin_pct:.1f}% sobre o preço efetivo de "
                        f"venda (referência mínima: {_LOW_MARGIN_PCT:.0f}%). Revise "
                        "custo, preço ou promoção.",
                    )
                )
        return signals[:_MAX_SIGNALS_PER_KIND]

    async def _revenue_signals(self, company_id: str) -> list[BusinessSignal]:
        now = datetime.now(UTC)
        summary = await self._dashboard_use_case.execute(
            company_id=company_id,
            start=_month_start(now, _HISTORY_MONTHS - 1),
            end=now,
        )
        breakdown = summary.monthly_breakdown
        if len(breakdown) < 3:
            return []
        *previous, last = breakdown
        previous_revenues = [month.revenue_cents for month in previous]
        average = sum(previous_revenues) / len(previous_revenues)
        if average <= 0 or last.revenue_cents >= average * _REVENUE_DROP_RATIO:
            return []
        drop_pct = (1 - last.revenue_cents / average) * 100
        return [
            BusinessSignal(
                kind=SignalKind.REVENUE_DROP,
                severity=SignalSeverity.WARNING,
                title="Queda de receita no mês atual",
                detail=f"A receita de {last.month:02d}/{last.year} está {drop_pct:.0f}% "
                f"abaixo da média dos {len(previous)} meses anteriores. Parte disso "
                "pode ser o mês em andamento — acompanhe de perto.",
            )
        ]

    async def _overdue_signals(self) -> list[BusinessSignal]:
        pending = await self._transaction_repository.list_all(status=TransactionStatus.PENDING)
        now = datetime.now(UTC)
        overdue_count = 0
        overdue_cents = 0
        for transaction in pending:
            if transaction.due_date is None:
                continue
            due = transaction.due_date
            if due.tzinfo is None:
                due = due.replace(tzinfo=UTC)
            if due < now:
                overdue_count += 1
                overdue_cents += abs(transaction.amount_cents)
        if overdue_count == 0:
            return []
        return [
            BusinessSignal(
                kind=SignalKind.OVERDUE_BILLS,
                severity=SignalSeverity.CRITICAL,
                title=f"{overdue_count} lançamento(s) pendente(s) vencido(s)",
                detail=f"Total vencido de {overdue_cents / 100:.2f} na moeda da empresa "
                "— cobre recebimentos e regularize pagamentos para não distorcer o caixa.",
            )
        ]
