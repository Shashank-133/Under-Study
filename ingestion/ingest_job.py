"""
Render Workflow ingestion job — shared folder, sync with team before editing.

Pipeline (to be wired):
  1. Read raw incident text or seed file
  2. Call ai.extraction.extract_incident()
  3. Write nodes/relationships to Neo4j via backend graph layer

Person 2 + Person 3 + team: implement after core modules are ready.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = REPO_ROOT / "backend" / "seed_data" / "incidents.json"
AI_PATH = REPO_ROOT / "ai"


def load_seed_incidents() -> list[dict]:
    with open(SEED_PATH, encoding="utf-8") as f:
        return json.load(f)


def run_ingest_job(source: str = "seed") -> dict:
    """
    Entry point for Render Workflow cron / manual trigger.

    Returns summary dict for logging.
    """
    if source == "seed":
        incidents = load_seed_incidents()
    else:
        incidents = []

    # TODO: sys.path insert or package layout for cross-folder imports
    # from extraction import extract_incident
    # from backend.app.graph.connection import get_driver

    processed = len(incidents)
    print(f"[ingest_job] Loaded {processed} incidents from {source} (stub — not written to Neo4j)")

    return {
        "status": "stub",
        "source": source,
        "processed": processed,
        "written": 0,
    }


if __name__ == "__main__":
    source_arg = sys.argv[1] if len(sys.argv) > 1 else "seed"
    result = run_ingest_job(source_arg)
    print(json.dumps(result, indent=2))
