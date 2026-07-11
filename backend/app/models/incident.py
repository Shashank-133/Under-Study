from pydantic import BaseModel, Field


class ErrorSignature(BaseModel):
    message: str
    stack_trace: str = ""
    error_type: str = ""


class RootCause(BaseModel):
    category: str
    description: str


class FileLocation(BaseModel):
    path: str
    line: int | None = None


class FixPattern(BaseModel):
    description: str
    code_snippet: str = ""


class Person(BaseModel):
    name: str
    email: str = ""


class PullRequest(BaseModel):
    number: int
    url: str
    title: str = ""


class SimilarIncidentRef(BaseModel):
    incident_id: str
    score: float = Field(ge=0.0, le=1.0)


class Incident(BaseModel):
    id: str
    title: str
    description: str
    created_at: str
    error_signature: ErrorSignature
    root_cause: RootCause
    files: list[FileLocation] = []
    fix_pattern: FixPattern
    resolved_by: Person
    pr: PullRequest
    similar_to: list[SimilarIncidentRef] = []
