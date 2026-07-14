from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: dict[str, object] = Field(default_factory=dict)
