from datetime import datetime

from pydantic import BaseModel, Field

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


class PeriodSummaryResponse(BaseModel):
    summary: str


class AskQuestionRequest(BaseModel):
    start: datetime
    end: datetime
    question: str = Field(min_length=3, max_length=500)


class AskQuestionResponse(BaseModel):
    answer: str
