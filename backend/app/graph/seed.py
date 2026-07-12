"""
Load seed_data/incidents.json into Neo4j AuraDB.

Usage (from backend/):
    python -m app.graph.seed
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from app.graph.connection import close_driver, get_driver, is_neo4j_configured, verify_connectivity
from app.graph.writer import UPSERT_SIMILAR, ensure_constraints, write_incident_to_neo4j

SEED_PATH = Path(__file__).resolve().parents[2] / "seed_data" / "incidents.json"
CLEAR_GRAPH = "MATCH (n) DETACH DELETE n"


def load_incidents(path: Path = SEED_PATH) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError("incidents.json must be a JSON array")
    return data


def seed_graph(*, clear: bool = True) -> int:
    """
    Write all seed incidents into Neo4j.
    Returns number of incidents seeded.
    """
    if not is_neo4j_configured():
        raise RuntimeError(
            "Neo4j is not configured. Copy .env.example to .env and set "
            "NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD."
        )

    driver = get_driver()
    if driver is None or not verify_connectivity():
        raise RuntimeError("Could not connect to Neo4j. Check AuraDB credentials.")

    incidents = load_incidents()

    with driver.session() as session:
        ensure_constraints(session)
        if clear:
            session.run(CLEAR_GRAPH)

    for incident in incidents:
        ok = write_incident_to_neo4j(incident)
        if not ok:
            raise RuntimeError(f"Failed to write incident {incident.get('id')}")

    # Re-apply SIMILAR_TO after all nodes exist (writer already does per-incident;
    # second pass is harmless MERGEs for any ordering issues).
    with driver.session() as session:
        for incident in incidents:
            for ref in incident.get("similar_to") or []:
                session.run(
                    UPSERT_SIMILAR,
                    from_id=incident["id"],
                    to_id=ref["incident_id"],
                    score=float(ref.get("score") or 0.0),
                )

    return len(incidents)


def main() -> int:
    try:
        count = seed_graph(clear=True)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        close_driver()

    print(f"Seeded {count} incidents into Neo4j from {SEED_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
