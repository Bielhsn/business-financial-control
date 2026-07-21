from pydantic import BaseModel

from app.domain.alerts.entities import AlertSeverity


class AlertResponse(BaseModel):
    code: str
    severity: AlertSeverity
    title: str
    message: str
    action: str | None
