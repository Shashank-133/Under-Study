"""Write a single incident into Neo4j (used by seed + live ingest)."""

from __future__ import annotations

from typing import Any

from app.graph.connection import get_driver, is_neo4j_configured, verify_connectivity

CONSTRAINTS = [
    "CREATE CONSTRAINT incident_id IF NOT EXISTS FOR (i:Incident) REQUIRE i.id IS UNIQUE",
    "CREATE CONSTRAINT person_email IF NOT EXISTS FOR (p:Person) REQUIRE p.email IS UNIQUE",
    "CREATE CONSTRAINT pr_number IF NOT EXISTS FOR (pr:PR) REQUIRE pr.number IS UNIQUE",
    "CREATE CONSTRAINT file_path IF NOT EXISTS FOR (f:File) REQUIRE f.path IS UNIQUE",
]

UPSERT_INCIDENT = """
MERGE (i:Incident {id: $id})
SET i.title = $title,
    i.description = $description,
    i.created_at = $created_at

MERGE (es:ErrorSignature {id: $es_id})
SET es.message = $es_message,
    es.stack_trace = $es_stack,
    es.error_type = $es_type
MERGE (i)-[:HAS_SIGNATURE]->(es)

MERGE (rc:RootCause {id: $rc_id})
SET rc.category = $rc_category,
    rc.description = $rc_description
MERGE (i)-[:CAUSED_BY]->(rc)

MERGE (fp:FixPattern {id: $fp_id})
SET fp.description = $fp_description,
    fp.code_snippet = $fp_snippet
MERGE (i)-[:HAS_FIX]->(fp)

MERGE (p:Person {email: $person_email})
SET p.name = $person_name
MERGE (i)-[:RESOLVED_BY]->(p)

MERGE (pr:PR {number: $pr_number})
SET pr.url = $pr_url,
    pr.title = $pr_title
MERGE (i)-[:IMPLEMENTED_IN]->(pr)
MERGE (p)-[:AUTHORED_BY]->(pr)
"""

UPSERT_FILE = """
MATCH (i:Incident {id: $incident_id})
MERGE (f:File {path: $path})
SET f.line = $line
MERGE (i)-[:LOCATED_IN]->(f)
"""

UPSERT_SIMILAR = """
MATCH (a:Incident {id: $from_id})
MATCH (b:Incident {id: $to_id})
MERGE (a)-[r:SIMILAR_TO]->(b)
SET r.score = $score
"""


def _write_one(tx, incident: dict[str, Any]) -> None:
    incident_id = incident["id"]
    signature = incident.get("error_signature") or {}
    root_cause = incident.get("root_cause") or {}
    fix = incident.get("fix_pattern") or {}
    person = incident.get("resolved_by") or {}
    pr = incident.get("pr") or {}

    person_name = person.get("name") or "Unknown"
    person_email = person.get("email") or (
        f"{person_name.lower().replace(' ', '.')}@team.dev"
    )
    pr_number = int(pr.get("number") or 0)
    if pr_number <= 0:
        # Neo4j uniqueness on PR.number — derive stable synthetic number from id
        pr_number = abs(hash(incident_id)) % 900000 + 100000

    tx.run(
        UPSERT_INCIDENT,
        id=incident_id,
        title=incident.get("title", ""),
        description=incident.get("description", ""),
        created_at=incident.get("created_at", ""),
        es_id=f"{incident_id}-sig",
        es_message=signature.get("message", ""),
        es_stack=signature.get("stack_trace", ""),
        es_type=signature.get("error_type", ""),
        rc_id=f"{incident_id}-rc",
        rc_category=root_cause.get("category", ""),
        rc_description=root_cause.get("description", ""),
        fp_id=f"{incident_id}-fix",
        fp_description=fix.get("description", ""),
        fp_snippet=fix.get("code_snippet", ""),
        person_email=person_email,
        person_name=person_name,
        pr_number=pr_number,
        pr_url=pr.get("url", ""),
        pr_title=pr.get("title", ""),
    )

    for file_loc in incident.get("files") or []:
        path = (file_loc or {}).get("path") or ""
        if not path:
            continue
        tx.run(
            UPSERT_FILE,
            incident_id=incident_id,
            path=path,
            line=file_loc.get("line"),
        )


def ensure_constraints(session) -> None:
    for cypher in CONSTRAINTS:
        session.run(cypher)


def write_incident_to_neo4j(incident: dict[str, Any]) -> bool:
    """
    Upsert one incident into Neo4j.
    Returns True on success, False if Neo4j is unavailable.
    """
    if not is_neo4j_configured():
        return False

    driver = get_driver()
    if driver is None or not verify_connectivity():
        return False

    with driver.session() as session:
        ensure_constraints(session)
        session.execute_write(_write_one, incident)
        for ref in incident.get("similar_to") or []:
            session.run(
                UPSERT_SIMILAR,
                from_id=incident["id"],
                to_id=ref["incident_id"],
                score=float(ref.get("score") or 0.0),
            )
    return True
