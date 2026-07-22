from app.application.alerts.compute import compute_alerts
from app.domain.alerts.entities import AlertSeverity
from app.domain.goals.entities import GoalMetric

_HEALTHY: dict[str, object] = {
    "connections_with_error": 0,
    "off_track_goals": [],
    "projected_net_cents": 50000,
    "total_orders": 100,
    "total_refunds": 1,
    "members_used": 1,
    "members_limit": 5,
    "integrations_used": 1,
    "integrations_limit": 3,
}


def _alerts(**overrides: object) -> list:
    return compute_alerts(**{**_HEALTHY, **overrides})  # type: ignore[arg-type]


def test_healthy_state_has_no_alerts() -> None:
    assert _alerts() == []


def test_integration_error_is_critical() -> None:
    alerts = _alerts(connections_with_error=2)
    assert alerts[0].code == "integration_error"
    assert alerts[0].severity == AlertSeverity.CRITICAL


def test_negative_forecast_is_critical() -> None:
    alerts = _alerts(projected_net_cents=-1000)
    assert any(
        a.code == "negative_forecast" and a.severity == AlertSeverity.CRITICAL for a in alerts
    )


def test_off_track_goal_generates_warning() -> None:
    alerts = _alerts(off_track_goals=[GoalMetric.MONTHLY_NET])
    goal_alert = next(a for a in alerts if a.code == "goal_off_track_monthly_net")
    assert goal_alert.severity == AlertSeverity.WARNING


def test_high_refund_rate_only_with_enough_orders() -> None:
    # Poucos pedidos: não dispara mesmo com proporção alta.
    assert not any(a.code == "high_refund_rate" for a in _alerts(total_orders=3, total_refunds=3))
    # Volume suficiente e >= 15%: dispara.
    alerts = _alerts(total_orders=17, total_refunds=3)
    assert any(a.code == "high_refund_rate" for a in alerts)


def test_plan_limits_generate_info_alerts() -> None:
    alerts = _alerts(members_used=5, members_limit=5, integrations_used=3, integrations_limit=3)
    codes = {a.code for a in alerts}
    assert "members_limit_reached" in codes
    assert "integrations_limit_reached" in codes


def test_unlimited_plan_never_hits_limit_alert() -> None:
    alerts = _alerts(
        members_used=999, members_limit=-1, integrations_used=999, integrations_limit=-1
    )
    codes = {a.code for a in alerts}
    assert "members_limit_reached" not in codes
    assert "integrations_limit_reached" not in codes


def test_alerts_sorted_by_severity() -> None:
    alerts = _alerts(
        connections_with_error=1,  # critical
        off_track_goals=[GoalMetric.MONTHLY_INCOME],  # warning
        members_used=5,
        members_limit=5,  # info
    )
    severities = [a.severity for a in alerts]
    assert severities == sorted(
        severities, key=lambda s: {"critical": 0, "warning": 1, "info": 2}[s]
    )


def test_overdue_bills_generate_critical_alert() -> None:
    alerts = _alerts(overdue_payable_count=3, overdue_payable_cents=250000)
    overdue = next(a for a in alerts if a.code == "bills_overdue")
    assert overdue.severity == AlertSeverity.CRITICAL
    assert "3 conta" in overdue.message
    assert "R$ 2.500,00" in overdue.message


def test_due_soon_bills_generate_warning_alert() -> None:
    alerts = _alerts(due_soon_payable_count=2, due_soon_payable_cents=15000)
    due_soon = next(a for a in alerts if a.code == "bills_due_soon")
    assert due_soon.severity == AlertSeverity.WARNING
    assert "R$ 150,00" in due_soon.message


def test_no_due_alerts_when_zero() -> None:
    codes = {a.code for a in _alerts()}
    assert "bills_overdue" not in codes
    assert "bills_due_soon" not in codes
