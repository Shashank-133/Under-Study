"""
Cypher helpers + unified similarity search over Neo4j or local seed JSON.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.graph.connection import get_driver, verify_connectivity
from app.graph.runtime_store import merge_with_base, runtime_count
from app.graph.similarity import rank_incidents

SEED_PATH = Path(__file__).resolve().parents[2] / "seed_data" / "incidents.json"

FETCH_ALL_INCIDENTS_CYPHER = """
MATCH (i:Incident)
OPTIONAL MATCH (i)-[:HAS_SIGNATURE]->(es:ErrorSignature)
OPTIONAL MATCH (i)-[:CAUSED_BY]->(rc:RootCause)
OPTIONAL MATCH (i)-[:LOCATED_IN]->(f:File)
OPTIONAL MATCH (i)-[:RESOLVED_BY]->(p:Person)
OPTIONAL MATCH (i)-[:IMPLEMENTED_IN]->(pr:PR)
OPTIONAL MATCH (i)-[:HAS_FIX]->(fp:FixPattern)
WITH i, es, rc, p, pr, fp, collect(DISTINCT {path: f.path, line: f.line}) AS files
RETURN i.id AS id,
       i.title AS title,
       i.description AS description,
       i.created_at AS created_at,
       es.message AS es_message,
       es.stack_trace AS es_stack,
       es.error_type AS es_type,
       rc.category AS rc_category,
       rc.description AS rc_description,
       files,
       fp.description AS fix_description,
       fp.code_snippet AS fix_snippet,
       p.name AS person_name,
       p.email AS person_email,
       pr.number AS pr_number,
       pr.url AS pr_url,
       pr.title AS pr_title
"""


@lru_cache(maxsize=1)
def load_seed_incidents() -> list[dict[str, Any]]:
    with SEED_PATH.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError(f"Expected list in {SEED_PATH}")
    return data


def reload_seed_cache() -> None:
    load_seed_incidents.cache_clear()


def _rows_to_incidents(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    incidents: list[dict[str, Any]] = []
    for row in rows:
        files = [f for f in (row.get("files") or []) if f and f.get("path")]
        incidents.append(
            {
                "id": row.get("id"),
                "title": row.get("title") or "",
                "description": row.get("description") or "",
                "created_at": row.get("created_at") or "",
                "error_signature": {
                    "message": row.get("es_message") or "",
                    "stack_trace": row.get("es_stack") or "",
                    "error_type": row.get("es_type") or "",
                },
                "root_cause": {
                    "category": row.get("rc_category") or "",
                    "description": row.get("rc_description") or "",
                },
                "files": files,
                "fix_pattern": {
                    "description": row.get("fix_description") or "",
                    "code_snippet": row.get("fix_snippet") or "",
                },
                "resolved_by": {
                    "name": row.get("person_name") or "",
                    "email": row.get("person_email") or "",
                },
                "pr": {
                    "number": row.get("pr_number") or 0,
                    "url": row.get("pr_url") or "",
                    "title": row.get("pr_title") or "",
                },
                "similar_to": [],
            }
        )
    return incidents


def fetch_incidents_from_neo4j() -> list[dict[str, Any]] | None:
    """Return incidents from AuraDB, or None if Neo4j is unavailable."""
    driver = get_driver()
    if driver is None or not verify_connectivity():
        return None

    try:
        with driver.session() as session:
            result = session.run(FETCH_ALL_INCIDENTS_CYPHER)
            rows = [dict(record) for record in result]
        if not rows:
            return []
        return _rows_to_incidents(rows)
    except Exception:
        return None


def get_all_incidents() -> tuple[list[dict[str, Any]], str]:
    """
    Prefer Neo4j; fall back to seed JSON so /query always works locally.
    Always merges in-memory runtime incidents from live POST /ingest.
    Returns (incidents, source) where source is 'neo4j', 'seed_json', or mixed.
    """
    neo4j_incidents = fetch_incidents_from_neo4j()
    if neo4j_incidents is not None and len(neo4j_incidents) > 0:
        merged = merge_with_base(neo4j_incidents)
        source = "neo4j+runtime" if runtime_count() else "neo4j"
        return merged, source

    merged = merge_with_base(load_seed_incidents())
    source = "seed_json+runtime" if runtime_count() else "seed_json"
    return merged, source


def search_similar(error: str, *, limit: int = 5) -> list[dict[str, Any]]:
    """
    Given error text, find similar incidents ranked by confidence.

    Each dict matches the API SimilarIncidentResult fields, plus optional
    `_score_breakdown` and `_source` for internal use.
    """
    incidents, source = get_all_incidents()
    ranked = rank_incidents(error, incidents, limit=limit)
    for item in ranked:
        item["_source"] = source
    return ranked


def graph_stats() -> dict[str, Any]:
    incidents, source = get_all_incidents()
    return {
        "source": source,
        "incident_count": len(incidents),
        "runtime_incident_count": runtime_count(),
        "neo4j_connected": source.startswith("neo4j"),
    }
