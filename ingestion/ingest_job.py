"""
Render Workflow ingestion job — shared folder.

Pipeline:
  1. Read raw incident text OR seed file
  2. Call ai.extraction.extract_incident() (via backend ai_bridge when available)
  3. Write nodes/relationships to Neo4j + runtime store via backend ingest service

Usage:
  python ingest_job.py seed
  python ingest_job.py raw "TypeError: Cannot read property 'map' of undefined"
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = REPO_ROOT / "backend"
SEED_PATH = BACKEND_PATH / "seed_data" / "incidents.json"
AI_PATH = REPO_ROOT / "ai"


def _bootstrap_paths() -> None:
    for path in (str(BACKEND_PATH), str(AI_PATH), str(REPO_ROOT)):
        if path not in sys.path:
            sys.path.insert(0, path)


def load_seed_incidents() -> list[dict]:
    with open(SEED_PATH, encoding="utf-8") as f:
        return json.load(f)


def run_ingest_job(source: str = "seed", raw_text: str | None = None) -> dict:
    """
    Entry point for Render Workflow cron / manual trigger.
    """
    _bootstrap_paths()

    from dotenv import load_dotenv

    load_dotenv(REPO_ROOT / ".env")

    from app.services.ingest import ingest_raw_error

    written = 0
    processed = 0
    results: list[dict] = []

    if source == "raw":
        text = raw_text or ""
        if not text.strip():
            return {"status": "error", "error": "raw text required", "processed": 0, "written": 0}
        result = ingest_raw_error(text)
        processed = 1
        written = 1 if result.get("neo4j_written") else 0
        results.append({"id": result.get("id"), "storage": result.get("storage")})
    else:
        # Re-seed path: write each seed incident through the same writer
        from app.graph.writer import write_incident_to_neo4j
        from app.graph.runtime_store import upsert_runtime_incident

        incidents = load_seed_incidents()
        processed = len(incidents)
        for incident in incidents:
            upsert_runtime_incident(incident)
            if write_incident_to_neo4j(incident):
                written += 1
            results.append({"id": incident.get("id"), "storage": "seed"})

    status = "ok" if processed else "empty"
    print(
        f"[ingest_job] source={source} processed={processed} "
        f"neo4j_writes={written} results={len(results)}"
    )
    return {
        "status": status,
        "source": source,
        "processed": processed,
        "written": written,
        "results": results[:10],
    }


if __name__ == "__main__":
    source_arg = sys.argv[1] if len(sys.argv) > 1 else "seed"
    raw_arg = None
    if source_arg == "raw":
        raw_arg = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else sys.stdin.read()
    result = run_ingest_job(source_arg, raw_text=raw_arg)
    print(json.dumps(result, indent=2))
