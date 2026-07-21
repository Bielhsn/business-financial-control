from pydantic import BaseModel, Field

from app.domain.goals.entities import GoalMetric


class SetGoalRequest(BaseModel):
    target_cents: int = Field(gt=0)


class GoalProgressResponse(BaseModel):
    metric: GoalMetric
    target_cents: int
    actual_cents: int
    projected_cents: int
    progress_pct: float
    on_track: bool
