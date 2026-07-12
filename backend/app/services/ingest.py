"""
Service: extract → persist (Neo4j and/or runtime store) for live ingest.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.ai_bridge import extract_incident
from app.graph.runtime_store import upsert_runtime_incident
from app.graph.writer import write_incident_to_neo4j


def _normalize_incident(extracted: dict[str, Any], raw_text: str) -> dict[str, Any]:
    incident_id = extracted.get("id") or f"inc-live-{uuid4().hex[:8]}"
    created_at = extracted.get("created_at") or datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    signature = extracted.get("error_signature") or {}
    if not signature.get("stack_trace"):
        signature["stack_trace"] = raw_text
    if not signature.get("message"):
        signature["message"] = (raw_text or "").split("\n")[0][:200]

    return {
        "id": incident_id,
        "title": extracted.get("title") or "Ingested incident",
        "description": extracted.get("description") or "",
        "created_at": created_at,
        "error_signature": {
            "message": signature.get("message", ""),
            "stack_trace": signature.get("stack_trace", ""),
            "error_type": signature.get("error_type", "Unknown"),
        },
        "root_cause": extracted.get("root_cause")
        or {"category": "unclassified", "description": ""},
        "files": extracted.get("files") or [],
        "fix_pattern": extracted.get("fix_pattern")
        or {"description": "", "code_snippet": ""},
        "resolved_by": extracted.get("resolved_by") or {"name": "Unknown", "email": ""},
        "pr": extracted.get("pr") or {"number": 0, "url": "", "title": ""},
        "similar_to": extracted.get("similar_to") or [],
    }


def ingest_raw_error(raw_text: str) -> dict[str, Any]:
    """
    Full ingest pipeline used by POST /ingest and ingestion/ingest_job.py.
    Always updates the in-process runtime store so /query can find it immediately.
    Also writes to Neo4j when configured.
    """
    if not (raw_text or "").strip():
        raise ValueError("raw text is required")

    extracted = extract_incident(raw_text.strip())
    incident = _normalize_incident(extracted, raw_text.strip())

    upsert_runtime_incident(incident)
    neo4j_written = write_incident_to_neo4j(incident)

    return {
        "status": "ok",
        "id": incident["id"],
        "title": incident["title"],
        "neo4j_written": neo4j_written,
        "storage": "neo4j+runtime" if neo4j_written else "runtime",
        "incident": incident,
    }
