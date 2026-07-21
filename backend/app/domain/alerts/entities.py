from dataclasses import dataclass
from enum import StrEnum


class AlertSeverity(StrEnum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class Alert:
    """Recomendação acionável derivada do estado atual da empresa. Determinística
    — as mesmas condições geram sempre os mesmos alertas."""

    code: str
    severity: AlertSeverity
    title: str
    message: str
    action: str | None = None  # rota relativa sugerida (ex.: "integrations")
