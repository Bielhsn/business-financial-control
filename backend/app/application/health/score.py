"""Índice de saúde do negócio (0..100) — média ponderada de fatores explicáveis.

Determinístico e transparente: cada fator vira um score 0..100 com um `detail`
que explica o número. Fatores sem dados suficientes são ignorados (não penalizam),
então uma empresa nova não recebe uma nota artificialmente baixa.
"""

from app.domain.health.entities import HealthFactor, HealthRating, HealthScore

_MIN_ORDERS_FOR_REFUND_FACTOR = 10


def _clamp(value: float) -> int:
    return max(0, min(100, round(value)))


def _rating(score: int) -> HealthRating:
    if score >= 80:
        return HealthRating.EXCELLENT
    if score >= 60:
        return HealthRating.GOOD
    if score >= 40:
        return HealthRating.ATTENTION
    return HealthRating.CRITICAL


def compute_health_score(
    *,
    income_cents: int,
    net_cents: int,
    trend_pct: float | None,
    total_orders: int,
    total_refunds: int,
    goals_total: int,
    goals_on_track: int,
    connections_total: int,
    connections_error: int,
) -> HealthScore:
    factors: list[HealthFactor] = []

    # Margem líquida do mês: -20% → 0, 0% → 50, +20% → 100.
    if income_cents > 0:
        margin_pct = net_cents / income_cents * 100
        factors.append(
            HealthFactor(
                key="margin",
                label="Margem do mês",
                score=_clamp(50 + margin_pct * 2.5),
                weight=3,
                detail=f"Margem líquida de {margin_pct:.0f}% sobre a receita do mês.",
            )
        )

    # Tendência de caixa (do forecast): -20% → 0, 0% → 50, +20% → 100.
    if trend_pct is not None:
        factors.append(
            HealthFactor(
                key="trend",
                label="Tendência de caixa",
                score=_clamp(50 + trend_pct * 2.5),
                weight=2,
                detail=f"Resultado {'subindo' if trend_pct >= 0 else 'caindo'} "
                f"{abs(trend_pct):.0f}% frente aos meses anteriores.",
            )
        )

    # Reembolsos: 0% → 100, 15% → 50, 30%+ → 0.
    total = total_orders + total_refunds
    if total_orders >= _MIN_ORDERS_FOR_REFUND_FACTOR and total > 0:
        refund_rate = total_refunds / total * 100
        factors.append(
            HealthFactor(
                key="refunds",
                label="Reembolsos",
                score=_clamp(100 - refund_rate * (100 / 30)),
                weight=2,
                detail=f"{refund_rate:.0f}% das vendas viraram reembolso no período.",
            )
        )

    # Metas: proporção de metas no caminho.
    if goals_total > 0:
        factors.append(
            HealthFactor(
                key="goals",
                label="Metas",
                score=_clamp(goals_on_track / goals_total * 100),
                weight=2,
                detail=f"{goals_on_track} de {goals_total} meta(s) no caminho.",
            )
        )

    # Integrações saudáveis.
    if connections_total > 0:
        healthy = connections_total - connections_error
        factors.append(
            HealthFactor(
                key="integrations",
                label="Integrações",
                score=_clamp(healthy / connections_total * 100),
                weight=1,
                detail=f"{healthy} de {connections_total} integração(ões) sincronizando.",
            )
        )

    if not factors:
        # Sem dados: neutro (50), não crítico — evita punir empresa recém-criada.
        return HealthScore(score=50, rating=_rating(50), factors=[])

    weighted = sum(factor.score * factor.weight for factor in factors)
    total_weight = sum(factor.weight for factor in factors)
    score = round(weighted / total_weight)
    return HealthScore(score=score, rating=_rating(score), factors=factors)
