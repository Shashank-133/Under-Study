from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.query import QueryRequest, QueryResponse, SimilarIncidentResult

app = FastAPI(
    title="Understudy API",
    description="AI pair-debugger with institutional memory",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Placeholder endpoint — Person 2 replaces logic with real graph traversal.
    Request/response shape is frozen; do not change without team sync.
    """
    return QueryResponse(
        answer=(
            "[Stub] Your team may have seen something like this before. "
            f"Received error ({len(request.error)} chars) with language={request.language}. "
            "Real similarity search and answers will appear once the backend pipeline is wired."
        ),
        confidence=0.0,
        similar_incidents=[
            SimilarIncidentResult(
                id="inc-001",
                title="Null user list crashes dashboard",
                similarity_score=0.85,
                fix_summary="Guard with optional chaining: const users = data?.users ?? [];",
                resolved_by="Alice Kumar",
                pr_url="https://github.com/team/understudy/pull/142",
            )
        ],
        ask_person="Alice Kumar",
    )
