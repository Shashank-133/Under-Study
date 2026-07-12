"""In-memory incident store for live ingest when Neo4j is offline."""

from __future__ import annotations

from typing import Any

_runtime_incidents: list[dict[str, Any]] = []


def list_runtime_incidents() -> list[dict[str, Any]]:
    return list(_runtime_incidents)


def upsert_runtime_incident(incident: dict[str, Any]) -> dict[str, Any]:
    incident_id = incident.get("id")
    if not incident_id:
        raise ValueError("incident must include id")

    for idx, existing in enumerate(_runtime_incidents):
        if existing.get("id") == incident_id:
            _runtime_incidents[idx] = incident
            return incident

    _runtime_incidents.insert(0, incident)
    return incident


def merge_with_base(base: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Runtime incidents override base incidents with the same id."""
    by_id = {item.get("id"): item for item in base if item.get("id")}
    for item in _runtime_incidents:
        iid = item.get("id")
        if iid:
            by_id[iid] = item
    # Preserve base order, then append purely new runtime ids at front
    base_ids = [item.get("id") for item in base]
    merged = []
    seen = set()
    for item in _runtime_incidents:
        iid = item.get("id")
        if iid and iid not in base_ids and iid not in seen:
            merged.append(item)
            seen.add(iid)
    for item in base:
        iid = item.get("id")
        if iid in by_id and iid not in seen:
            merged.append(by_id[iid])
            seen.add(iid)
    return merged


def runtime_count() -> int:
    return len(_runtime_incidents)
