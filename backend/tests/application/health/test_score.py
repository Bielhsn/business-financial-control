from app.application.health.score import compute_health_score
from app.domain.health.entities import HealthRating

_BASE: dict[str, object] = {
    "income_cents": 100000,
    "net_cents": 20000,  # margem 20% → score de margem 100
    "trend_pct": 20.0,  # → score 100
    "total_orders": 100,
    "total_refunds": 0,  # → score 100
    "goals_total": 2,
    "goals_on_track": 2,  # → 100
    "connections_total": 1,
    "connections_error": 0,  # → 100
}


def _score(**overrides: object):
    return compute_health_score(**{**_BASE, **overrides})  # type: ignore[arg-type]


def test_all_healthy_is_excellent() -> None:
    health = _score()
    assert health.score == 100
    assert health.rating == HealthRating.EXCELLENT
    assert {f.key for f in health.factors} == {
        "margin",
        "trend",
        "refunds",
        "goals",
        "integrations",
    }


def test_no_data_returns_neutral_not_critical() -> None:
    health = compute_health_score(
        income_cents=0,
        net_cents=0,
        trend_pct=None,
        total_orders=0,
        total_refunds=0,
        goals_total=0,
        goals_on_track=0,
        connections_total=0,
        connections_error=0,
    )
    assert health.score == 50
    assert health.rating == HealthRating.ATTENTION
    assert health.factors == []


def test_negative_margin_lowers_score() -> None:
    healthy = _score()
    poor = _score(net_cents=-20000)  # margem -20% → score de margem 0
    assert poor.score < healthy.score
    margin = next(f for f in poor.factors if f.key == "margin")
    assert margin.score == 0


def test_refund_factor_skipped_with_few_orders() -> None:
    health = _score(total_orders=3, total_refunds=3)
    assert "refunds" not in {f.key for f in health.factors}


def test_integration_error_reduces_integration_factor() -> None:
    health = _score(connections_total=2, connections_error=1)
    integrations = next(f for f in health.factors if f.key == "integrations")
    assert integrations.score == 50


def test_rating_bands() -> None:
    # Margem 0% (score 50), sem outros fatores → 50 → atenção.
    attention = compute_health_score(
        income_cents=100000,
        net_cents=0,
        trend_pct=None,
        total_orders=0,
        total_refunds=0,
        goals_total=0,
        goals_on_track=0,
        connections_total=0,
        connections_error=0,
    )
    assert attention.rating == HealthRating.ATTENTION
