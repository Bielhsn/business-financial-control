from pydantic import BaseModel

from app.domain.health.entities import HealthRating


class HealthFactorResponse(BaseModel):
    key: str
    label: str
    score: int
    weight: int
    detail: str


class HealthScoreResponse(BaseModel):
    score: int
    rating: HealthRating
    factors: list[HealthFactorResponse]
