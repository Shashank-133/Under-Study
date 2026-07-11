from typing import Literal

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    error: str = Field(..., min_length=1, description="Raw error message or stack trace")
    language: Literal["en", "hi", "ta", "te"] = "en"


class SimilarIncidentResult(BaseModel):
    id: str
    title: str
    similarity_score: float = Field(ge=0.0, le=1.0)
    fix_summary: str
    resolved_by: str
    pr_url: str


class QueryResponse(BaseModel):
    answer: str
    confidence: float = Field(ge=0.0, le=1.0)
    similar_incidents: list[SimilarIncidentResult] = []
    ask_person: str | None = None
