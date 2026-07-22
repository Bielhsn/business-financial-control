"""Deriva alertas/recomendações acionáveis do estado atual da empresa.

Composição determinística de sinais que já existem (integrações, metas, previsão,
reembolsos, limites de plano). A lógica de decisão é pura; um orquestrador
(GetAlertsUseCase) reúne os números das outras camadas.
"""

from app.domain.alerts.entities import Alert, AlertSeverity
from app.domain.goals.entities import GoalMetric

_REFUND_RATE_ALERT_PCT = 15.0
_MIN_ORDERS_FOR_REFUND_ALERT = 10

_GOAL_LABEL = {
    GoalMetric.MONTHLY_INCOME: "faturamento",
    GoalMetric.MONTHLY_NET: "resultado",
}

# Ordem de severidade para ordenar os alertas (mais grave primeiro).
_SEVERITY_ORDER = {AlertSeverity.CRITICAL: 0, AlertSeverity.WARNING: 1, AlertSeverity.INFO: 2}


def _unlimited(limit: int) -> bool:
    return limit < 0


def _reais(cents: int) -> str:
    # 123456 -> "R$ 1.234,56" (separadores pt-BR).
    formatted = f"{cents / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def compute_alerts(
    *,
    connections_with_error: int,
    off_track_goals: list[GoalMetric],
    projected_net_cents: int,
    total_orders: int,
    total_refunds: int,
    members_used: int,
    members_limit: int,
    integrations_used: int,
    integrations_limit: int,
    overdue_payable_count: int = 0,
    overdue_payable_cents: int = 0,
    due_soon_payable_count: int = 0,
    due_soon_payable_cents: int = 0,
) -> list[Alert]:
    alerts: list[Alert] = []

    if overdue_payable_count > 0:
        alerts.append(
            Alert(
                code="bills_overdue",
                severity=AlertSeverity.CRITICAL,
                title="Contas vencidas",
                message=(
                    f"Você tem {overdue_payable_count} conta(s) a pagar vencida(s), somando "
                    f"{_reais(overdue_payable_cents)}. Quite para evitar juros e multa."
                ),
                action="transactions",
            )
        )

    if due_soon_payable_count > 0:
        alerts.append(
            Alert(
                code="bills_due_soon",
                severity=AlertSeverity.WARNING,
                title="Contas a vencer",
                message=(
                    f"{due_soon_payable_count} conta(s) a pagar vencem nos próximos 7 dias, "
                    f"somando {_reais(due_soon_payable_cents)}. Programe o pagamento."
                ),
                action="transactions",
            )
        )

    if connections_with_error > 0:
        alerts.append(
            Alert(
                code="integration_error",
                severity=AlertSeverity.CRITICAL,
                title="Integração com erro",
                message=(
                    f"{connections_with_error} integração(ões) estão com erro e não estão "
                    "sincronizando. Revise as credenciais para não perder vendas."
                ),
                action="integrations",
            )
        )

    if projected_net_cents < 0:
        alerts.append(
            Alert(
                code="negative_forecast",
                severity=AlertSeverity.CRITICAL,
                title="Projeção de caixa negativa",
                message=(
                    "No ritmo atual, o resultado do mês deve fechar negativo. "
                    "Reveja despesas e acelere recebimentos."
                ),
                action="transactions",
            )
        )

    for metric in off_track_goals:
        label = _GOAL_LABEL.get(metric, metric.value)
        alerts.append(
            Alert(
                code=f"goal_off_track_{metric.value}",
                severity=AlertSeverity.WARNING,
                title=f"Meta de {label} abaixo do ritmo",
                message=(
                    f"A projeção de {label} do mês não deve alcançar a meta definida. "
                    "Ajuste as ações ou revise a meta."
                ),
                action="",
            )
        )

    total = total_orders + total_refunds
    if total_orders >= _MIN_ORDERS_FOR_REFUND_ALERT and total > 0:
        refund_rate = (total_refunds / total) * 100
        if refund_rate >= _REFUND_RATE_ALERT_PCT:
            alerts.append(
                Alert(
                    code="high_refund_rate",
                    severity=AlertSeverity.WARNING,
                    title="Taxa de reembolso alta",
                    message=(
                        f"{refund_rate:.0f}% das vendas do período viraram reembolso. "
                        "Vale investigar produtos ou expectativas de compra."
                    ),
                    action="integrations",
                )
            )

    if not _unlimited(members_limit) and members_used >= members_limit:
        alerts.append(
            Alert(
                code="members_limit_reached",
                severity=AlertSeverity.INFO,
                title="Limite de usuários atingido",
                message=(
                    "Você atingiu o limite de usuários do seu plano. "
                    "Faça upgrade para adicionar mais pessoas à equipe."
                ),
                action="plans",
            )
        )

    if not _unlimited(integrations_limit) and integrations_used >= integrations_limit:
        alerts.append(
            Alert(
                code="integrations_limit_reached",
                severity=AlertSeverity.INFO,
                title="Limite de integrações atingido",
                message=(
                    "Você atingiu o limite de integrações do seu plano. "
                    "Faça upgrade para conectar mais plataformas."
                ),
                action="plans",
            )
        )

    alerts.sort(key=lambda alert: _SEVERITY_ORDER[alert.severity])
    return alerts
