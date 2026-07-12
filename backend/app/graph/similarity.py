"""
Confidence / similarity scoring for matching a pasted error to past incidents.

Weights (explainable):
  - 0.55 stack / message token similarity
  - 0.25 file-path overlap (paths extracted from the error text)
  - 0.20 root-cause / error-type category match
"""

from __future__ import annotations

import re
from typing import Any

# Optional Person 3 embeddings — never required for backend to boot.
try:
    import sys
    from pathlib import Path

    _ai_root = Path(__file__).resolve().parents[3] / "ai"
    if _ai_root.is_dir() and str(_ai_root) not in sys.path:
        sys.path.insert(0, str(_ai_root))
    from embeddings import compute_similarity as _embedding_similarity  # type: ignore
except Exception:  # pragma: no cover - ai may be absent or broken
    _embedding_similarity = None


_TOKEN_RE = re.compile(r"[A-Za-z0-9_./\\-]+")
_PATH_RE = re.compile(
    r"(?:[A-Za-z]:)?(?:/|\\)?(?:[\w.-]+(?:/|\\))+[\w.-]+\.\w+(?::\d+)?"
)


def tokenize(text: str) -> set[str]:
    if not text:
        return set()
    return {t.lower() for t in _TOKEN_RE.findall(text) if len(t) > 1}


def token_overlap_similarity(a: str, b: str) -> float:
    tokens_a = tokenize(a)
    tokens_b = tokenize(b)
    if not tokens_a or not tokens_b:
        return 0.0
    union = tokens_a | tokens_b
    return len(tokens_a & tokens_b) / len(union)


def stack_similarity(error_text: str, signature: dict[str, Any]) -> float:
    """Compare pasted error to stored message + stack_trace (+ optional embeddings)."""
    stored = " ".join(
        filter(
            None,
            [
                signature.get("message", ""),
                signature.get("stack_trace", ""),
                signature.get("error_type", ""),
            ],
        )
    )
    overlap = token_overlap_similarity(error_text, stored)

    if _embedding_similarity is None:
        return overlap

    try:
        emb = float(_embedding_similarity(error_text, stored))
        # Blend: embeddings help when available, overlap remains primary signal.
        return round(0.45 * overlap + 0.55 * emb, 4)
    except Exception:
        return overlap


def extract_paths(text: str) -> set[str]:
    paths: set[str] = set()
    for match in _PATH_RE.findall(text or ""):
        cleaned = match.split(":")[0].replace("\\", "/").lower()
        paths.add(cleaned)
        # Also keep basename for softer matches
        paths.add(cleaned.rsplit("/", 1)[-1])
    # Common "at File.ext:line" frames
    for m in re.finditer(r"at\s+([\w./\\-]+\.\w+):\d+", text or "", flags=re.I):
        p = m.group(1).replace("\\", "/").lower()
        paths.add(p)
        paths.add(p.rsplit("/", 1)[-1])
    return paths


def file_path_overlap(error_text: str, files: list[dict[str, Any]]) -> float:
    incident_paths: set[str] = set()
    for f in files or []:
        path = (f.get("path") or "").replace("\\", "/").lower()
        if not path:
            continue
        incident_paths.add(path)
        incident_paths.add(path.rsplit("/", 1)[-1])

    if not incident_paths:
        return 0.0

    error_paths = extract_paths(error_text)
    if not error_paths:
        # Soft signal: token overlap against joined paths
        return token_overlap_similarity(error_text, " ".join(incident_paths))

    return len(error_paths & incident_paths) / len(error_paths | incident_paths)


def category_match(error_text: str, root_cause: dict[str, Any], error_type: str) -> float:
    text = (error_text or "").lower()
    score = 0.0

    category = (root_cause.get("category") or "").lower()
    if category:
        # Direct token presence or hyphen/underscore variants
        variants = {category, category.replace("_", " "), category.replace("_", "-")}
        if any(v and v in text for v in variants):
            score += 0.6
        # Heuristic keyword map for common categories
        keywords = {
            "null_reference": ["undefined", "null", "cannot read", "map of", "length"],
            "cors_misconfiguration": ["cors", "access-control", "blocked by cors"],
            "async_error_handling": ["unhandled promise", "await", "async"],
            "configuration": ["env", ".env", "configuration", "missing"],
            "auth_token": ["jwt", "401", "token", "csrf", "unauthorized"],
            "race_condition": ["duplicate", "idempotency", "race"],
            "resource_leak": ["memory", "leak", "session"],
            "timezone": ["timezone", "utc", "ist", "overdue"],
            "react_hooks": ["useeffect", "maximum update depth", "stale"],
            "injection": ["sql injection", "or 1=1"],
            "networking": ["websocket", "reconnect", "econnrefused"],
            "dependency_upgrade": ["pydantic", "field default", "openapi"],
            "performance": ["timeout", "n+1", "slow"],
        }
        for kw in keywords.get(category, []):
            if kw in text:
                score += 0.25
                break

    et = (error_type or "").lower()
    if et and et.lower() in text:
        score += 0.4

    return min(1.0, score)


def score_incident(error_text: str, incident: dict[str, Any]) -> dict[str, float]:
    """
    Return component scores and weighted confidence for one incident.
    """
    signature = incident.get("error_signature") or {}
    root_cause = incident.get("root_cause") or {}
    files = incident.get("files") or []

    stack = stack_similarity(error_text, signature)
    files_score = file_path_overlap(error_text, files)
    category = category_match(error_text, root_cause, signature.get("error_type", ""))

    confidence = round(0.55 * stack + 0.25 * files_score + 0.20 * category, 4)
    confidence = max(0.0, min(1.0, confidence))

    return {
        "stack": round(stack, 4),
        "files": round(files_score, 4),
        "category": round(category, 4),
        "confidence": confidence,
    }


def rank_incidents(
    error_text: str,
    incidents: list[dict[str, Any]],
    *,
    limit: int = 5,
    min_score: float = 0.12,
) -> list[dict[str, Any]]:
    """
    Score and rank incidents. Each result includes similarity_score plus
    `_score_breakdown` for debugging / explainability.
    """
    ranked: list[dict[str, Any]] = []
    for incident in incidents:
        breakdown = score_incident(error_text, incident)
        if breakdown["confidence"] < min_score:
            continue
        ranked.append(
            {
                "id": incident.get("id", ""),
                "title": incident.get("title", ""),
                "similarity_score": breakdown["confidence"],
                "fix_summary": (incident.get("fix_pattern") or {}).get("description", ""),
                "resolved_by": (incident.get("resolved_by") or {}).get("name", ""),
                "pr_url": (incident.get("pr") or {}).get("url", ""),
                "_score_breakdown": breakdown,
                "_incident": incident,
            }
        )

    ranked.sort(key=lambda r: r["similarity_score"], reverse=True)
    return ranked[:limit]
