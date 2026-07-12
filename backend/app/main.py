"""Understudy FastAPI app — graph-backed /query + /ingest pipeline."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.ai_bridge import generate_answer
from app.api.ingest import IngestRequest, IngestResponse
from app.api.query import QueryRequest, QueryResponse, SimilarIncidentResult
from app.graph.connection import close_driver, is_neo4j_configured, verify_connectivity
from app.graph.queries import graph_stats, search_similar
from app.services.ingest import ingest_raw_error


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    close_driver()


app = FastAPI(
    title="Understudy API",
    description="AI pair-debugger with institutional memory",
    version="0.3.0",
    lifespan=lifespan,
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
    stats = graph_stats()
    neo4j_ok = is_neo4j_configured() and verify_connectivity()
    return {
        "status": "ok",
        "neo4j_configured": is_neo4j_configured(),
        "neo4j_connected": neo4j_ok,
        "incident_source": stats["source"],
        "incident_count": stats["incident_count"],
        "runtime_incident_count": stats["runtime_incident_count"],
    }


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Real pipeline:
      1. Accept QueryRequest
      2. Similarity search + graph traversal (Neo4j / seed + runtime ingest)
      3. Build conversational answer (Person 3 generate_answer when available)
      4. Return frozen QueryResponse shape
    """
    matches = search_similar(request.error, limit=5)

    similar = [
        SimilarIncidentResult(
            id=m["id"],
            title=m["title"],
            similarity_score=round(float(m["similarity_score"]), 4),
            fix_summary=m.get("fix_summary") or "",
            resolved_by=m.get("resolved_by") or "",
            pr_url=m.get("pr_url") or "",
        )
        for m in matches
    ]

    confidence = similar[0].similarity_score if similar else 0.0
    ask_person = similar[0].resolved_by if similar else None

    graph_results = {
        "similar_incidents": [s.model_dump() for s in similar],
        "confidence": confidence,
        "ask_person": ask_person,
    }
    answer = generate_answer(graph_results, request.language)

    return QueryResponse(
        answer=answer,
        confidence=confidence,
        similar_incidents=similar,
        ask_person=ask_person,
    )


@app.post("/ingest", response_model=IngestResponse)
async def ingest(request: IngestRequest):
    """
    Live ingestion demo endpoint:
      raw error → ai.extract_incident → Neo4j (if configured) + runtime store
    """
    raw = request.raw_text()
    if not raw:
        raise HTTPException(status_code=422, detail="raw text is required")

    try:
        result = ingest_raw_error(raw)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ingest failed: {exc}") from exc

    storage = result["storage"]
    message = (
        f"Incident '{result['title']}' saved to team memory ({storage}). "
        "Query the same error on Chat to see it surface."
    )
    return IngestResponse(
        status=result["status"],
        id=result["id"],
        title=result["title"],
        neo4j_written=result["neo4j_written"],
        storage=storage,
        message=message,
    )
