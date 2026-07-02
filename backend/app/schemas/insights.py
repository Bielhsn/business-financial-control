from datetime import datetime

from pydantic import BaseModel

from app.domain.insights.entities import InsightKind


class GenerateInsightsRequest(BaseModel):
    start: datetime
    end: datetime


class InsightResponse(BaseModel):
    kind: InsightKind
    title: str
    message: str


class InsightsResponse(BaseModel):
    start: datetime
    end: datetime
    insights: list[InsightResponse]
