from pydantic import BaseModel, model_validator


class IngestRequest(BaseModel):
    raw: str | None = None
    error: str | None = None

    @model_validator(mode="after")
    def require_text(self):
        if not self.raw_text():
            raise ValueError("Provide 'raw' or 'error' with non-empty text")
        return self

    def raw_text(self) -> str:
        return (self.raw or self.error or "").strip()


class IngestResponse(BaseModel):
    status: str
    id: str
    title: str
    neo4j_written: bool
    storage: str
    message: str
