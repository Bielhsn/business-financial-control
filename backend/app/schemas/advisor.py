from pydantic import BaseModel

from app.domain.advisor.entities import SignalKind, SignalSeverity


class BusinessSignalResponse(BaseModel):
    kind: SignalKind
    severity: SignalSeverity
    title: str
    detail: str


class SignalsResponse(BaseModel):
    signals: list[BusinessSignalResponse]


class RecommendationsResponse(BaseModel):
    signals: list[BusinessSignalResponse]
    recommendations: str
